#!/usr/bin/env python3

import openpyxl
import csv


def _construct_lookup_from_xlsx(xlsx_path, offset):
    """Parse xlsx data format to lookup table"""
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active

    records = {}
    header_row = 0 + offset
    for idx, row in enumerate(ws.iter_rows(values_only=True)):
        if idx < header_row:
            pass
        elif idx == header_row:
            row_length = len(row)
            column_headings = row
            def parse_row(new_row):
                row_dict = {}
                for col_idx in range(row_length):
                    row_dict[column_headings[col_idx]] = new_row[col_idx]
                records[new_row[0]] = row_dict
        else:
            parse_row(row)

    return records


def _construct_lookup_from_csv(csv_path, offset, delimiter=","):
    """Parse csv data format to lookup table"""
    records = {}
    header_row = 0 + offset
    with open(csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter, quotechar='|')
        for idx, row in enumerate(reader):
            if idx < header_row:
                pass
            elif idx == header_row:
                row_length = len(row)
                column_headings = row
                def parse_row(new_row):
                    row_dict = {}
                    for col_idx in range(row_length):
                        row_dict[column_headings[col_idx]] = new_row[col_idx]
                    records[new_row[0]] = row_dict
            else:
                parse_row(row)

    return records


def parse_table(tabular_data_path, offset=0):
    """Parse tabular data format to lookup table"""
    extension = tabular_data_path.split(".")[-1]
    if (extension == "xlsx"):
        records = _construct_lookup_from_xlsx(tabular_data_path, offset)
    elif (extension == "csv"):
        records = _construct_lookup_from_csv(tabular_data_path, offset)
    elif (extension == "txt"):
        records = _construct_lookup_from_csv(tabular_data_path, offset, "\t")
    else:
        raise ValueError(f"Currently supported extensions: xlsx and csv. Unable to process {extension}.")
    return records
