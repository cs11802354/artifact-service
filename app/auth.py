"""Shared-key gate, same shape as ai-workforce's shared-password auth: no
accounts, just a bearer key that keeps the endpoint from being open to
anyone who finds the URL. No key configured means the gate is off."""

import secrets

from fastapi import Depends, HTTPException, Request

from app.config import settings


def auth_enabled() -> bool:
    return bool(settings.api_key)


async def require_api_key(request: Request) -> None:
    if not auth_enabled():
        return

    header = request.headers.get("authorization", "")
    scheme, _, key = header.partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(key, settings.api_key):
        raise HTTPException(401, "Not authenticated")


AuthDep = Depends(require_api_key)
