#!/usr/bin/env python3
import argparse
from datetime import datetime
import math
import os
import pprint
import sys
from typing import List
import traceback
from urllib.parse import urlparse

import boto3
import exifread
from stac_pydantic.collection import Collection, Extent, SpatialExtent, TimeInterval
from stac_pydantic.item import Item
from stac_pydantic.shared import Asset, Provider, ProviderRoles

# Initialize a session with your AWS credentials
session = boto3.Session()

# Create an S3 client
s3 = session.client('s3')
paginator = s3.get_paginator('list_objects_v2')


def serialize_dt_rfc3339(dt) -> str:
    """Convert a datetime object to an RFC 3339-compliant string."""
    rfc3339_string = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return rfc3339_string


def dms_to_decimal(dms_list, direction):
    """Convert a string of degrees, minutes, seconds to decimal degrees."""
    d, m, s = dms_list
    decimal_degrees = d + m / 60 + s / 3600

    if direction in ('W', 'S'):
        decimal_degrees = -decimal_degrees

    return decimal_degrees


def create_geojson_point(lat, lon):
    """Create a GeoJSON Point object from a latitude and longitude."""
    return {
        "type": "Point",
        "coordinates": [lon, lat]
    }


def parse_s3uri(s3uri: str):
    """Parse an S3 URI into a bucket name and prefix."""
    parsed = urlparse(s3uri)

    bucket_name = parsed.netloc
    prefix = parsed.path.lstrip('/')

    return (bucket_name, prefix)


def get_metadata(s3uri: str):
    """Get the metadata from a jpg image stored in S3."""
    file_path = s3uri.replace("s3://place-data", "/home/storage/imagery")
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f)
        return tags
    except Exception:
        print(f"Error encountered while retrieving metadata for {s3uri}")
        print(traceback.format_exc())


def get_bounding_box(lat, lon):
    """Get a bounding box around a latitude and longitude."""
    # Radius of the Earth in meters
    R = 6378137

    # Approximate length of 1 degree of latitude and longitude in meters
    lat_length = math.pi * R / 180
    lon_length = math.pi * R * math.cos(math.radians(lat)) / 180

    # Calculate the latitude/longitude coordinates of the corners of the bounding box
    lat_diff = 100 / lat_length
    lon_diff = 100 / lon_length

    min_lat = lat - (lat_diff / 2)
    max_lat = lat + (lat_diff / 2)
    min_lon = lon - (lon_diff / 2)
    max_lon = lon + (lon_diff / 2)

    return [min_lat, min_lon, max_lat, max_lon]


def list_s3_objects(s3uri: str):
    """List all objects in an S3 bucket with a given prefix."""
    bucket_name, prefix = parse_s3uri(s3uri)

    keys = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        keys = keys + [obj['Key'] for obj in page.get('Contents', [])]
    return keys


def s3uri_to_id(key: str):
    """Convert an S3 URI to a STAC Item ID."""
    split = key.split("/")
    location = split[-3]
    filename = split[-1].split('.')[0]
    if location == "grandturk":
        return filename
    else:
        return f"{location}_{filename}"


def read_all_metadata(s3uri: str):
    """Read all metadata from jpg images in an S3 bucket."""
    bucket_name, prefix = parse_s3uri(s3uri)
    obj_keys = [key for key in list_s3_objects(s3uri) if key.lower().endswith(".jpg") or key.lower().endswith(".jpeg")]
    obj_paths = [f"s3://{bucket_name}/{key}" for key in obj_keys]
    all_metadata = [get_metadata(obj_path) for obj_path in obj_paths]
    processed = []
    for idx, md in enumerate(all_metadata):
        try:
            img_lat = dms_to_decimal([ratio.decimal() for ratio in md['GPS GPSLatitude'].values], md['GPS GPSLatitudeRef'].values)
            img_lng =  dms_to_decimal([ratio.decimal() for ratio in md['GPS GPSLongitude'].values], md['GPS GPSLongitudeRef'].values)
            img_datetime = datetime.strptime(md['EXIF DateTimeOriginal'].values, '%Y:%m:%d %H:%M:%S')
        except KeyError:
            print(f"Key Error while reading metadata for {obj_paths[idx]}. Continuing...")
            print(traceback.format_exc())

        try:
            processed_metadata = {
                "path": obj_paths[idx],
                "lat": img_lat,
                "lng": img_lng,
                "datetime": img_datetime,
                "make": md['Image Make'].values,
                "model": md['Image Model'].values,
                "focal_length": md['EXIF FocalLengthIn35mmFilm'].values[0],
                "exposure_time": md['EXIF ExposureTime'].values[0].decimal()
            }
            if "GPS GPSAltitude" in md:
                altitude = md['GPS GPSAltitude'].values[0].decimal()
                processed_metadata["altitude"] = altitude
            processed.append(processed_metadata)
        except TypeError:
            print(f"Error processing metadata for {obj_paths[idx]}. Continuing...")
            print(traceback.format_exc())
        except KeyError:
            print(f"Error processing metadata for {obj_paths[idx]}. Continuing...")
            pprint.pprint(md)
            print(traceback.format_exc())
    return processed


