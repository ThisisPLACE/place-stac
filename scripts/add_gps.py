#!/usr/bin/env python3
import argparse
import glob
import os

from GPSPhoto import gpsphoto

def make_label_geotags(prefix, item):
    return {
        "input_file": f"{prefix}/{item[0]}",
        "latitude": float(item[1]),
        "longitude": float(item[2]),
        "altitude": int(round(float(item[3])))
    }


def make_label_nonstandard(prefix, item):
    try:
        return {
            "input_file": f"{prefix}/{item[1]}",
            "latitude": float(item[2]),
            "longitude": float(item[3]),
            "altitude": int(round(float(item[4])))
        }
    except ValueError:
        return {
            "input_file": f"{prefix}/{item[3]}",
            "latitude": float(item[0]),
            "longitude": float(item[1]),
            "altitude": int(round(float(item[2])))
        }

def make_gps(label):
    return (
        label["input_file"],
        gpsphoto.GPSInfo(
            (float(label["latitude"]), float(label["longitude"])),
            alt=int(round(float(label["altitude"]), 0))
        )
    )


def find_csv_files(directory):
    csv_files = []

    directory = directory.rstrip("/")
    for file in glob.glob(os.path.join(directory, "*.csv")):
        csv_files.append(file)

    return csv_files


def run_dir(dir_path):
    res = []
    if os.path.exists(f"{dir_path}/Geotags.txt"):
        with open(f"{dir_path}/Geotags.txt") as f:
            for line in f:
                result = line.strip("\n")
                result = result.split("\t")
                label = make_label_geotags(dir_path, result)
                gps = make_gps(label)
                res.append(gps)
    else: # Heuristic to find CSV file if no geotags is found
        csv_file = find_csv_files(dir_path)[0]
        with open(csv_file) as f:
            lines = f.readlines()[1:]
        for line in lines:
            result = line.strip("\n")
            result = result.split(",")
            label = make_label_nonstandard(dir_path, result)
            gps = make_gps(label)
            res.append(gps)
    return res


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')

    # Add the directory path argument
    parser.add_argument('-i', '--input_directory', metavar='IN_DIRECTORY', type=str,
                        help='path to the input directory')
    parser.add_argument('-o', '--output_directory', metavar='OUT_DIRECTORY', type=str,
                        help='path to the output directory')
    parser.add_argument('-p', '--output_prefix', metavar='OUT_DIRECTORY', type=str,
                        help='path to the output directory', default="")
    
    args = parser.parse_args()

    os.makedirs(args.output_directory, exist_ok=True)
    errored = []
    for record in run_dir(args.input_directory):
        output_filename = f"{args.output_prefix}{os.path.basename(record[0])}"
        output_path = f"{args.output_directory}/{output_filename}"
        # Skip if the file already exists
        if os.path.exists(output_path):
            print(f"File {output_path} already exists. Skipping.")
            continue
        try:
            gpsphoto.GPSPhoto(record[0]).modGPSData(record[1], output_path)
        except FileNotFoundError as e:
            errored.append(record)
            print(f"WARNING: did not find file at {record[0]}. Skipping.")
        print(f"Writing updated files to {output_path}")
    if len(errored) > 0:
        print(f"WARNING: {len(errored)} files were not found. See errors above for details.")