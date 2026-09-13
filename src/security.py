from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path
from uuid import uuid4

from fastapi import Header, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Optional API-key authentication for the course prototype.

    If CLOUDSHIELD_API_KEY is configured, callers must provide the same value
    in the X-API-Key header. In production this should be replaced or extended
    with managed identity, OAuth2, or an API gateway authorizer.
    """
    expected = os.getenv("CLOUDSHIELD_API_KEY")
    if not expected:
        return
    if x_api_key is None or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply simple software-security headers and a request correlation ID."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response
