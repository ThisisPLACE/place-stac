from typing import Optional, Type
from dataclasses import dataclass, field
from urllib.parse import urljoin

import attr
from fastapi import Query, Request, Response
from fastapi.templating import Jinja2Templates
from rio_tiler.io.base import BaseReader
from rio_tiler.io.stac import COGReader
from starlette.responses import HTMLResponse
from titiler.core.dependencies import DefaultDependency
from titiler.core.factory import MultiBaseTilerFactory
from titiler.pgstac.dependencies import ItemPathParams
from titiler.pgstac.reader import PgSTACReader

from place.tiles.reader import ReaderParams
from place.tiles.settings import Settings
from place.common.render import get_render_config
#from pccommon.config import get_render_config
#from pctiler.colormaps import PCColorMapParams

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore


# TODO: mypy fails in python 3.9, we need to find a proper way to do this
templates = Jinja2Templates(
    directory=str(resources_files(__package__) / "templates")  # type: ignore
)

@attr.s
class ItemSTACReader(PgSTACReader):

    # TODO: remove CustomCOGReader once moved to rasterio 1.3
    reader: Type[BaseReader] = attr.ib(default=COGReader)

    # We make request an optional attribute to avoid re-writing
    # the whole list of attribute
    request: Optional[Request] = attr.ib(default=None)


pc_tile_factory = MultiBaseTilerFactory(
    reader=ItemSTACReader,
    path_dependency=ItemPathParams,
    reader_dependency=ReaderParams,
    router_prefix="item",
)


@pc_tile_factory.router.get("/map", response_class=HTMLResponse)
def map(
    request: Request,
    collection: str = Query(..., description="STAC Collection ID"),
    item: str = Query(..., description="STAC Item ID"),
) -> Response:
    render_config = get_render_config(collection)
    if render_config is None:
        return Response(
            status_code=404,
            content=f"No item map available for collection {collection}",
        )

    qs: str = render_config.get_full_render_qs(collection, item)
    tilejson_url: str = pc_tile_factory.url_for(request, "tilejson")
    print("TESTING")
    print(tilejson_url)
    print("TESTING")
    print(qs)
    tilejson_url = str(tilejson_url) + str(f"?{qs}")

    item_url = urljoin(
        Settings().get_stac_api_href(request),
        f"collections/{collection}/items/{item}",
    )

    return templates.TemplateResponse(
        "item_preview.html",
        context={
            "request": request,
            "tileJson": tilejson_url,
            "collectionId": collection,
            "itemId": item,
            "itemUrl": item_url,
        },
    )