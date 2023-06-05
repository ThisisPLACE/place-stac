import os
from pathlib import Path

import orjson
from pypgstac.load import Loader, Methods, PgstacDB

collection = "/app/data/collections/abidjian.json"
items = "/app/data/items"


def load_test_data() -> None:
    with PgstacDB() as conn:
        loader = Loader(db=conn)
        with open(collection, "rb") as f:
            c = orjson.loads(f.read())
            loader.load_collections([c], Methods.upsert)
        item_paths = Path(items).glob("*.json")
        for path in item_paths:
            with open(str(path), "rb") as f:
                i = orjson.loads(f.read())
                loader.load_items([i], Methods.upsert)


load_test_data()