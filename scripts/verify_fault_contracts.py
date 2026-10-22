"""Executable synthetic fault contracts; not a participant baseline comparison."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import numpy as np
from compass.artifacts.packets import emit_decision_packets
from compass.artifacts.validation import verify_run
from compass.policy.decision import apply_policy, binary_entropy
from compass.policy.governance import canonical_bytes, digest, audit_decisions, assess_constraints


def create_fixture(folder, constraints=None, k=2):
    folder.mkdir(parents=True, exist_ok=True)
    scores = np.array([.99, .98, .1, .01])
    labels = np.array([1, 1, 0, 0]); groups = np.array([0, 1, 0, 1])
    policy = {"schema_version": "2.0", "mode": "allocation", "descending": True,
              "topk": {"k": k}, "abstain": {"enabled": True, "gamma_entropy": 1, "unit": "bits", "scope": "global"},
              "ecl": {"enabled": True, "constraints": constraints or {"max_delta_eopp_at_k": .05, "min_coverage": .5}}}
    manifest = b'{"fixture":"synthetic-fault-contract"}'
    model = b"Opaque synthetic fixture bytes; not an executable model"
    meta = {"schema_version": "2.0", "entropy_unit": "bits", "case_ids": ["a", "b", "c", "d"],
            "policy_hash": digest(policy), "dataset_manifest_hash": hashlib.sha256(manifest).hexdigest(),
            "model_hash": hashlib.sha256(model).hexdigest()}
    (folder / "policy.json").write_bytes(canonical_bytes(policy))
    (folder / "dataset_manifest.json").write_bytes(manifest)
    (folder / "model.pkl").write_bytes(model)
    (folder / "run_metadata.json").write_bytes(canonical_bytes(meta))
    dec = apply_policy(scores, policy, meta["case_ids"])
    emit_decision_packets(folder / "artifacts", scores, dec["selected"], dec["abstain"], dec["entropy"], labels, groups, meta)


def replay_only(folder):
    try:
        policy = json.loads((folder / "policy.json").read_text())
        rows = [json.loads(line) for line in (folder / "artifacts/decision_packets.jsonl").read_text().splitlines()]
        dec = apply_policy([r["score"] for r in rows], policy, [r["case_id"] for r in rows])
        return bool(np.array_equal(dec["decision"], [r["decision"] for r in rows]))
    except (OSError, ValueError, KeyError):
        return False


def verify_and_gate(folder):
    verification = verify_run(folder)
    if not verification["replayable"]:
        return verification, False
    policy = json.loads((folder / "policy.json").read_text())
    rows = [json.loads(line) for line in (folder / "artifacts/decision_packets.jsonl").read_text().splitlines()]
    dec = apply_policy([r["score"] for r in rows], policy, [r["case_id"] for r in rows])
    metrics = audit_decisions([r["y_true"] for r in rows], [r["sensitive"] for r in rows], dec["decision"], dec["eligible"])
    return verification, assess_constraints(metrics, policy["ecl"]["constraints"])["deployment_authorized"]


def run_contracts():
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "base"; create_fixture(base)
        cases = ["unchanged", "score_changed_without_rehash", "case_omitted", "wrong_model_bytes",
                 "wrong_entropy_unit", "policy_missing", "constraint_violation"]
        for name in cases:
            folder = Path(tmp) / name; shutil.copytree(base, folder)
            path = folder / "artifacts/decision_packets.jsonl"
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            if name == "score_changed_without_rehash":
                rows[-1]["score"] = .02
                rows[-1]["entropy"] = float(binary_entropy([.02])[0])
            elif name == "case_omitted": rows.pop()
            elif name == "wrong_model_bytes": (folder / "model.pkl").write_bytes(b"changed")
            elif name == "wrong_entropy_unit": rows[-1]["entropy_unit"] = "nats"
            elif name == "policy_missing": (folder / "policy.json").unlink()
            elif name == "constraint_violation":
                create_fixture(folder, k=1)
                rows = None
            if rows is not None: path.write_text("".join(json.dumps(r) + "\n" for r in rows))
            verification, authorized = verify_and_gate(folder)
            results.append({"case": name, "logs_cards_contract": "retains information; no automated rejection check",
                            "replay_only_accepts": replay_only(folder), "evidence_verifies": verification["replayable"],
                            "gate_authorizes": authorized,
                            "verification_errors": [e.split(": ", 1)[0] if e.startswith("FileNotFoundError:") else e
                                                    for e in verification["errors"]]})
    return {"scope": "synthetic contract comparison, not efficacy or comparison with all audit systems",
            "cases": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(run_contracts(), indent=2) + "\n")
