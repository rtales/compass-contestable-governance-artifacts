"""Empirical constraints, exact Pareto filtering and explicit MAS profiles."""
from __future__ import annotations
import hashlib
import json
import math
import numpy as np

CRITERIA = {"min_abs_delta_eopp": ("abs_delta_eopp_at_k", False),
            "max_utility": ("utility_at_k", True),
            "min_abstain_rate": ("abstain_rate", False)}
DEFAULT_ORDER = list(CRITERIA)


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def audit_decisions(y, groups, decision, eligible=None):
    decision = np.asarray(decision)
    n = len(decision)
    if n == 0 or not np.isin(decision, ["select", "reject", "abstain"]).all():
        raise ValueError("Nonempty sample with known decision states required.")
    selected = decision == "select"
    counts = {state: int((decision == state).sum()) for state in ["select", "reject", "abstain"]}
    result = {"n": n, "n_selected": counts["select"], "n_rejected": counts["reject"],
              "n_abstained": counts["abstain"], "coverage": 1 - counts["abstain"] / n,
              "selection_rate": counts["select"] / n, "abstain_rate": counts["abstain"] / n,
              "n_eligible": int(np.asarray(eligible).sum()) if eligible is not None else None,
              "utility_at_k": None, "delta_eopp_at_k": None, "abs_delta_eopp_at_k": None,
              "group_counts": {}, "fairness_status": "insufficient_evidence"}
    if y is None:
        return result
    y = np.asarray(y)
    if y.shape != (n,) or not np.isin(y, [0, 1]).all():
        raise ValueError("Binary retrospective labels must match sample length.")
    if selected.any():
        result["utility_at_k"] = float(y[selected].mean())
    if groups is None:
        return result
    groups = np.asarray(groups)
    if groups.shape != (n,):
        raise ValueError("Audit groups must match sample length.")
    tprs = []
    for g in sorted(np.unique(groups)):
        m = groups == g
        positives = m & (y == 1)
        denom = int(positives.sum())
        numerator = int((positives & selected).sum())
        result["group_counts"][str(g)] = {
            "n": int(m.sum()), "positive": denom, "positive_selected": numerator,
            **{state: int((m & (decision == state)).sum()) for state in counts},
            "tpr": numerator / denom if denom else None}
        tprs.append(numerator / denom if denom else None)
    if len(tprs) >= 2 and all(t is not None for t in tprs):
        result["fairness_status"] = "available"
        result["abs_delta_eopp_at_k"] = max(tprs) - min(tprs)
        result["delta_eopp_at_k"] = tprs[1] - tprs[0] if len(tprs) == 2 else None
    return result


def assess_constraints(metrics, constraints):
    violations = []
    insufficient = False
    cap = constraints.get("max_delta_eopp_at_k", constraints.get("max_abs_delta_eopp_at_k"))
    if cap is not None:
        value = metrics.get("abs_delta_eopp_at_k")
        if value is None or not math.isfinite(value):
            violations.append("fairness_not_estimable")
            insufficient = True
        elif value > cap:
            violations.append("fairness_cap")
    if metrics["coverage"] < constraints.get("min_coverage", 0):
        violations.append("coverage_floor")
    return {"status": "insufficient_evidence" if insufficient else "infeasible" if violations else "feasible",
            "violations": violations, "deployment_authorized": not violations}


def _objectives(c):
    values = [c.get("utility_at_k"), c.get("abs_delta_eopp_at_k"), c.get("abstain_rate")]
    if any(x is None or not math.isfinite(x) for x in values):
        raise ValueError("MAS requires finite estimable objectives.")
    return (values[0], -values[1], -values[2])


def pareto_front(candidates):
    objectives = [_objectives(c) for c in candidates]
    return [c for i, c in enumerate(candidates) if not any(
        all(a >= b for a, b in zip(other, objectives[i])) and
        any(a > b for a, b in zip(other, objectives[i]))
        for j, other in enumerate(objectives) if i != j)]


def select_candidate(candidates, constraints, order=None, tolerances=None):
    order = DEFAULT_ORDER if order is None else order
    if len(order) != len(set(order)) or any(k not in CRITERIA for k in order):
        raise ValueError("Unknown or repeated MAS criterion.")
    tolerances = {} if tolerances is None else tolerances
    if any(k not in CRITERIA or not math.isfinite(v) or v < 0 for k, v in tolerances.items()):
        raise ValueError("Tolerances must be finite, nonnegative and criterion-specific.")
    if len({c["candidate_id"] for c in candidates}) != len(candidates):
        raise ValueError("Candidate IDs must be unique.")
    feasible = [c for c in candidates if assess_constraints(c, constraints)["deployment_authorized"]
                and all(c.get(k) is not None and math.isfinite(c[k])
                        for k in ["utility_at_k", "abs_delta_eopp_at_k", "abstain_rate"])]
    front = pareto_front(feasible)
    remaining = front
    for key in order:
        if not remaining:
            break
        col, maximize = CRITERIA[key]
        best = (max if maximize else min)(c[col] for c in remaining)
        remaining = [c for c in remaining if abs(c[col] - best) <= tolerances.get(key, 0.0)]
    chosen = min(remaining, key=lambda c: c["candidate_id"]) if remaining else None
    return {"status": "feasible" if chosen else "infeasible", "selected": chosen,
            "n_candidates": len(candidates), "n_feasible": len(feasible), "n_pareto": len(front),
            "order": order, "tolerances": tolerances,
            "pareto_candidate_ids": sorted(c["candidate_id"] for c in front)}


def evaluate_policy_candidates(scores, y, groups, policy, case_ids):
    """Offline policy search on labelled evaluation data, not prospective validation."""
    from copy import deepcopy
    from compass.policy.decision import apply_policy
    search = policy.get("mas", {})
    grid = search.get("grid", {})
    ks = grid.get("k", [policy.get("topk", {}).get("k", 100)])
    gammas = grid.get("gamma_entropy", [policy.get("abstain", {}).get("gamma_entropy")])
    constraints = policy.get("ecl", {}).get("constraints", {}) if policy.get("ecl", {}).get("enabled", False) else {}
    candidates = []
    for k in ks:
        for gamma in gammas:
            p = deepcopy(policy)
            p.setdefault("topk", {})["k"] = k
            p.setdefault("abstain", {})["gamma_entropy"] = gamma
            dec = apply_policy(scores, p, case_ids)
            candidates.append({**audit_decisions(y, groups, dec["decision"], dec["eligible"]),
                               "candidate_id": digest(p), "policy": p})
    result = select_candidate(candidates, constraints, search.get("tie_breakers"), search.get("tolerances"))
    return {**result, "evaluation_scope": "retrospective_policy_search", "candidates": candidates}
