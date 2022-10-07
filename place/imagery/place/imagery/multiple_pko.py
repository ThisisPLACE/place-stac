#!/usr/bin/env python3
import argparse
from multiprocessing import Pool
import sys
from typing import Any, Dict, List, Optional

import botocore

from cogify import cogify
from rotation import construct_rotation_matrix
from version import __version__
from util.tabular import parse_table

def cogify_with_status(path, output_path, rotation_matrix):
    print(f"Processing imagery from {path}")
    cogify(path, output_path, rotation_matrix)
    print(f"Successfully processed; results: {output_path}")


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
        "--jpg-dir",
        help="Directory of jpg images to orthorectify.",
        required=True,
    )

    parser.add_argument(
        "--output-dir",
        help="Location to save output COGs",
        required=True
    )

    parser.add_argument(
        "--pko-table",
        help="Table of phi, kappa, omega transformation values",
        required=True
    )

    parsed_args = {
        k: v for k, v in vars(parser.parse_args(args)).items() if v is not None
    }

    return parsed_args

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    pko_lookup = parse_table(args["pko_table"], offset=1)

    params = []
    for id, pko_dict in pko_lookup.items():
        rotation_matrix = construct_rotation_matrix([
            float(pko_dict["r11"]),
            float(pko_dict["r12"]),
            float(pko_dict["r13"]),
            float(pko_dict["r21"]),
            float(pko_dict["r22"]),
            float(pko_dict["r23"]),
            float(pko_dict["r31"]),
            float(pko_dict["r32"]),
            float(pko_dict["r33"])
        ])
        jpg_path = f"{args['jpg_dir']}/{id}.JPG"
        output_path = f"{args['output_dir']}/{id}.tif"
        params.append((jpg_path, output_path, rotation_matrix))
    try:
        with Pool() as p:
            p.starmap(cogify_with_status, params)
    except botocore.exceptions.ClientError:
        print(f"Failure: Unable to find imagery at {jpg_path}")