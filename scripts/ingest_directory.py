import os
import sys
from pathlib import Path

import orjson
from pypgstac.load import Loader, Methods, PgstacDB


# Read directory path from command-line argument
directory = sys.argv[1]
# Get all relevant files in directory
items_files = [file for file in os.listdir(directory) if file.endswith('items.json')]
collection_files = [file for file in os.listdir(directory) if file.endswith('collection.json')]



def load_test_data() -> None:
    with PgstacDB() as conn:
        loader = Loader(db=conn)
        for collection_file in collection_files:
            loader.load_collections(collection_file, Methods.upsert)
        for items_file in items__files:
            loader.load_items(items_file, Methods.upsert)


load_test_data()