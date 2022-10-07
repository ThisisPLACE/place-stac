#!/usr/bin/env python3

import math
import os
import tempfile
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import boto3
import exifread
import numpy as np
from PIL import ExifTags, Image
import rawpy
import rasterio as rio
from rasterio.control import GroundControlPoint
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rasterio.plot import reshape_as_raster
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

from rotation import construct_rotation_matrix, rotate
from S3Url import S3Url

GOOD_EXIF = ("DateTime", "Model", "Software")

def download_s3_to_temp(s3_path: str):

    s3 = boto3.client("s3")
    s3url = S3Url(s3_path)

    (fd, temp_path) = tempfile.mkstemp()
    with os.fdopen(mode="w+b", fd=fd) as f:
        s3.download_fileobj(s3url.bucket, s3url.key, f)

    return (fd, temp_path)

def process_raw(raw_img_path: str):
    with open(raw_img_path, "rb") as raw_for_tags:
        raw_tags = exifread.process_file(raw_for_tags)
        tags = {tag: raw_tags[tag] for tag in raw_tags}

    with rawpy.imread(raw_img_path) as raw:
        rgb = raw.postprocess()

    return (rgb, tags)


def process_jpg(jpg_img_path: str):
    img = Image.open(jpg_img_path)
    tags = {
        ExifTags.TAGS[k]: v
        for k, v in img._getexif().items()
    }
    rgb = np.array(img)
    return (rgb, tags)

def degrees_to_radians(nesw: str, degrees, minutes, seconds):
    # Degrees + (Minutes + Seconds/60)/60.
    radians = degrees + (minutes + seconds / 60) / 60
    if nesw in ["N", "E"]:
        signed_radians = radians
    elif nesw in ["S", "W"]:
        signed_radians = -radians
    else:
        raise ValueError("nesw value must be one of N, E, S, or W")
    return signed_radians



def cogify(
    input_img_path: str,
    dest_tif_path: str,
    transformation_matrix: np.matrix
) -> None:

    if input_img_path.lower().startswith("s3"):
        (fd, temp_path) = download_s3_to_temp(input_img_path)
        local_path = temp_path
    else:
        local_path = input_img_path

    if input_img_path.lower().endswith("jpg") or input_img_path.lower().endswith("jpeg"):
        (rgb, tags) = process_jpg(local_path)
    else:
        (rgb, tags) = process_raw(local_path)

    crs = CRS.from_epsg(4326)

    img_height = rgb.shape[0]
    img_width = rgb.shape[1]
    bands = rgb.shape[2]

    # get lat/lng/altitude from exif
    position = tags["GPSInfo"]
    latitude = degrees_to_radians(position[1], position[2][0], position[2][1], position[2][2])
    longitude = degrees_to_radians(position[3], position[4][0], position[4][1], position[4][2])
    altitude = position[6] - 0.12

    # approximate in meters
    earth_radius = 6378
    # meters/longitude increases as latitude shifts away from equator
    ms_per_lng = ((math.pi/180) * earth_radius * math.cos(latitude*math.pi/180)) * 1000
    ms_per_lat = 111.3171 * 1000


    # GSD (ground sampling distance) formula used to estimate pixel extent
    # (flight altitude x sensor height or width) / (focal length x image height or width)
    
    # magical numbers (based on the sensor dimensions for the Sony ILCE-7M2)
    # sensor_width_cm = 35.8 * 0.1
    # sensor_height_cm = 23.9 * 0.1
    # focal_length_cm = 24 * 0.1
    # altitude_cm = altitude * 100

    # magical numbers (based on the sensor dimensions for the Sony ILCE-6000)
    sensor_width_cm = 23.5 * 0.1
    sensor_height_cm = 15.6 * 0.1
    focal_length_cm = 16 * 0.1
    altitude_cm = altitude * 100

    x_resolution = (altitude_cm * sensor_width_cm) / (focal_length_cm * img_width)
    y_resolution = (altitude_cm * sensor_height_cm) / (focal_length_cm * img_height)
    # print(f"x resolution in cm: {x_resolution}")
    # print(f"y resolution in cm: {y_resolution}")

    # Construct offsets from the lat/lng center corresponding to image boundaries
    # (division by 100 to move from cm to meters)
    m_y_offset = ((img_height / 2) * y_resolution) / 100
    m_x_offset = ((img_width / 2) * x_resolution) / 100

    # Here, we determine lat/lng offsets
    lat_offset = m_y_offset / ms_per_lat
    lng_offset = m_x_offset / ms_per_lng
    # print(f"lat offset {lat_offset}")
    # print(f"lng offset {lng_offset}")

    # Carry out OPK based rotation
    rotated = rotate(latitude, longitude, lat_offset, lng_offset, transformation_matrix)
    reshaped = reshape_as_raster(rgb)

    # Construct ground control points relating the corners of the image to new, rotated and offset locations
    tl = GroundControlPoint(0, 0, rotated["TL"][1], rotated["TL"][0], rotated["TL"][2])
    bl = GroundControlPoint(img_height, 0, rotated["BL"][1], rotated["BL"][0], rotated["BL"][2])
    tr = GroundControlPoint(0, img_width, rotated["TR"][1], rotated["TR"][0], rotated["TR"][2])
    br = GroundControlPoint(img_height, img_width, rotated["BR"][1], rotated["BR"][0], rotated["BR"][2])
    transform = rio.transform.from_gcps([tl, bl, tr, br])
    with MemoryFile() as memfile:
        with memfile.open(
            driver="GTiff", height=img_height, width=img_width,
            bands=bands, count=bands, dtype=str(rgb.dtype), crs=crs,
            transform=transform, nodata=1
        ) as mem:
            # Populate the input file with numpy array
            mem.update_tags(**{tag: tags[tag] for tag in tags if tag in GOOD_EXIF})
            mem.write(reshaped)

            dst_profile = cog_profiles.get("webp")
            cog_translate(
                mem,
                dest_tif_path,
                dst_profile,
                in_memory=True,
                quiet=True,
            )
