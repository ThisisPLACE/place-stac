import os
from urllib.parse import urljoin

from fastapi import Request
from pydantic import Field
from titiler.application.settings import ApiSettings

class Settings(ApiSettings):

    host: str = Field(env="TILER_HOST", default="0.0.0.0")
    port: int = Field(env="TILER_PORT", default=8000)
    reload: bool = Field(env="TILER_RELOAD", default=True)

    def get_stac_api_href(self, request: Request) -> str:
        """Generates the STAC API HREF.
        If the setting for the stac_api_href
        is relative, then use the request's base URL to generate the
        absolute URL.
        """
        if request:
            base_hostname = f"{request.url.scheme}://{request.url.netloc}/"
            return urljoin(base_hostname, self.stac_api_href)
        else:
            return self.stac_api_href