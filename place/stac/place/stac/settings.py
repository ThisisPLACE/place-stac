from functools import lru_cache
from urllib.parse import urljoin

from pydantic import Field
from stac_fastapi.pgstac.config import Settings as PGStacSettings


class Settings(PGStacSettings):
    tiler_root: str = Field(env="TILER_ROOT", default="")
