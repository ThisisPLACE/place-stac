from typing import Any, Dict
import urllib

import orjson


def orjson_dumps(v: Dict[str, Any], *args: Any, default: Any) -> str:
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()

def get_param_str(params: Dict[str, Any]) -> str:
    parts = []
    for k, v in params.items():
        if isinstance(v, list):
            for v2 in v:
                parts.append(f"{k}={urllib.parse.quote_plus(str(v2))}")
        else:
            parts.append(f"{k}={urllib.parse.quote_plus(str(v))}")

    return "&".join(parts)

def get_param_str_raw(params: Dict[str, Any]) -> str:
    parts = []
    for k, v in params.items():
        if isinstance(v, list):
            for v2 in v:
                parts.append(f"{k}={str(v2)}")
        else:
            parts.append(f"{k}={str(v)}")

    return "&".join(parts)