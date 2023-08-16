"""Custom STAC reader."""

from typing import Dict, Optional, Set, Type

import attr
import pystac
from morecantile import TileMatrixSet
from rasterio.crs import CRS
from rio_tiler.constants import WEB_MERCATOR_TMS, WGS84_CRS
from rio_tiler.io import BaseReader, COGReader
from rio_tiler.io.stac import DEFAULT_VALID_TYPE
from titiler.pgstac.reader import PgSTACReader


class UrlRewritePgSTACReader(PgSTACReader):

    input: pystac.Item = attr.ib()

    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)
    minzoom: int = attr.ib(default=None)
    maxzoom: int = attr.ib(default=None)

    geographic_crs: CRS = attr.ib(default=WGS84_CRS)

    include_assets: Optional[Set[str]] = attr.ib(default=None)
    exclude_assets: Optional[Set[str]] = attr.ib(default=None)

    include_asset_types: Set[str] = attr.ib(default=DEFAULT_VALID_TYPE)
    exclude_asset_types: Optional[Set[str]] = attr.ib(default=None)

    reader: Type[BaseReader] = attr.ib(default=COGReader)
    reader_options: Dict = attr.ib(factory=dict)

    def _get_asset_url(self, asset: str) -> str:
        """Validate asset names and return rewritten asset url.

        This is useful if, for instance, a publicly accessible URI
        would more quickly be accessed via a private URI.

        Args:
            asset (str): STAC asset name.

        Returns:
            str: STAC asset href, rewritten.

        """
        asset_url = super()._get_asset_url(asset)
        # Hardcoding these values to make it simple for future developers and because we
        #  are targeting only one deployment environment.
        return asset_url.replace(
            "s3://place-data/",
            "file:///home/storage/imagery/"
        )