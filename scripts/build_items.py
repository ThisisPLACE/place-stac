#!/usr/bin/env python
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import math
from urllib.parse import urlparse

import boto3
import pyexiv2
from pyexiv2 import ImageData
from stac_pydantic.item import Item
from stac_pydantic.shared import Asset


# Necessary to work with sony exif data
pyexiv2.set_log_level(4)

# Initialize a session with your AWS credentials
session = boto3.Session()

# Create an S3 client
s3 = session.client('s3')
paginator = s3.get_paginator('list_objects_v2')

def parse_dt(dt_str):
    """Parse a datetime string into a datetime object."""
    return datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')

def parse_dt_rfc3339(dt_str):
    """Convert a datetime string to an RFC 3339-compliant string."""
    rfc3339_str = parse_dt(dt_str).isoformat() + "Z"

    return rfc3339_str


def parse_dt_rfc3339(dt):
    """Convert a datetime object to an RFC 3339-compliant string."""
    input_str = dt
    dt = datetime.strptime(input_str, '%Y:%m:%d %H:%M:%S')

    return dt

def dms_to_decimal(dms_str, direction):
    """Convert a string of degrees, minutes, seconds to decimal degrees."""
    dms_list = dms_str.split(' ')
    d, m, s = [float(fraction.split('/')[0]) / float(fraction.split('/')[1]) for fraction in dms_list]
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


def get_metadata(s3uri: str, maxbytes: int = 65535):
    """Get the metadata from a jpg image stored in S3."""
    bucket_name, key = parse_s3uri(s3uri)
    try:
        response = s3.get_object(
            Bucket=bucket_name,
            Key=key,
            Range=f"bytes=0-{maxbytes}"
        )
        partial_data = response['Body'].read()
        exif_data = ImageData(partial_data).read_exif()
        return exif_data
    except Exception as e:
        print(bucket_name, key)


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

def read_all_metadata(s3uri: str, max_workers=10):
    """Read all metadata from jpg images in an S3 bucket."""
    bucket_name, prefix = parse_s3uri(s3uri)
    obj_keys = [key for key in list_s3_objects(s3uri) if key.endswith(".jpg")]
    obj_paths = [f"s3://{bucket_name}/{key}" for key in obj_keys]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        read_tasks = [executor.submit(get_metadata, f"s3://{bucket_name}/{key}") for key in obj_keys]
        results = [task.result() for task in read_tasks]
    processed = []
    for idx, res in enumerate(results):
        raw_altitude = res['Exif.GPSInfo.GPSAltitude'].split("/")
        altitude = float(raw_altitude[0]) / float(raw_altitude[1])
        processed.append({
            "path": obj_paths[idx],
            "lat": dms_to_decimal(res['Exif.GPSInfo.GPSLatitude'], res['Exif.GPSInfo.GPSLatitudeRef']),
            "lng": dms_to_decimal(res['Exif.GPSInfo.GPSLongitude'], res['Exif.GPSInfo.GPSLongitudeRef']),
            "altitude": altitude,
            "datetime": parse_dt(res['Exif.Image.DateTime']),
            "make": res['Exif.Image.Make'],
            "model": res['Exif.Image.Model'],
            "focal_length": res['Exif.Photo.FocalLengthIn35mmFilm'],
            "exposure_time": res['Exif.Photo.ExposureTime']
        })
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
    bbox = get_bounding_box(md['lat'], md['lng'])
    dt = md['datetime']

    assets = {
        'raw_jpg': Asset(
            href=md['path'],
            type='image/jpeg',
            title='Raw JPG',
            description='Raw JPG image taken during drone flight.',
            roles=['data'],
        )
    }

    item = Item(
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

    return item



if __name__ == '__main__':
    for md in read_all_metadata('s3://placetrustuk/TCI/middle_caicos/raw/'):
        item = build_stac_item(md, "middle_caicos")
        print(item.json())
