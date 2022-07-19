#!/usr/bin/env python3

from ast import Str
from tokenize import Double

import math

import exifread
import numpy as np
import rawpy
import rasterio as rio
from rasterio.control import GroundControlPoint
from rasterio.crs import CRS
from rasterio.io import MemoryFile
from rasterio.plot import reshape_as_raster
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

from rotation import construct_rotation_matrix, rotate


def cogify(
    raw_tif_path: Str,
    dest_tif_path: Str,
    latitude: Double,
    longitude: Double,
    altitude: Double,
    transformation_matrix: np.matrix
) -> None:
    crs = CRS.from_epsg(4326)

    with open(raw_tif_path, "rb") as raw_for_tags:
        raw_tags = exifread.process_file(raw_for_tags)
        tags = {tag: raw_tags[tag] for tag in raw_tags if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote')}

    with rawpy.imread(raw_tif_path) as raw:
        rgb = raw.postprocess()
        img_height = rgb.shape[0]
        img_width = rgb.shape[1]
        bands = rgb.shape[2]

        # approximate in meters
        earth_radius = 6378
        # meters/longitude increases as latitude shifts away from equator
        ms_per_lng = ((math.pi/180) * earth_radius * math.cos(longitude*math.pi/180)) * 1000
        ms_per_lat = 111 * 1000


        # GSD (ground sampling distance) formula used to estimate pixel extent
        # (flight altitude x sensor height or width) / (focal length x image height or width)
        
        # magical numbers (based on the sensor dimensions for the Sony ILCE-7M2)
        sensor_width_cm = 35.8 * 0.1
        sensor_height_cm = 23.9 * 0.1
        focal_length_cm = 24 * 0.1
        altitude_cm = altitude * 100

        # It is possible that the camera is sideways, so we need to account for that here:
        if (img_width > img_height):
            x_resolution = (altitude_cm * sensor_width_cm) / (focal_length_cm * img_width)
            y_resolution = (altitude_cm * sensor_height_cm) / (focal_length_cm * img_height)
        else:
            x_resolution = (altitude_cm * sensor_height_cm) / (focal_length_cm * img_width)
            y_resolution = (altitude_cm * sensor_width_cm) / (focal_length_cm * img_height)
        print(f"x resolution in cm: {x_resolution}")
        print(f"y resolution in cm: {y_resolution}")

        # Construct offsets from the lat/lng center corresponding to image boundaries
        # (division by 100 to move from cm to meters)
        m_y_offset = ((img_height / 2) * y_resolution) / 100
        m_x_offset = ((img_width / 2) * x_resolution) / 100

        # Likely an invalid assumption here. We need the yaw to determine how this image sits in space
        lat_offset = m_y_offset / ms_per_lat
        lng_offset = m_x_offset / ms_per_lng
        print(f"lat offset {lat_offset}")
        print(f"lng offset {lng_offset}")

        # Carry out OPK based rotation
        rotated = rotate(latitude, longitude, lat_offset, lng_offset, transformation_matrix)
        reshaped = reshape_as_raster(rgb)

        # Construct ground control points relating the corners of the image to new, rotated and offset locations
        tl = GroundControlPoint(1, 1, rotated["NW"][1], rotated["NW"][0])
        bl = GroundControlPoint(img_height, 1, rotated["SW"][1], rotated["SW"][0])
        br = GroundControlPoint(img_height, img_width, rotated["SE"][1], rotated["SE"][0])
        tr = GroundControlPoint(1, img_width, rotated["NE"][1], rotated["NE"][0])
        transform = rio.transform.from_gcps([tl, bl, br, tr])
        with MemoryFile() as memfile:
            with memfile.open(driver='GTiff',
                      height=img_height, width=img_width, bands=bands,
                      count=bands, dtype=str(rgb.dtype),
                      crs=crs, transform=transform, nodata=1) as mem:
                # Populate the input file with numpy array
                mem.update_tags(**tags)
                mem.write(reshaped)

                dst_profile = cog_profiles.get("webp")
                cog_translate(
                    mem,
                    dest_tif_path,
                    dst_profile,
                    in_memory=True,
                    quiet=True,
                )
