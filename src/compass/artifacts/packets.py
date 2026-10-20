from __future__ import annotations

from pathlib import Path
import json
import numpy as np

from compass.utils.hashing import sha256_bytes


def emit_decision_packets(out_dir: Path, scores: np.ndarray, selected: np.ndarray, abstain: np.ndarray,
                          entropy: np.ndarray, y_true: np.ndarray, sensitive: np.ndarray,
                          run_meta: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    packets_path = out_dir / "decision_packets.jsonl"

    policy_hash = run_meta.get("policy_hash", "")
    dataset_manifest_hash = run_meta.get("dataset_manifest_hash", "")
    model_hash = run_meta.get("model_hash", "")
    case_ids = run_meta.get("case_ids", list(range(len(scores))))

    with open(packets_path, "w", encoding="utf-8") as f:
        for i in range(scores.shape[0]):
            pkt = {
                "schema_version": "2.0",
                "case_id": case_ids[i],
                "entropy_unit": "bits",
                "entropy_epsilon": 1e-7,
                "replay_scope": "fixed_scores_topk",
                "score": float(scores[i]),
                "entropy": float(entropy[i]),
                "decision": "abstain" if bool(abstain[i]) else ("select" if bool(selected[i]) else "reject"),
                "y_true": int(y_true[i]),
                "sensitive": int(sensitive[i]),
                "policy_hash": policy_hash,
                "dataset_manifest_hash": dataset_manifest_hash,
                "model_hash": model_hash,
            }
            pkt_bytes = json.dumps(pkt, sort_keys=True).encode("utf-8")
            pkt["packet_hash"] = sha256_bytes(pkt_bytes)
            f.write(json.dumps(pkt) + "\n")
    return packets_path
