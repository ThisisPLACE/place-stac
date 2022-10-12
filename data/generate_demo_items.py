#!/usr/bin/env python3
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path

import boto3
import pystac
import rasterio
from rasterio.session import AWSSession

from pystac.utils import str_to_datetime
from rio_stac import stac
from rasterio.session import AWSSession


ENDPOINT_URL="https://s3.af-south-1.amazonaws.com"
AWS_SESSION = AWSSession(endpoint_url=ENDPOINT_URL, region_name="af-south-1")

def create_item(
    properties,
    datetime,
    cog_url,
    collection,
) -> pystac.Item:
    """
    Function to create a stac item from a COG using rio_stac
    """

    rasterio_kwargs = {}

    with rasterio.Env(
        session=AWS_SESSION,
        options={
            **rasterio_kwargs,
            "GDAL_MAX_DATASET_POOL_SIZE": 1024,
            "GDAL_DISABLE_READDIR_ON_OPEN": False,
            "GDAL_CACHEMAX": 1024000000,
            "GDAL_HTTP_MAX_RETRY": 4,
            "GDAL_HTTP_RETRY_DELAY": 1,
        },
    ):
        item = stac.create_stac_item(
            id=Path(cog_url).stem,
            source=cog_url,
            collection=collection,
            input_datetime=datetime,
            properties=properties,
            with_proj=True,
            with_raster=True,
            asset_name="cog",
            asset_roles=["data", "layer"],
            asset_media_type=(
                "image/tiff; application=geotiff; profile=cloud-optimized"
            ),
        )
        item.id = item.id.split("_")[0]
        item.links = []
        return item


def find_tif_keys():

    client = boto3.client('s3', endpoint_url=ENDPOINT_URL, region_name="af-south-1")
    response = client.list_objects_v2(
        Bucket="placetrustafrica",
        Prefix="Ivory Coast/Abidjan/Drone Imagery/Images_Drones/Drone_V-MAP/Adjame/Flight 2S/cog/"
    )
    keys = [obj["Key"].replace(" ", "+") for obj in response["Contents"] if obj["Key"].endswith("tif")]
    return keys


def build_stac_item(key):
    cog_url = f"https://placetrustafrica.s3.af-south-1.amazonaws.com/{key}"
    with rasterio.Env(
        session=AWS_SESSION,
        GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',
    ):
        with rasterio.open(cog_url) as src:
            tags = src.tags()
            dt = datetime.strptime(tags["DateTime"], "%Y:%m:%d %H:%M:%S")
            camera = tags["Model"]
        item = create_item(
            properties={"camera": camera},
            datetime=dt,
            cog_url=cog_url,
            collection="IvoryCoast-Abidjian-Adjame",
        )
        item.save_object(
            include_self_link=False,
            dest_href=f"data/items/{item.id}.json"
        )


if __name__ == "__main__":
    tif_keys = find_tif_keys()
    with Pool() as p:
        p.map(build_stac_item, tif_keys)

