#!/usr/bin/env python3
import argparse
import csv
import subprocess

def execute_cli_command(cli, args):

    for arg_set in args:
        argument_strings = []
        for field, value in arg_set.items():
            print(field, value)
            argument_strings.append(f'--{field.strip()} "{value}"')
            print(argument_strings)
        argument_string = " ".join(argument_strings)
        print(argument_string)
        command = cli + " " + argument_string
    
        try:
            subprocess.run(command, check=True, shell=True)
            print(f"Command executed successfully: {' '.join(command)}")
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {' '.join(command)}")
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

    arguments = parse_csv_to_dict(args.csv)
    execute_cli_command(args.script, arguments)
