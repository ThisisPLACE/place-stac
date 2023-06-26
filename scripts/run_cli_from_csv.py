#!/usr/bin/env python3
import argparse
import csv
import multiprocessing
import os
import subprocess

def execute_cli_command(cli, arg_set):

    argument_strings = []
    for field, value in arg_set.items():
        argument_strings.append(f'--{field.strip()} "{value}"')
    argument_string = " ".join(argument_strings)
    command = cli + " " + argument_string

    try:
        subprocess.run(command, check=True, shell=True)
        print(f"Command executed successfully: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        raise


def parse_csv_to_dict(csv_path):
    data = []

    with open(csv_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            data.append(row)

    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a series of CLI tasks with arguments defined in CSV')

    parser.add_argument('-c', '--csv', metavar='CSV', type=str,
                        help='path to the csv defining CLI args')
    parser.add_argument('-s', '--script', metavar='SCRIPT', type=str,
                        help='path to the python script')
    args = parser.parse_args()

    def execute_script(argument_set):
        return execute_cli_command(args.script, argument_set)

    argument_sets = parse_csv_to_dict(args.csv)
    parallelism = min(os.cpu_count(), 4)
    with multiprocessing.Pool(parallelism) as pool:
        pool.map(execute_script, argument_sets)
