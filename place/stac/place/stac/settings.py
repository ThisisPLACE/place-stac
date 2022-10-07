from functools import lru_cache
from urllib.parse import urljoin

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    tiler_root: str = Field(env="TILER_ROOT", default="")


    class Config:
        env_prefix = "PLACE_"
        extra = "ignore"
        env_nested_delimiter = "__"