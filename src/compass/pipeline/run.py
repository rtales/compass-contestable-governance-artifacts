from __future__ import annotations

from pathlib import Path
import json
from datetime import datetime, timezone

import yaml
import numpy as np

from compass.utils.seeds import set_global_seed
from compass.utils.env import collect_env_info
from compass.utils.hashing import sha256_bytes
from compass.data.validation import validate_processed_dataset
from compass.data.io import load_processed
from compass.models.registry import build_model
from compass.policy.decision import apply_topk_with_abstain
from compass.metrics.utility import utility_at_k, coverage_rate, abstain_rate
from compass.metrics.fairness import delta_eopp_at_k
from compass.metrics.contestability import ContestabilityScorecard
from compass.artifacts.packets import emit_decision_packets
from compass.reporting.decision_brief import write_decision_brief_md, try_write_decision_brief_pdf
from compass.reporting.bundle import build_paper_bundle


def _git_sha() -> str:
    # Offline execution: do not invoke git commands.
    return "LOCAL"


def run_recipe(recipe_path: Path) -> Path:
    recipe = yaml.safe_load(recipe_path.read_text(encoding="utf-8"))
    seed = int(recipe.get("seed", 42))
    set_global_seed(seed)

    dataset = recipe["dataset"]
    dataset_id = dataset["id"]
    dataset_dir = Path(dataset["local_path"]).parent  # .../data/<id>
    processed_dir = Path(dataset["local_path"])

    # Validate dataset contract
    report = validate_processed_dataset(dataset_dir)
    if not report.ok:
        raise RuntimeError(f"Dataset validation failed: {report.to_text()}")

    X, y, s = load_processed(processed_dir)

    # Split (deterministic): 80/20
    n = X.shape[0]
    idx = np.arange(n)
    rng = np.random.default_rng(seed)
    rng.shuffle(idx)
    split = int(0.8 * n)
    tr, te = idx[:split], idx[split:]

    Xtr, ytr = X[tr], y[tr]
    Xte, yte = X[te], y[te]
    ste = s[te]

    # Train model
    model_cfg = recipe.get("model", {"type": "numpy_linear", "params": {"l2": 1e-3}})
    model = build_model(model_cfg["type"], model_cfg.get("params", {}))
    model.fit(Xtr, ytr)
    scores = model.predict_proba(Xte)

    # Policy apply
    pol = recipe.get("policy", {})
    k = int(pol.get("topk", {}).get("k", 100))
    abst_cfg = pol.get("abstain", {})
    gamma = abst_cfg.get("gamma_entropy") if abst_cfg.get("enabled", True) else None

    dec = apply_topk_with_abstain(scores, k=k, gamma_entropy=gamma)
    selected = dec["selected"]
    abstain = dec["abstain"]
    entropy = dec["entropy"]

    # Metrics
    util = utility_at_k(yte, selected)
    cov = coverage_rate(abstain)
    abst = abstain_rate(abstain)
    deopp = delta_eopp_at_k(yte, selected, ste)

    # ECL check (simple constraints)
    ecl = pol.get("ecl", {})
    issues = []
    if ecl.get("enabled", False):
        c = ecl.get("constraints", {})
        max_deopp = float(c.get("max_delta_eopp_at_k", 1.0))
        min_cov = float(c.get("min_coverage", 0.0))
        if abs(deopp) > max_deopp:
            issues.append(f"ECL violation: |ΔEOpp@K|={abs(deopp):.4f} > {max_deopp}")
        if cov < min_cov:
            issues.append(f"ECL violation: coverage={cov:.4f} < {min_cov}")

    # Output directory (stable run id)
    gitsha = _git_sha()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{recipe.get('recipe_id','run')}_{dataset_id}_seed{seed}_{ts}_{gitsha[:7]}"
    out_root = Path(recipe.get("outputs", {}).get("root", "outputs"))
    run_dir = out_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Run metadata
    policy_yaml = yaml.safe_dump(pol, sort_keys=True)
    policy_hash = sha256_bytes(policy_yaml.encode("utf-8"))
    dataset_manifest_hash = sha256_bytes((dataset_dir / "manifest.json").read_bytes())
    model_hash = sha256_bytes(json.dumps(model_cfg, sort_keys=True).encode("utf-8"))

    env = collect_env_info().to_dict()
    meta = {
        "run_id": run_id,
        "recipe_path": str(recipe_path),
        "recipe_hash": sha256_bytes(recipe_path.read_bytes()),
        "git_sha": gitsha,
        "dataset_id": dataset_id,
        "dataset_dir": str(dataset_dir),
        "dataset_manifest_hash": dataset_manifest_hash,
        "policy_hash": policy_hash,
        "model_hash": model_hash,
        "seed": seed,
        "created_utc": ts,
        "env": env,
    }
    (run_dir / "run_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # Decision packets
    if recipe.get("outputs", {}).get("decision_packets", True):
        packets_dir = run_dir / "artifacts"
        emit_decision_packets(
            packets_dir, scores, selected, abstain, entropy, yte, ste, meta
        )

    # Contestability scorecard (minimal)
    scorecard = ContestabilityScorecard(
        replayable=True,
        has_policy_hash=True,
        has_dataset_manifest=True,
        packet_complete=True,
    ).to_dict()

    metrics = {
        "utility_at_k": util,
        "coverage": cov,
        "abstain_rate": abst,
        "delta_eopp_at_k": deopp,
        "ecl_issues": issues,
        "contestability_scorecard": scorecard,
    }
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # Decision brief
    brief = {
        "identity": {
            "run_id": run_id,
            "git_sha": gitsha,
            "dataset_id": dataset_id,
            "seed": seed,
            "recipe": str(recipe_path),
            "policy_hash": policy_hash,
            "dataset_manifest_hash": dataset_manifest_hash,
        },
        "metrics": {
            "utility_at_k": round(util, 6),
            "coverage": round(cov, 6),
            "abstain_rate": round(abst, 6),
            "delta_eopp_at_k": round(deopp, 6),
            "contestability_score": scorecard["score"],
            "contestability_max": scorecard["max_score"],
        },
        "policy_yaml": policy_yaml,
        "notes": [
            "This brief is auto-generated for decision support and auditability.",
            "ECL constraints are checked deterministically; infeasibility/violations are reported as issues.",
            "Metrics are computed on a deterministic 80/20 shuffled split.",
        ] + (issues if issues else []),
    }

    reports_dir = run_dir / "reports"
    md_path = write_decision_brief_md(reports_dir, brief)
    if recipe.get("outputs", {}).get("decision_brief", True):
        pdf_path = try_write_decision_brief_pdf(reports_dir, brief)
        # pdf_path may be None; markdown remains available

    # Bundle
    if recipe.get("outputs", {}).get("bundle_zip", True):
        template = Path("paper_template")
        zip_path = build_paper_bundle(run_dir, template)

    return run_dir
