#!/usr/bin/env python3
import argparse
import sys
from typing import Any, Dict, List, Optional

from cogify import cogify
from rotation import construct_rotation_matrix
from version import __version__

def parse_args(args: List[str]) -> Optional[Dict[str, Any]]:
    desc = "PLACE cog conversion CLI"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--version",
        help="Print version and exit",
        action="version",
        version=__version__,
    )

    parser.add_argument(
        "--raw-image",
        help="Location of raw image to orthorectify.",
        required=True,
    )

    parser.add_argument(
        "--output",
        help="Location to save output COG",
        required=True
    )

    parser.add_argument(
        "--latitude",
        type=float,
        help="Center of image latitude",
        required=True
    )

    parser.add_argument(
        "--longitude",
        type=float,
        help="Center of image longitude",
        required=True
    )

    parser.add_argument(
        "--altitude",
        type=float,
        help="Altitude of flight",
        required=True
    )

    parser.add_argument(
        "--rotation-matrix",
        type=float,
        nargs='+',
        help="Transformation matrix values",
        required=True
    )

    parsed_args = {
        k: v for k, v in vars(parser.parse_args(args)).items() if v is not None
    }

    return parsed_args

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    assert len(args["rotation_matrix"]) == 9, f"The rotation matrix requires 9 values, {len(args['transformation_matrix'])} values provided"

    rotation_matrix = construct_rotation_matrix(args["rotation_matrix"])
    cogify(args["raw_image"], args["output"], args["latitude"], args["longitude"], args["altitude"], rotation_matrix)
