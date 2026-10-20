"""Version 2 decision semantics shared by scoring and policy replay."""
from __future__ import annotations
import numpy as np

ENTROPY_UNIT = "bits"
ENTROPY_EPSILON = 1e-7


def binary_entropy(p, eps=None):
    p = np.asarray(p, dtype=np.float64)
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Scores must be finite probabilities in [0, 1].")
    epsilon = ENTROPY_EPSILON if eps is None else float(eps)
    if not 0 < epsilon < 0.5:
        raise ValueError("Entropy epsilon must lie in (0, .5).")
    q = np.clip(p, epsilon, 1 - epsilon)
    return -(q * np.log2(q) + (1 - q) * np.log2(1 - q))


def apply_topk_with_abstain(scores, k, gamma_entropy, *, case_ids=None,
                            mode="allocation", descending=True,
                            abstain_scope="global", entropy_unit="bits"):
    scores = np.asarray(scores, dtype=np.float64)
    if scores.ndim != 1:
        raise ValueError("Scores must be one-dimensional.")
    n = len(scores)
    if isinstance(k, bool) or int(k) != k or k < 0:
        raise ValueError("K must be a nonnegative integer capacity.")
    if entropy_unit != ENTROPY_UNIT:
        raise ValueError("Only bits accepted; convert units explicitly.")
    if gamma_entropy is not None and (not np.isfinite(gamma_entropy) or not 0 <= gamma_entropy <= 1):
        raise ValueError("Threshold must lie in [0, 1] bits.")
    if mode not in {"allocation", "screening"} or abstain_scope not in {"global", "topk"}:
        raise ValueError("Unknown decision taxonomy.")
    ids = np.asarray([str(i) for i in range(n)] if case_ids is None else case_ids).astype(str)
    if len(ids) != n or len(set(ids)) != n:
        raise ValueError("Unique case IDs required.")
    ent = binary_entropy(scores)
    uncertain = np.zeros(n, dtype=bool) if gamma_entropy is None else ent > gamma_entropy
    ranked = np.lexsort((ids, -scores if descending else scores))
    selected = np.zeros(n, dtype=bool)
    if abstain_scope == "global":
        selected[ranked[~uncertain[ranked]][:int(k)]] = True
        abstain = uncertain.copy()
    else:
        nominees = ranked[:int(k)]
        selected[nominees[~uncertain[nominees]]] = True
        abstain = np.zeros(n, dtype=bool)
        abstain[nominees[uncertain[nominees]]] = True
    if mode == "screening":
        abstain = ~selected
    decision = np.where(abstain, "abstain", np.where(selected, "select", "reject"))
    return {"selected": selected, "abstain": abstain, "entropy": ent,
            "decision": decision, "case_ids": ids, "eligible": ~uncertain}


def apply_policy(scores, policy, case_ids=None):
    abst = policy.get("abstain", {})
    return apply_topk_with_abstain(
        scores, policy.get("topk", {}).get("k", 100),
        abst.get("gamma_entropy") if abst.get("enabled", True) else None,
        case_ids=case_ids, mode=policy.get("mode", "allocation"),
        descending=policy.get("descending", True),
        abstain_scope=abst.get("scope", "global"), entropy_unit=abst.get("unit", "bits"))
