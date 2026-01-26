from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen, Request


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "compass-artifacts/0.1"})
    with urlopen(req) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
