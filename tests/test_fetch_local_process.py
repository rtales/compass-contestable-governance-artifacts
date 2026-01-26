from pathlib import Path
import shutil
import os
import pytest

from compass.snapshots.fetch import fetch_snapshot


@pytest.mark.parametrize("dataset_id,raw_name", [
    ("oulad_v1", "anonymisedData.zip"),
    ("assistments_2009_2010_v1", "skill_builder_data.csv"),
])
def test_fetch_local_process_skips_if_missing(tmp_path: Path, monkeypatch, dataset_id: str, raw_name: str):
    # This test does not require the real datasets in CI.
    wd = tmp_path / "wd"
    wd.mkdir()
    monkeypatch.chdir(wd)

    repo_root = Path(__file__).resolve().parents[1]
    shutil.copytree(repo_root / "snapshots", wd / "snapshots")

    # Ensure datasets dir exists but raw file missing
    (wd / "datasets").mkdir()
    with pytest.raises(FileNotFoundError):
        fetch_snapshot(dataset_id, wd / "snapshots" / "catalog.yaml")
