from pathlib import Path
import shutil

from compass.snapshots.fetch import fetch_snapshot
from compass.pipeline.run import run_recipe


def test_run_synthetic_recipe(tmp_path: Path, monkeypatch):
    # run in an isolated working dir
    wd = tmp_path / "wd"
    wd.mkdir()
    monkeypatch.chdir(wd)

    # copy required repo files for a minimal run
    repo_root = Path(__file__).resolve().parents[1]
    shutil.copytree(repo_root / "snapshots", wd / "snapshots")
    shutil.copytree(repo_root / "configs", wd / "configs")
    shutil.copytree(repo_root / "paper_template", wd / "paper_template")

    # fetch synthetic (local generate)
    fetch_snapshot("synthetic_v1", wd / "snapshots" / "catalog.yaml")

    run_dir = run_recipe(wd / "configs" / "recipes" / "synthetic.yaml")
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "reports" / "decision_brief.md").exists()
