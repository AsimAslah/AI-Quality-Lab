from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.config import get_settings


settings = get_settings()
SECRET_PATTERN = re.compile(
    r"(?i)(sk-[a-z0-9_-]{12,}|api[_-]?key\s*[:=]\s*\S+|password\s*[:=]\s*\S+|postgres(?:ql)?://\S+)"
)


def new_owner_token() -> str:
    return secrets.token_urlsafe(32)


def hash_owner_token(token: str) -> str:
    return hmac.new(settings.session_secret.encode(), token.encode(), hashlib.sha256).hexdigest()


def redact_error(value: object) -> str:
    message = SECRET_PATTERN.sub("[REDACTED]", str(value))
    return message[:280]


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: int = 60) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= now - window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                raise HTTPException(status_code=429, detail="Too many requests. Please try again shortly.")
            hits.append(now)


rate_limiter = RateLimiter()


def require_owner(request: Request) -> str:
    owner_hash = getattr(request.state, "owner_hash", None)
    if not owner_hash:
        raise HTTPException(status_code=401, detail="Session unavailable")
    return owner_hash
