"""Per-client sliding-window rate limit.

In-memory, so it only holds correctly for a single process — which is what's
actually deployed (`uvicorn app.main:app` with the default one worker, no
multi-process/multi-instance setup). If this service is ever scaled out
horizontally, this needs to move to a shared store (e.g. Redis) instead.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

WINDOW_SECONDS = 60
MAX_REQUESTS = int(os.environ.get("ARTIFACT_RATE_LIMIT_PER_MIN", "30"))

_hits: dict[str, deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    # Falls back to the auth key when present so a shared NAT/proxy IP
    # doesn't get one client's limit applied to everyone behind it.
    auth = request.headers.get("authorization")
    if auth:
        return auth
    return request.client.host if request.client else "unknown"


async def enforce_rate_limit(request: Request) -> None:
    key = _client_key(request)
    now = time.monotonic()
    hits = _hits[key]

    while hits and now - hits[0] > WINDOW_SECONDS:
        hits.popleft()

    if len(hits) >= MAX_REQUESTS:
        raise HTTPException(429, "Rate limit exceeded. Try again shortly.")

    hits.append(now)
