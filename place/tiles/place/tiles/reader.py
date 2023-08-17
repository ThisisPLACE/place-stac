"""Custom STAC reader."""

from typing import Any, Dict, Optional, Set, Type

import attr
import pystac
import rasterio
from morecantile import TileMatrixSet
from rasterio.crs import CRS
from rio_tiler.constants import WEB_MERCATOR_TMS, WGS84_CRS
from rio_tiler.errors import InvalidAssetName, MissingAssets
from rio_tiler.io import BaseReader, MultiBaseReader, Reader
from rio_tiler.io.stac import DEFAULT_VALID_TYPE, _get_assets
from rio_tiler.types import AssetInfo
from titiler.pgstac.reader import PgSTACReader


@attr.s
class UrlRewritePgSTACReader(PgSTACReader):

    input: pystac.Item = attr.ib()

    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)
    minzoom: int = attr.ib()
    maxzoom: int = attr.ib()

    geographic_crs: CRS = attr.ib(default=WGS84_CRS)

    include_assets: Optional[Set[str]] = attr.ib(default=None)
    exclude_assets: Optional[Set[str]] = attr.ib(default=None)

    include_asset_types: Set[str] = attr.ib(default=DEFAULT_VALID_TYPE)
    exclude_asset_types: Optional[Set[str]] = attr.ib(default=None)

    reader: Type[BaseReader] = attr.ib(default=Reader)
    reader_options: Dict = attr.ib(factory=dict)

    ctx: Any = attr.ib(default=rasterio.Env)

    @minzoom.default
    def _minzoom(self):
        return self.tms.minzoom

    @maxzoom.default
    def _maxzoom(self):
        return self.tms.maxzoom

    def _get_asset_info(self, asset: str) -> AssetInfo:
        """Validate asset names and return rewritten asset url.

        This is useful if, for instance, a publicly accessible URI
        would more quickly be accessed via a private URI.

        Args:
            asset (str): STAC asset name.

        Returns:
            str: STAC asset href, rewritten.

        """
        asset_info = super()._get_asset_info(asset)
        # Hardcoding these values to make it simple for future developers and because we
        #  are targeting only one deployment environment.
        print(f"NON updated asset info: {asset_info}")
        asset_info["url"] = asset_info["url"].replace(
            "s3://place-data/",
            "/home/storage/imagery/"
        )
        print(f"updated asset info: {asset_info}")
        return asset_info