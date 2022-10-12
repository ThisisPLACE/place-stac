from dataclasses import dataclass, field

from fastapi import Query, Request
from fastapi.responses import ORJSONResponse
from psycopg_pool import ConnectionPool
from titiler.core import dependencies
from titiler.pgstac.factory import MosaicTilerFactory

from place.tiles.reader import PGSTACBackend, ReaderParams


@dataclass
class AssetsBidxExprParams(dependencies.AssetsBidxExprParams):

    collection: str = Query(None, description="STAC Collection ID")


@dataclass(init=False)
class BackendParams(dependencies.DefaultDependency):
    """backend parameters."""

    pool: ConnectionPool = field(init=False)
    request: Request = field(init=False)

    def __init__(self, request: Request):
        """Initialize BackendParams"""
        self.pool = request.app.state.dbpool
        self.request = request


pgstac_mosaic_factory = MosaicTilerFactory(
    reader=PGSTACBackend,
    layer_dependency=AssetsBidxExprParams,
    reader_dependency=ReaderParams,
    router_prefix="/mosaic",
    backend_dependency=BackendParams,
)
