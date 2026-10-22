import copy
import json
import numpy as np
import pytest
from compass.policy.validation import partition_case_ids, freeze_from_validation, evaluate_frozen


def test_partition_is_disjoint_complete_and_order_invariant():
    ids = [f"student:{i}" for i in range(11)]
    a = partition_case_ids(ids, "sample")
    assert a == partition_case_ids(ids[::-1], "sample")
    assert len(a["validation"]) == 5 and len(a["test"]) == 6
    assert not set(a["validation"]) & set(a["test"])
    assert set(a["validation"] + a["test"]) == set(ids)
    with pytest.raises(ValueError): partition_case_ids(["a", "a"], "sample")


def test_frozen_policy_is_not_retuned_on_test_labels_or_failure():
    p = [.99, .98, .1, .01]
    policy = {"topk": {"k": 2}, "abstain": {"enabled": True, "unit": "bits"},
              "ecl": {"enabled": True, "constraints": {"max_delta_eopp_at_k": 0, "min_coverage": .5}},
              "mas": {"grid": {"gamma_entropy": [.1, 1]}}}
    frozen = freeze_from_validation(p, [1, 1, 0, 0], [0, 1, 0, 1], list("abcd"), policy)
    before = json.dumps(frozen, sort_keys=True)
    assert frozen["policy"]["abstain"]["gamma_entropy"] == 1
    for labels in [[1, 1, 0, 0], [0, 1, 1, 0]]:
        report = evaluate_frozen(frozen, p, labels, [0, 1, 0, 1], list("efgh"))
        assert report["freeze_hash"] == frozen["freeze_hash"]
    assert report["status"] == "infeasible"
    assert json.dumps(frozen, sort_keys=True) == before
    changed = copy.deepcopy(frozen)
    changed["policy"]["topk"]["k"] = 3
    with pytest.raises(ValueError): evaluate_frozen(changed, p, [1, 1, 0, 0], [0, 1, 0, 1], list("efgh"))


def test_empty_validation_feasible_set_does_not_create_test_policy():
    policy = {"topk": {"k": 1}, "abstain": {"enabled": True},
              "mas": {"grid": {"gamma_entropy": [.1]}},
              "ecl": {"enabled": True, "constraints": {"min_coverage": 1}}}
    frozen = freeze_from_validation([.5, .5], [0, 1], [0, 1], ["a", "b"], policy)
    assert frozen["policy"] is None
    assert evaluate_frozen(frozen, [.9, .1], [1, 0], [0, 1], ["c", "d"])["status"] == "no_validation_policy"
