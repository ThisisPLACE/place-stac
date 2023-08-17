from typing import Any, Dict
from urllib.parse import urljoin

import pystac
from fastapi import Request
from stac_fastapi.types.stac import Collection, Item
from stac_fastapi.types.requests import get_base_url

from place.common.render import RenderConfig
from place.stac.settings import Settings

class LinkInjector:
    """
    A class which organizes information relating STAC entries
    to endpoints which render associated assets. Used within the
    Planetary Computer to inject links from catalog entries to
    tiling endpoints

    ...

    Attributes
    ----------
    collection_id : str
        The ID of a STAC Collection in the PC
    render_config : RenderConfig
        Details about the collection: e.g. asset names and convenient
        parameters for rendering those assets
    """

    def __init__(
        self,
        collection_id: str,
        render_config: RenderConfig,
        request: Request,
    ) -> None:
        self.collection_id = collection_id
        self.render_config = render_config
        self.tiler_href = urljoin(get_base_url(request), "data/")

    def inject_collection(self, collection: Collection) -> None:
        """Inject rendering links to a collection"""
        collection.get("links", []).append(self._get_collection_map_link())

        assets = collection.get("assets", {})
        assets["tilejson"] = self._get_collection_tilejson_asset()
        collection["assets"] = assets  # assets not a required property.

    def inject_item(self, item: Item) -> None:
        """Inject rendering links to an item"""
        item_id = item.get("id", "")
        item["links"] = item.get("links", [])
        item["links"].append(self._get_item_map_link(item_id))
        item["links"].append(self._get_item_wmts_link(item_id))

        assets = item.get("assets", {})
        assets["tilejson"] = self._get_item_tilejson_asset(item_id)
        assets["rendered_preview"] = self._get_item_preview_asset(item_id)

    def _get_collection_tilejson_asset(self) -> Dict[str, Any]:
        qs = self.render_config.get_full_render_qs()
        href = urljoin(self.tiler_href, f"collection/tilejson.json?{qs}")

        return {
            "title": "Mosaic TileJSON with default rendering",
            "href": href,
            "type": pystac.MediaType.JSON,
            "roles": ["tiles"],
        }

    def _get_collection_map_link(self) -> Dict[str, Any]:
        href = urljoin(
            self.tiler_href,
            f"collection/map?collection={self.collection_id}",
        )

        return {
            "rel": pystac.RelType.PREVIEW,
            "href": href,
            "title": "Map of collection mosaic",
            "type": "text/html",
        }

    def _get_item_preview_asset(self, item_id: str) -> Dict[str, Any]:
        qs = self.render_config.get_full_render_qs()
        href = urljoin(self.tiler_href, f"collections/{self.collection_id}/items/{item_id}/preview.png?{qs}")

        return {
            "title": "Rendered preview",
            "rel": "preview",
            "href": href,
            "roles": ["overview"],
            "type": pystac.MediaType.PNG,
        }

    def _get_item_tilejson_asset(self, item_id: str) -> Dict[str, Any]:
        qs = self.render_config.get_full_render_qs()
        href = urljoin(self.tiler_href, f"collections/{self.collection_id}/items/{item_id}/tilejson.json?{qs}")

        return {
            "title": "TileJSON with default rendering",
            "href": href,
            "type": pystac.MediaType.JSON,
            "roles": ["tiles"],
        }

    def _get_item_map_link(self, item_id: str) -> Dict[str, Any]:
        qs = self.render_config.get_full_render_qs_raw()
        href = urljoin(
            self.tiler_href,
            f"collections/{self.collection_id}/items/{item_id}/map?{qs}"
        )

        return {
            "rel": pystac.RelType.PREVIEW,
            "href": href,
            "title": "Map of item",
            "type": "text/html",
        }

    def _get_item_wmts_link(self, item_id: str) -> Dict[str, Any]:
        qs = self.render_config.get_full_render_qs_raw()
        href = urljoin(
            self.tiler_href,
            f"collections/{self.collection_id}/items/{item_id}/WebMercatorQuad/WMTSCapabilities.xml?{qs}",
        )

        return {
            "rel": "WMTS",
            "href": href,
            "title": "WMTS capabilities for item",
            "type": "text/xml",
        }