#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from compass.data.validation import validate_processed_dataset


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify processed dataset folder contract (schema + invariants).")
    ap.add_argument("--processed-dir", required=True)
    args = ap.parse_args()

    processed = Path(args.processed_dir)
    report = validate_processed_dataset(processed)
    print(report.to_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
