import logging
from typing import List, Type
from urllib.parse import urljoin

import attr
from fastapi import Request
from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.types.search import BaseSearchPostRequest
from stac_fastapi.types.stac import (
    Collection,
    Collections,
    Item,
    ItemCollection,
    LandingPage,
)


logger = logging.getLogger(__name__)


@attr.s
class PlaceClient(CoreCrudClient):
    """Client for core endpoints defined by stac."""

    # https://github.com/microsoft/planetary-computer-apis/blob/c177bcc3338010668a4d16a9744b59b74c6f525e/pcstac/pcstac/client.py#L267-L282
    @classmethod
    def create(
        cls,
        post_request_model: Type[BaseSearchPostRequest],
        extra_conformance_classes: List[str] = [],
    ) -> "PlaceClient":
        it = cls(  # type: ignore
            landing_page_id="place",
            title="PLACE STAC API",
            description="Spatiotemporal Asset Catalog managed by PLACE",
            extra_conformance_classes=extra_conformance_classes,
            post_request_model=post_request_model,
        )
        return it