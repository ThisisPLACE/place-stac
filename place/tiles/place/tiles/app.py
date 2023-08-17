"""Place Tiler"""
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette_cramjam.middleware import CompressionMiddleware
from titiler.application import __version__ as titiler_version
from titiler.pgstac.db import close_db_connection, connect_to_db
from titiler.pgstac.dependencies import ItemPathParams
from titiler.pgstac.reader import PgSTACReader

from titiler.core.resources.enums import OptionalHeader
from titiler.core.factory import (
    AlgorithmFactory,
    MultiBaseTilerFactory,
    TMSFactory,
)
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.middleware import (
    CacheControlMiddleware,
    LoggerMiddleware,
    LowerCaseQueryStringMiddleware,
    TotalTimeMiddleware,
)
from titiler.mosaic.errors import MOSAIC_STATUS_CODES

from place.tiles.settings import Settings
from place.tiles.reader import UrlRewritePgSTACReader


settings = Settings()
print(f"APP SETTINGS DEBUG ON: {settings.debug}")
if settings.debug:
    optional_headers = [OptionalHeader.server_timing, OptionalHeader.x_assets]
else:
    optional_headers = []

app = FastAPI(
    title=settings.name,
    description="A lightweight Cloud Optimized GeoTIFF tile server",
    version=titiler_version,
    root_path=settings.root_path,
)

###############################################################################
# STAC Item Endpoints
stac = MultiBaseTilerFactory(
    reader=UrlRewritePgSTACReader,
    path_dependency=ItemPathParams,
    optional_headers=optional_headers,
    router_prefix="/collections/{collection_id}/items/{item_id}",
)
app.include_router(
    stac.router, tags=["Item"], prefix="/collections/{collection_id}/items/{item_id}"
)

###############################################################################
# TileMatrixSets endpoints
tms = TMSFactory()
app.include_router(tms.router, tags=["Tiling Schemes"])

###############################################################################
# Algorithms endpoints
algorithms = AlgorithmFactory()
app.include_router(algorithms.router, tags=["Algorithms"])

#add_exception_handlers(app, DEFAULT_STATUS_CODES)
#add_exception_handlers(app, MOSAIC_STATUS_CODES)


# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.add_middleware(
    CompressionMiddleware,
    minimum_size=0,
    exclude_mediatype={
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/jp2",
        "image/webp",
    },
)

app.add_middleware(
    CacheControlMiddleware,
    cachecontrol=settings.cachecontrol,
    exclude_path={r"/health"},
)

if settings.debug:
    app.add_middleware(LoggerMiddleware, headers=True, querystrings=True)
    app.add_middleware(TotalTimeMiddleware)

if settings.lower_case_query_parameters:
    app.add_middleware(LowerCaseQueryStringMiddleware)


@app.get("/health", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}

@app.on_event("startup")
async def startup_event() -> None:
    """Connect to database on startup."""
    await connect_to_db(app)

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close database connection."""
    await close_db_connection(app)


if settings.debug:
    app.add_middleware(LoggerMiddleware, headers=True, querystrings=True)
    app.add_middleware(TotalTimeMiddleware)

if settings.lower_case_query_parameters:
    app.add_middleware(LowerCaseQueryStringMiddleware)

def run():
    """Run app from command line using uvicorn if available."""
    try:
        import uvicorn

        uvicorn.run(
            "place.tiles.app:app",
            host=settings.host,
            port=settings.port,
            log_level="debug",
            reload=settings.reload,
        )
    except ImportError:
        raise RuntimeError("Uvicorn must be installed in order to use command")


if __name__ == "__main__":
    run()


def create_handler(app):
    """Create a handler to use with AWS Lambda if mangum available."""
    try:
        from mangum import Mangum

        return Mangum(app)
    except ImportError:
        return None


handler = create_handler(app)