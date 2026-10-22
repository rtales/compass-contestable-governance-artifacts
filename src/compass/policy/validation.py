"""Separate labelled policy selection from frozen-policy evaluation on fixed scores.

This does not split or refit a predictor, and is not prospective validation.
"""
from copy import deepcopy
import hashlib
import numpy as np
from compass.policy.decision import apply_policy
from compass.policy.governance import audit_decisions, assess_constraints, digest, evaluate_policy_candidates


def partition_case_ids(case_ids, dataset, salt="compass-round2-v1"):
    ids = [str(i) for i in case_ids]
    if len(ids) < 2 or len(ids) != len(set(ids)):
        raise ValueError("At least two unique case IDs required.")
    ordered = sorted(ids, key=lambda i: (hashlib.sha256(f"{salt}|{dataset}|{i}".encode()).hexdigest(), i))
    half = len(ordered) // 2
    return {"validation": ordered[:half], "test": ordered[half:]}


def freeze_from_validation(scores, labels, groups, case_ids, policy):
    """Accepts only the selection sample. No test inputs belong in this call."""
    result = evaluate_policy_candidates(scores, labels, groups, deepcopy(policy), case_ids)
    selected = result["selected"]
    content = {"scope": "fixed_score_policy_validation", "validation_case_ids_hash": digest(sorted(map(str, case_ids))),
               "selection_report": result, "policy": deepcopy(selected["policy"]) if selected else None}
    return {**content, "freeze_hash": digest(content)}


def evaluate_frozen(frozen, scores, labels, groups, case_ids):
    """Apply one frozen policy. Never searches or relaxes constraints on test."""
    content = {k: v for k, v in frozen.items() if k != "freeze_hash"}
    if digest(content) != frozen.get("freeze_hash"):
        raise ValueError("Frozen selection was changed.")
    policy = frozen["policy"]
    if policy is None:
        return {"status": "no_validation_policy", "metrics": None, "freeze_hash": frozen["freeze_hash"]}
    dec = apply_policy(scores, policy, case_ids)
    audit = audit_decisions(labels, groups, dec["decision"], dec["eligible"])
    constraints = policy.get("ecl", {}).get("constraints", {}) if policy.get("ecl", {}).get("enabled", False) else {}
    assessment = assess_constraints(audit, constraints)
    return {"status": assessment["status"], "constraint_violations": assessment["violations"],
            "metrics": audit, "freeze_hash": frozen["freeze_hash"],
            "test_case_ids_hash": digest(sorted(map(str, case_ids))),
            "scope": "retrospective_fixed_score_test_only; not deployment authorization"}
