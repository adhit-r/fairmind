"""Common utility functions for FairMind backend."""

import hashlib
import secrets
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import json


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    unique_part = secrets.token_hex(8)
    return f"{prefix}{unique_part}" if prefix else unique_part


def hash_string(value: str, algorithm: str = "sha256") -> str:
    """Hash a string using the specified algorithm."""
    hasher = hashlib.new(algorithm)
    hasher.update(value.encode('utf-8'))
    return hasher.hexdigest()


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def safe_json_loads(value: str, default: Any = None) -> Any:
    """Safely parse JSON string, returning default on error."""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(value: Any, default: str = "{}") -> str:
    """Safely serialize to JSON, returning default on error."""
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return default


def chunks(lst: List, n: int):
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
