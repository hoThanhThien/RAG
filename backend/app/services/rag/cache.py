from __future__ import annotations

import base64
import json
import logging
import time
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple

import numpy as np

try:
    import redis  # type: ignore
except Exception:
    redis = None


logger = logging.getLogger(__name__)


class InMemoryTTLCache:
    def __init__(self, max_size: int):
        self.max_size = max_size
        self._data: "OrderedDict[str, Tuple[float, Any]]" = OrderedDict()

    def get(self, key: str) -> Any | None:
        now = time.time()
        item = self._data.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at <= now:
            self._data.pop(key, None)
            return None
        self._data.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._data[key] = (time.time() + ttl_seconds, value)
        self._data.move_to_end(key)
        self._prune()

    def clear(self) -> None:
        self._data.clear()

    def _prune(self) -> None:
        now = time.time()
        expired_keys = [key for key, (expires_at, _) in self._data.items() if expires_at <= now]
        for key in expired_keys:
            self._data.pop(key, None)
        while len(self._data) > self.max_size:
            self._data.popitem(last=False)


class RedisCache:
    def __init__(self, url: str, key_prefix: str, timeout_seconds: int):
        if redis is None:
            raise RuntimeError("redis package is not installed")
        self.key_prefix = key_prefix.rstrip(":")
        self.client = redis.Redis.from_url(url, socket_timeout=timeout_seconds, socket_connect_timeout=timeout_seconds, decode_responses=False)

    def _key(self, key: str) -> str:
        return f"{self.key_prefix}:{key}"

    def get_bytes(self, key: str) -> bytes | None:
        try:
            return self.client.get(self._key(key))
        except Exception:
            logger.exception("Redis get_bytes failed for key=%r", key)
            return None

    def set_bytes(self, key: str, value: bytes, ttl_seconds: int) -> None:
        try:
            self.client.setex(self._key(key), ttl_seconds, value)
        except Exception:
            logger.exception("Redis set_bytes failed for key=%r", key)

    def get_json(self, key: str) -> Dict[str, Any] | None:
        payload = self.get_bytes(key)
        if not payload:
            return None
        try:
            return json.loads(payload.decode("utf-8"))
        except Exception:
            logger.exception("Redis get_json decode failed for key=%r", key)
            return None

    def set_json(self, key: str, value: Dict[str, Any], ttl_seconds: int) -> None:
        try:
            self.set_bytes(key, json.dumps(value, ensure_ascii=False).encode("utf-8"), ttl_seconds)
        except Exception:
            logger.exception("Redis set_json failed for key=%r", key)

    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except Exception:
            logger.warning("Redis ping failed", exc_info=False)
            return False


def encode_vector(vector: np.ndarray) -> bytes:
    payload = {
        "shape": list(vector.shape),
        "dtype": str(vector.dtype),
        "data": base64.b64encode(vector.astype("float32").tobytes()).decode("ascii"),
    }
    return json.dumps(payload).encode("utf-8")


def decode_vector(payload: bytes) -> np.ndarray | None:
    try:
        data = json.loads(payload.decode("utf-8"))
        raw = base64.b64decode(data["data"])
        vector = np.frombuffer(raw, dtype=np.dtype(data.get("dtype") or "float32"))
        return vector.reshape(data["shape"])
    except Exception:
        logger.exception("Failed to decode vector payload from cache")
        return None