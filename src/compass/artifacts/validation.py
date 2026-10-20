"""Validate actual persisted evidence. Never loads executable model pickles."""
from pathlib import Path
import json
import hashlib
import numpy as np
from compass.policy.decision import apply_policy, ENTROPY_EPSILON
from compass.policy.governance import digest


def verify_run(run_dir):
    run_dir = Path(run_dir)
    checks = {"replayable": False, "has_policy_hash": False,
              "has_dataset_manifest": False, "packet_complete": False}
    errors = []
    try:
        meta = json.loads((run_dir / "run_metadata.json").read_text())
        policy = json.loads((run_dir / "policy.json").read_text())
        checks["has_policy_hash"] = digest(policy) == meta["policy_hash"]
        checks["has_dataset_manifest"] = hashlib.sha256(
            (run_dir / "dataset_manifest.json").read_bytes()).hexdigest() == meta["dataset_manifest_hash"]
        model_valid = hashlib.sha256((run_dir / "model.pkl").read_bytes()).hexdigest() == meta["model_hash"]
        rows = [json.loads(line) for line in (run_dir / "artifacts/decision_packets.jsonl").read_text().splitlines()]
        required = {"case_id", "score", "entropy", "decision", "policy_hash", "dataset_manifest_hash",
                    "model_hash", "packet_hash", "schema_version", "entropy_unit", "entropy_epsilon", "replay_scope"}
        complete = bool(rows)
        for row in rows:
            complete &= required <= row.keys()
            content = {k: v for k, v in row.items() if k != "packet_hash"}
            complete &= hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest() == row.get("packet_hash")
            complete &= all(row.get(key) == meta[key] for key in ["policy_hash", "dataset_manifest_hash", "model_hash"])
            complete &= row.get("schema_version") == "2.0" and row.get("entropy_unit") == "bits"
            complete &= row.get("entropy_epsilon") == ENTROPY_EPSILON
            complete &= row.get("replay_scope") == "fixed_scores_topk"
        checks["packet_complete"] = bool(complete and model_valid)
        dec = apply_policy([r["score"] for r in rows], policy, [r["case_id"] for r in rows])
        checks["replayable"] = bool(all(checks[k] for k in checks if k != "replayable") and
            np.array_equal(dec["decision"], [r["decision"] for r in rows]) and
            np.allclose(dec["entropy"], [r["entropy"] for r in rows], atol=1e-12, rtol=0))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    if not all(checks.values()) and not errors:
        errors.append("One or more persisted evidence checks failed.")
    return {**checks, "score": sum(checks.values()), "max_score": 4, "errors": errors}
