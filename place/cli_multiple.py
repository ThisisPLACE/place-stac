#!/usr/bin/env python3
import argparse
import sys
from typing import Any, Dict, List, Optional

from cogify import cogify
from rotation import construct_rotation_matrix
from version import __version__
from util.tabular import parse_table

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
        "--raw-image-dir",
        help="Directory of raw images to orthorectify.",
        required=True,
    )

    parser.add_argument(
        "--output-dir",
        help="Location to save output COGs",
        required=True
    )

    parser.add_argument(
        "--location-table",
        help="Table of imagery locations",
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

    location_lookup = parse_table(args["location_table"])
    pko_lookup = parse_table(args["pko_table"], offset=1)

    success_count = 0
    for location_id, location_dict in location_lookup.items():
        if (location_id not in pko_lookup):
            print(f"Warning: ID {location_id} not found in pko file. Unable to orthorectify; skipping...")
        else:
            pko_dict = pko_lookup[location_id]


            rotation_matrix = construct_rotation_matrix([
                pko_dict["r11"],
                pko_dict["r12"],
                pko_dict["r13"],
                pko_dict["r21"],
                pko_dict["r22"],
                pko_dict["r23"],
                pko_dict["r31"],
                pko_dict["r32"],
                pko_dict["r33"]
            ])
            raw_path = f"{args['raw_image_dir']}/{args['# PhotoID']}.ARW"
            output_path = f"{args['output_dir']}/{args['# PhotoID']}.tif"
            cogify(args["raw_image"], args["output"], location_lookup["Y"], location_lookup["X"], location_lookup["Z"], rotation_matrix)
            success_count += 1

    print(f"Successfully converted {success_count}/{len(location_lookup)} images in location table")
