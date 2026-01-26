#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from compass.utils.io import ensure_empty_dir
from compass.data.oulad import build_oulad_snapshot
from compass.data.assistments import build_assistments_snapshot


def main() -> int:
    ap = argparse.ArgumentParser(description="Build processed dataset snapshot (maintainer tool).")
    ap.add_argument("--dataset", required=True, choices=["oulad_v1", "assistments_2009_2010_v1"])
    ap.add_argument("--raw-dir", required=True, help="Path to raw dataset files (local).")
    ap.add_argument("--out-dir", required=True, help="Output directory to write processed snapshot folder.")
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)

    ensure_empty_dir(out_dir)

    if args.dataset == "oulad_v1":
        build_oulad_snapshot(raw_dir, out_dir)
    else:
        build_assistments_snapshot(raw_dir, out_dir)

    print(f"Snapshot built at: {out_dir}")
    print("Next steps: archive it (.zip/.tar.gz), compute sha256, publish (Zenodo/GH release), update snapshots/catalog.yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
