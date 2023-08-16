#!/usr/bin/env python3
import pprint
import traceback
from typing import List

import boto3
from rio_stac import create_stac_item
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

def list_s3_objects(bucket_name: str, prefix: str):
    """List all objects in an S3 bucket with a given prefix."""
    keys = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        keys = keys + [obj['Key'] for obj in page.get('Contents', [])]
    return keys

def build_stac_collection(collection_id: str, description: str, title: str, items: List[Item]) -> Collection:
    # global extent
    collection_bbox = [-180, -90, 180, 90]
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

if __name__ == "__main__":
    collection_file = "/home/storage/imagery/aerial/cog/collection.json"
    item_file = "/home/storage/imagery/aerial/cog/items.json"
    bucket_name = "place-data"
    prefix = "aerial/cog/"

    tif_keys = [key for key in list_s3_objects(bucket_name=bucket_name, prefix=prefix) if key.lower().endswith(".tif") or key.lower().endswith(".tiff")]
    tif_paths = [f"s3://{bucket_name}/{key}" for key in tif_keys]

    # Build STAC Items
    items = []
    for path in tif_paths:
        item = create_stac_item(
            source=path,
            collection="mosaic_preview",
            with_proj=True
        )
        items.append(item)

    # Build STAC Collection
    collection = build_stac_collection(
        collection_id="mosaic_preview",
        description="Preview Mosaics generated from PLACE drone flight imagery",
        title="PLACE Mosaic Previews",
        items=items
    )

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