from __future__ import annotations

from pathlib import Path
import json
import pickle
import subprocess
from datetime import datetime, timezone

import yaml
import numpy as np

from compass.utils.seeds import set_global_seed
from compass.utils.env import collect_env_info
from compass.utils.hashing import sha256_bytes
from compass.data.validation import validate_processed_dataset
from compass.data.io import load_processed
from compass.models.registry import build_model
from compass.policy.decision import apply_policy
from compass.policy.governance import audit_decisions, assess_constraints, canonical_bytes, digest, evaluate_policy_candidates
from compass.artifacts.validation import verify_run
from compass.artifacts.packets import emit_decision_packets
from compass.reporting.decision_brief import write_decision_brief_md, try_write_decision_brief_pdf
from compass.reporting.bundle import build_paper_bundle


def _git_sha() -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(Path(__file__).resolve().parents[3]), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


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
    pol.setdefault("schema_version", "2.0")
    pol.setdefault("mode", "allocation")
    pol.setdefault("descending", True)
    pol.setdefault("abstain", {}).setdefault("unit", "bits")
    pol["abstain"].setdefault("scope", "global")
    case_ids = [f"{dataset_id}:row:{int(i):012d}" for i in te]
    k = int(pol.get("topk", {}).get("k", 100))
    abst_cfg = pol.get("abstain", {})
    gamma = abst_cfg.get("gamma_entropy") if abst_cfg.get("enabled", True) else None

    selection_report = evaluate_policy_candidates(scores, yte, ste, pol, case_ids)
    if pol.get("mas", {}).get("enabled", True) and selection_report["selected"] is not None:
        pol = selection_report["selected"]["policy"]
    dec = apply_policy(scores, pol, case_ids)
    selected = dec["selected"]
    abstain = dec["abstain"]
    entropy = dec["entropy"]

    # Retrospective audit, separate from authorization of any deployment output.
    audit = audit_decisions(yte, ste, dec["decision"], dec["eligible"])
    constraints = pol.get("ecl", {}).get("constraints", {}) if pol.get("ecl", {}).get("enabled", False) else {}
    ecl_result = assess_constraints(audit, constraints)
    issues = ecl_result["violations"]
    util, cov, abst, deopp = (audit[key] for key in ["utility_at_k", "coverage", "abstain_rate", "delta_eopp_at_k"])

    # Output directory (stable run id)
    gitsha = _git_sha()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_id = f"{recipe.get('recipe_id','run')}_{dataset_id}_seed{seed}_{ts}_{(gitsha or 'snapshot')[:7]}"
    out_root = Path(recipe.get("outputs", {}).get("root", "outputs"))
    run_dir = out_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "selection_report.json").write_bytes(canonical_bytes(selection_report))

    # Run metadata
    policy_yaml = yaml.safe_dump(pol, sort_keys=True)
    policy_hash = digest(pol)
    (run_dir / "policy.json").write_bytes(canonical_bytes(pol))
    (run_dir / "dataset_manifest.json").write_bytes((dataset_dir / "manifest.json").read_bytes())
    model_bytes = pickle.dumps(model, protocol=5)
    (run_dir / "model.pkl").write_bytes(model_bytes)
    dataset_manifest_hash = sha256_bytes((dataset_dir / "manifest.json").read_bytes())
    model_hash = sha256_bytes(model_bytes)
    source_root = Path(__file__).resolve().parents[1]
    source_files = {str(f.relative_to(source_root)): sha256_bytes(f.read_bytes()) for f in sorted(source_root.rglob("*.py"))}

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
        "model_config_hash": digest(model_cfg),
        "source_files": source_files,
        "source_tree_hash": digest(source_files),
        "case_ids": case_ids,
        "schema_version": "2.0",
        "entropy_unit": "bits",
        "execution_scope": "retrospective_candidate_evaluation",
        "task": recipe.get("task", {}),
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

    scorecard = verify_run(run_dir)
    metrics = {**audit, "ecl_issues": issues, "ecl": ecl_result,
               "contestability_scorecard": scorecard}
    if not scorecard["replayable"]:
        ecl_result = {"status": "insufficient_evidence", "deployment_authorized": False,
                      "violations": [*issues, "artifact_validation_failed"]}
        metrics["ecl"] = ecl_result
    # Packets remain candidate evidence even if the export gate is closed.
    (run_dir / "deployment_gate.json").write_bytes(canonical_bytes(ecl_result))
    if ecl_result["deployment_authorized"]:
        exported = [{"case_id": case_id, "decision": str(state)}
                    for case_id, state in zip(case_ids, dec["decision"])]
        (run_dir / "authorized_decisions.json").write_bytes(canonical_bytes(exported))
    else:
        (run_dir / "review_required.json").write_bytes(canonical_bytes({
            "case_ids": case_ids, "reasons": ecl_result["violations"],
            "delivery_status": "not_connected_to_human_queue"}))
    (run_dir / "metrics.json").write_bytes(canonical_bytes(metrics))

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
            "utility_at_k": round(util, 6) if util is not None else None,
            "coverage": round(cov, 6),
            "abstain_rate": round(abst, 6),
            "delta_eopp_at_k": round(deopp, 6) if deopp is not None else None,
            "contestability_score": scorecard["score"],
            "contestability_max": scorecard["max_score"],
        },
        "policy_yaml": policy_yaml,
        "notes": [
            "This brief is auto-generated for decision support and auditability.",
            "Candidate metrics are retrospective. Consult deployment_gate.json before any operational use.",
            "No human queue is connected; review_required.json records a need, not a delivered review.",
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
