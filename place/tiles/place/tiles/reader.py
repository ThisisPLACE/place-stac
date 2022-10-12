import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Type

import attr
import morecantile
from cogeo_mosaic.errors import NoAssetFoundError
from fastapi import HTTPException
from geojson_pydantic import Polygon
from rio_tiler.errors import InvalidAssetName, MissingAssets, TileOutsideBounds
from rio_tiler.models import ImageData
from rio_tiler.mosaic import mosaic_reader
from starlette.requests import Request
from titiler.core.dependencies import DefaultDependency
from titiler.pgstac import mosaic as pgstac_mosaic

from place.common.render import get_render_config
from place.tiles.settings import Settings

logger = logging.getLogger(__name__)


@dataclass(init=False)
class ReaderParams(DefaultDependency):
    """reader parameters."""

    request: Request = field(init=False)

    def __init__(self, request: Request):
        """Initialize ReaderParams"""
        self.request = request


@attr.s
class PGSTACBackend(pgstac_mosaic.PGSTACBackend):
    """PgSTAC Mosaic Backend."""

    reader: Type[pgstac_mosaic.CustomSTACReader] = attr.ib(init=False, default=pgstac_mosaic.CustomSTACReader)

    # We make request an optional attribute to avoid re-writing
    # the whole list of attribute
    request: Optional[Request] = attr.ib(default=None)

    # Override from PGSTACBackend to use collection
    def assets_for_tile(
        self, x: int, y: int, z: int, collection: Optional[str] = None, **kwargs: Any
    ) -> List[Dict]:
        settings = Settings()

        # Require a collection
        if not collection:
            raise HTTPException(
                status_code=422,
                detail="Tile request must contain a collection parameter.",
            )

        render_config = get_render_config(collection)

        # Don't render if this collection is unconfigured
        if not render_config:
            return []

        # Check that the zoom isn't lower than minZoom
        if render_config.minzoom and render_config.minzoom > z:
            return []

        asset_kwargs = {**kwargs, "items_limit": 10}

        bbox = self.tms.bounds(morecantile.Tile(x, y, z))
        assets = self.get_assets(Polygon.from_bounds(*bbox), **asset_kwargs)

        return assets

    # override from PGSTACBackend to pass through collection
    def tile(
        self,
        tile_x: int,
        tile_y: int,
        tile_z: int,
        reverse: bool = False,
        collection: Optional[str] = None,
        scan_limit: Optional[int] = None,
        items_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        exitwhenfull: Optional[bool] = None,
        skipcovered: Optional[bool] = None,
        **kwargs: Any,
    ) -> Tuple[ImageData, List[str]]:
        """Get Tile from multiple observation."""
        mosaic_assets = self.assets_for_tile(
            tile_x,
            tile_y,
            tile_z,
            collection=collection,
            scan_limit=scan_limit,
            items_limit=items_limit,
            time_limit=time_limit,
            exitwhenfull=exitwhenfull,
            skipcovered=skipcovered,
        )

        if not mosaic_assets:
            raise NoAssetFoundError(
                f"No assets found for tile {tile_z}-{tile_x}-{tile_y}"
            )

        if reverse:
            mosaic_assets = list(reversed(mosaic_assets))

        def _reader(
            item: Dict[str, Any], x: int, y: int, z: int, **kwargs: Any
        ) -> ImageData:
            with self.reader(
                item, tms=self.tms, **self.reader_options  # type: ignore
            ) as src_dst:
                return src_dst.tile(x, y, z, **kwargs)

        tile = mosaic_reader(
            mosaic_assets,
            _reader,
            tile_x,
            tile_y,
            tile_z,
            allowed_exceptions=(TileOutsideBounds, MissingAssets, InvalidAssetName),
            **kwargs,
        )

        return tile