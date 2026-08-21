"""Storage + URL service.

Local disk for v1: content-addressed by artifact id under DATA_DIR, served
back out through FastAPI's StaticFiles mount at /files. Swapping in S3 later
means changing `save` and `url_for` without touching the orchestrator.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

DATA_DIR = Path(os.environ.get("ARTIFACT_DATA_DIR", "/data/artifacts"))

EXTENSIONS = {
    "html": "html",
    "markdown": "md",
}


def new_id() -> str:
    return uuid.uuid4().hex


def save(artifact_id: str, fmt: str, rendered: bytes) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ext = EXTENSIONS[fmt]
    path = DATA_DIR / f"{artifact_id}.{ext}"
    path.write_bytes(rendered)
    return path


def url_for(artifact_id: str, fmt: str, base_url: str) -> str:
    ext = EXTENSIONS[fmt]
    return f"{base_url.rstrip('/')}/files/{artifact_id}.{ext}"
