import os
from pathlib import Path

from pypgstac.load import Loader, Methods, PgstacDB

DATA_DIR =os.path.join(os.path.join(os.path.dirname(__file__), ".."), "data")
collections = os.path.join(DATA_DIR, "collections")
items = os.path.join(DATA_DIR, "items")


def load_test_data() -> None:
    with PgstacDB() as conn:
        loader = Loader(db=conn)
        for coll_path in Path(collections).glob("*.json"):
            loader.load_collections(coll_path, Methods.upsert)
        for item_path in Path(items).glob("*.json"):
            loader.load_items(item_path, Methods.upsert)

load_test_data()