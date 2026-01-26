from __future__ import annotations

from pathlib import Path
import yaml

from compass.utils.io import ensure_empty_dir
from compass.data.synthetic import build_synthetic_snapshot
from compass.data.oulad import build_oulad_processed_from_zip
from compass.data.assistments import build_assistments_processed_from_csv


def fetch_snapshot(dataset_id: str, catalog_path: Path, datasets_root: Path = Path("datasets")) -> None:
    """Install dataset snapshots offline.

    Modes supported in snapshots/catalog.yaml:
      - local_generate: generate deterministic synthetic data
      - local_process: process raw local files under ./datasets into ./data/<dataset_id>
    """
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    entry = next((e for e in catalog.get("snapshots", []) if e.get("dataset_id") == dataset_id), None)
    if not entry:
        raise ValueError(f"Dataset not found in catalog: {dataset_id}")

    mode = entry.get("mode")
    unpack_dir = Path(entry.get("unpack_dir", f"data/{dataset_id}"))

    if mode == "local_generate":
        ensure_empty_dir(unpack_dir)
        build_synthetic_snapshot(unpack_dir)
        return

    if mode == "local_process":
        raw_path = entry.get("raw_path")
        if not raw_path:
            raise ValueError(f"Missing raw_path for dataset_id={dataset_id} in catalog.")
        raw_file = Path(raw_path)
        if not raw_file.is_absolute():
            raw_file = (Path(".") / raw_file).resolve()
        if not raw_file.exists():
            raise FileNotFoundError(f"Raw dataset file not found: {raw_file}")

        ensure_empty_dir(unpack_dir)
        processed = unpack_dir / "processed"
        processed.mkdir(parents=True, exist_ok=True)

        if dataset_id == "oulad_v1":
            build_oulad_processed_from_zip(raw_file, unpack_dir)
            return

        if dataset_id == "assistments_2009_2010_v1":
            build_assistments_processed_from_csv(raw_file, unpack_dir)
            return

        raise ValueError(f"Unknown local_process dataset_id: {dataset_id}")

    raise ValueError(f"Unsupported snapshot mode: {mode}")
