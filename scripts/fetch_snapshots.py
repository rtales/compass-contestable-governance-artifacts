#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from compass.snapshots.fetch import fetch_snapshot


def main() -> int:
    ap = argparse.ArgumentParser(description="Offline: install dataset snapshots into ./data.")
    ap.add_argument("--catalog", default="snapshots/catalog.yaml")
    ap.add_argument("--dataset", required=True)
    args = ap.parse_args()

    fetch_snapshot(args.dataset, Path(args.catalog))
    print(f"OK installed: {args.dataset}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
