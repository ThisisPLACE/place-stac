#!/usr/bin/env python3
import argparse
import glob
import os

from GPSPhoto import gpsphoto

def make_label_geotags(prefix, item):
    return {
        "input_file": f"{prefix}/{item[0]}",
        "latitude": item[1],
        "longitude": item[2],
        "altitude": item[3]
    }


def make_label_imageslatlong(prefix, item):
    return {
        "input_file": f"{prefix}/{item[1]}",
        "latitude": item[2],
        "longitude": item[3],
        "altitude": item[4]
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
            label = make_label_imageslatlong(dir_path, result)
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
    for record in run_dir(args.input_directory):
        output_filename = f"{args.output_prefix}{os.path.basename(record[0])}"
        output_path = f"{args.output_directory}/{output_filename}"
        gpsphoto.GPSPhoto(record[0]).modGPSData(record[1], output_path)
        print(f"Writing updated files to {output_path}")