def merge_bboxes(bboxes):
    min_longitude = min(box[0] for box in bboxes)
    min_latitude = min(box[1] for box in bboxes)
    max_longitude = max(box[2] for box in bboxes)
    max_latitude = max(box[3] for box in bboxes)

    return [min_longitude, min_latitude, max_longitude, max_latitude]


def build_stac_item(md, collection_id: str) -> Item:
    """Build a STAC Item from a metadata dictionary."""
    id = s3uri_to_id(md['path'])
    point = create_geojson_point(md['lat'], md['lng'])
    bbox = get_bounding_box(md['lng'], md['lat'])
    dt = md['datetime']

    assets = {
        'raw_jpg_s3': Asset(
            href=md['path'],
            type='image/jpeg',
            title='Raw JPG',
            description='Raw JPG image taken during drone flight.',
            roles=['data'],
        )
        # TODO: Add this back in when auth is available to serve these files
        # 'raw_jpg': Asset(
        #     href=md['path'].replace("s3://place-data/", "https://stac.thisisplace.org/data/files/"),
        #     type='image/jpeg',
        #     title='Raw JPG',
        #     description='Raw JPG image taken during drone flight.',
        #     roles=['data'],
        # )
    }

    return Item(
        id=id,
        type='Feature',
        collection=collection_id,
        geometry=point,
        bbox=bbox,
        datetime=dt,
        properties={
            "datetime": dt,
            "make": md['make'],
            "model": md['model'],
            "focal_length": md['focal_length'],
            "exposure_time": md['exposure_time'],
            "altitude": md['altitude']
        },
        assets=assets,
        links=[],
    )

def build_stac_collection(collection_id: str, description: str, title: str, items: List[Item]) -> Collection:
    collection_bbox = merge_bboxes([item.bbox for item in items])
    min_dt = min(item.properties.datetime for item in items)
    max_dt = max(item.properties.datetime for item in items)
    collection_interval = [serialize_dt_rfc3339(min_dt), serialize_dt_rfc3339(max_dt)]
    collection_extent = Extent(
        spatial=SpatialExtent(bbox=[collection_bbox]),
        temporal=TimeInterval(interval=[collection_interval])
    )
    place_provider = Provider(
        name='The PLACE Trust',
        description='a permanent legal data trust based in the United Kingdom, which will hold all PLACE data and licenses, received from governments, in perpetuity.',
        roles=[ProviderRoles.host, ProviderRoles.licensor, ProviderRoles.producer],
        url='https://thisisplace.org'

    )
    collection = Collection(
        id=collection_id,
        description=description,
        title=title,
        extent=collection_extent,
        license='PLACE Research License',
        providers=[place_provider],
        summaries={},
        links=[],
    )
    return collection


def parse_arguments():
    parser = argparse.ArgumentParser(description='Process S3 URI and collection ID.')
    parser.add_argument('--collection_id', type=str, help='Collection ID', required=True)
    parser.add_argument('--collection_description', type=str, help='Collection Description', required=True)
    parser.add_argument('--collection_title', type=str, help='Collection Title', required=True)
    parser.add_argument('--input_directory', type=str, help='Directory which contains JPGs to be catalogued', required=True)
    parser.add_argument('--output_directory', type=str, help='Dir to write STAC Items to', required=True)
    parser.add_argument('--output_s3_backup', type=str, help='Optional backup output location as s3 uri', required=False)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    item_file = os.path.join(args.output_directory, args.collection_id + "_items.json")
    collection_file = os.path.join(args.output_directory, args.collection_id + "_collection.json")
    if os.path.exists(collection_file):
        print(f"Collection file already exists: {collection_file}")
        sys.exit(0)

    ### Build STAC Items and Collection
    item_count = 0
    print(f"Constructing items from {args.input_directory}")
    items: List[Item] = []
    for item_metadata in read_all_metadata(args.input_directory):
        item_count += 1
        item = build_stac_item(item_metadata, args.collection_id)
        items.append(item)

    print("Constructing collection")
    collection = build_stac_collection(args.collection_id, args.collection_description, args.collection_title, items)


    ### Write STAC Items and Collection to file
    print(f"Writing collection to file: {collection_file}")
    with open(collection_file, 'w') as f:
        f.write(collection.to_json())

    print(f"Writing items to file: {item_file}")
    with open(item_file, 'w') as f:
        for item in items:
            try:
                f.write(item.to_json() + '\n')
            except Exception:
                print(f"Error writing item to file: {item.id}")
                pprint.pprint(item)
                print(traceback.format_exc())

    if args.output_s3_backup:
        item_file_s3 = os.path.join(args.output_s3_backup, args.collection_id + "_items.json")
        collection_file_s3 = os.path.join(args.output_s3_backup, args.collection_id + "_collection.json")
        print(f"Uploading item file to S3: {item_file_s3}")
        item_bucket, item_key = parse_s3uri(item_file_s3)
        s3.upload_file(item_file, item_bucket, item_key)

        print(f"Uploading collection file to S3: {collection_file_s3}")
        collection_bucket, collection_key = parse_s3uri(collection_file_s3)
        s3.upload_file(collection_file, collection_bucket, collection_key)

    print(f"Items successfully created: {item_count}")