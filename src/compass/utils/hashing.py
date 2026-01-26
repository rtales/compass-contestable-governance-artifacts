"""Hashing utilities used for reproducible manifests and artifact integrity."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Union


def sha256_bytes(data: bytes) -> str:
    """Return hex SHA-256 of the provided bytes."""
    if data is None:
        raise ValueError("data must not be None")
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Union[str, Path], *, chunk_size: int = 1024 * 1024) -> str:
    """Return hex SHA-256 of a file, streaming in chunks."""
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

