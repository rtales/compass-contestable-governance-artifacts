from __future__ import annotations

import os
import tarfile
from pathlib import Path


def ensure_empty_dir(path: Path) -> None:
    if path.exists():
        # remove contents
        for p in sorted(path.glob("**/*"), reverse=True):
            if p.is_file() or p.is_symlink():
                p.unlink()
            elif p.is_dir():
                try:
                    p.rmdir()
                except OSError:
                    pass
    path.mkdir(parents=True, exist_ok=True)


def safe_extract_tar(tf: tarfile.TarFile, dest: Path) -> None:
    dest = dest.resolve()
    for member in tf.getmembers():
        member_path = (dest / member.name).resolve()
        if not str(member_path).startswith(str(dest)):
            raise RuntimeError("Unsafe tar archive: path traversal detected.")
    tf.extractall(dest)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)
