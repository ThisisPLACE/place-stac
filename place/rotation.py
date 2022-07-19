#!/usr/bin/env python3

import math

import numpy as np


def flatten(xss):
    """Efficiently flatten a python list."""
    return [x for xs in xss for x in xs]

def construct_rotation_matrix(matrix_elements) -> np.matrix:
    """Construct rotation matrix from matrix elements"""
    return np.matrix([
        [matrix_elements[0], matrix_elements[1], matrix_elements[2]],
        [matrix_elements[3], matrix_elements[4], matrix_elements[5]],
        [matrix_elements[6], matrix_elements[7], matrix_elements[8]]
    ])

def construct_rotation_matrix_opk(omega, phi, kappa) -> np.matrix:
    """Construct rotation matrix with omega, phi, kappa values.
    
    c.f. https://s3.amazonaws.com/mics.pix4d.com/KB/documents/Pix4D_Yaw_Pitch_Roll_Omega_to_Phi_Kappa_angles_and_conversion.pdf"""
    # Note: This gives a different result than the values in the CSV provided (r11-r33), so those will be used for now
    rotation_x = np.matrix([
        [1, 0, 0],
        [0, math.cos(omega), -math.sin(omega)],
        [0, math.sin(omega), math.cos(omega)]
    ])
    rotation_y = np.matrix([
        [math.cos(phi), 0, math.sin(phi)],
        [0, 1, 0],
        [-math.sin(phi), 0, math.cos(phi)]
    ])
    rotation_z = np.matrix([
        [math.cos(kappa), -math.sin(kappa), 0],
        [math.sin(kappa), math.cos(kappa), 0],
        [0, 0, 1]
    ])
    # Construct the full, 3d rotation matrix 
    return rotation_x * rotation_y * rotation_z

def _rotate_point(point, rotation_matrix, latitude, longitude) -> np.ndarray:
    """Apply rotation matrix to a point"""

    # TODO: We need to verify whether the lat offset should be reflected across the y-axis. See note:
    '''Note that the x/y axes of this (3D) image coordinate system are not
    aligned with the standard (2D) image coordinate system that is used to
    describe (pixel) positions on an image: The y-axis is flipped.'''
    rotated = rotation_matrix.dot(point)
    reshaped = rotated.reshape((3,1))
    reshaped[0] = latitude + reshaped[0]
    reshaped[1] = longitude + reshaped[1]
    return reshaped

def rotate(latitude, longitude, lat_offset, lng_offset, rotation_matrix, debug=False):
    """Construct an omega-phi-kappa transformation matrix to rotate extent around image center"""

    # Construct lat/lng offsets from the image center
    IMG_NE = np.array((lat_offset, lng_offset, 0))
    IMG_SE = np.array((-lat_offset, lng_offset, 0))
    IMG_SW = np.array((-lat_offset, -lng_offset, 0))
    IMG_NW = np.array((lat_offset, -lng_offset, 0))
    # Rotate all extent points around center of image
    NE_ROTATED = _rotate_point(IMG_NE, rotation_matrix, latitude, longitude)
    SE_ROTATED = _rotate_point(IMG_SE, rotation_matrix, latitude, longitude)
    SW_ROTATED = _rotate_point(IMG_SW, rotation_matrix, latitude, longitude)
    NW_ROTATED = _rotate_point(IMG_NW, rotation_matrix, latitude, longitude)

    results = {
        "NE": flatten(NE_ROTATED.tolist()[:2]),
        "SE": flatten(SE_ROTATED.tolist()[:2]),
        "SW": flatten(SW_ROTATED.tolist()[:2]),
        "NW": flatten(NW_ROTATED.tolist()[:2]),
    }
    if debug:
        results["INPUTS"] = [IMG_NE, IMG_SE, IMG_SW, IMG_NW],
        results["OUTPUTS"] = [NE_ROTATED, SE_ROTATED, SW_ROTATED, NW_ROTATED]
    return results