from __future__ import annotations

import json
import os

_ENV_NAME = "EMBOD_PARAMS_JSON"


def _load_params() -> dict[str, str]:
    raw = os.environ.get(_ENV_NAME, "{}")
    loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise ValueError(f"{_ENV_NAME} must decode to a JSON object")
    normalized: dict[str, str] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            raise ValueError("Parameter keys must be strings")
        if isinstance(value, str):
            normalized[key] = value
        elif isinstance(value, bool):
            normalized[key] = "true" if value else "false"
        elif isinstance(value, int | float):
            normalized[key] = str(value)
        else:
            raise ValueError(f"Unsupported parameter type for {key}")
    return normalized


def get_str_param(name: str, default: str) -> str:
    return _load_params().get(name, default)


def get_float_param(name: str, default: float) -> float:
    value = _load_params().get(name)
    return float(value) if value is not None else default


def get_int_param(name: str, default: int) -> int:
    value = _load_params().get(name)
    return int(value) if value is not None else default


def get_bool_param(name: str, default: bool) -> bool:
    value = _load_params().get(name)
    if value is None:
        return default
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Parameter {name} is not a boolean")
