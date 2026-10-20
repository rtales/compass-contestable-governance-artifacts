import json
import shutil
from pathlib import Path
import numpy as np
import pytest
from compass.policy.decision import binary_entropy, apply_topk_with_abstain
from compass.policy.governance import audit_decisions, assess_constraints, select_candidate, evaluate_policy_candidates
from compass.artifacts.validation import verify_run


def test_units_extremes_and_threshold_boundary():
    h = binary_entropy([0, .5, 1])
    assert h[1] == 1 and np.isfinite(h).all()
    assert apply_topk_with_abstain([.5], 1, 1)["selected"].tolist() == [True]
    assert apply_topk_with_abstain([.5], 1, .999)["abstain"].tolist() == [True]
    for p in [[float("nan")], [-.1], [1.1]]:
        with pytest.raises(ValueError): binary_entropy(p)
    with pytest.raises(ValueError): apply_topk_with_abstain([.8], 1, .6, entropy_unit="nats")


def test_capacity_modes_and_stable_case_ids():
    p = [.9, .9, .5, .1]
    ids = ["b", "a", "c", "d"]
    dec = apply_topk_with_abstain(p, 1, .6, case_ids=ids)
    assert dec["decision"].tolist() == ["reject", "select", "abstain", "reject"]
    perm = [3, 2, 0, 1]
    other = apply_topk_with_abstain(np.array(p)[perm], 1, .6, case_ids=np.array(ids)[perm])
    assert dict(zip(ids, dec["decision"])) == dict(zip(other["case_ids"], other["decision"]))
    assert apply_topk_with_abstain(p, 0, 1)["selected"].sum() == 0
    assert apply_topk_with_abstain(p, 100, .6)["selected"].sum() == 3
    screening = apply_topk_with_abstain(p, 1, .6, case_ids=ids, mode="screening")
    assert (screening["decision"] != "abstain").sum() == 1
    assert not apply_topk_with_abstain(p, 1, .6, abstain_scope="topk")["abstain"].any()
    with pytest.raises(ValueError): apply_topk_with_abstain(p, -1, .6)
    with pytest.raises(ValueError): apply_topk_with_abstain(p, 1, .6, case_ids=["a"]*4)


def test_metrics_denominators_and_insufficient_evidence():
    m = audit_decisions([1, 0, 1, 0], [0, 0, 1, 1], ["select", "reject", "abstain", "reject"])
    assert m["coverage"] == .75 and m["selection_rate"] == .25
    assert m["delta_eopp_at_k"] == -1
    missing = audit_decisions([0, 0, 1, 0], [0, 0, 1, 1], ["reject"]*4)
    assert missing["utility_at_k"] is None
    assert assess_constraints(missing, {"max_delta_eopp_at_k": .05})["status"] == "insufficient_evidence"
    assert audit_decisions(None, None, ["select"])["utility_at_k"] is None


def candidate(id, u, f, c):
    return {"candidate_id": id, "utility_at_k": u, "abs_delta_eopp_at_k": f,
            "coverage": c, "abstain_rate": 1-c}


def test_pareto_profile_tolerance_empty_and_permutation():
    cs = [candidate("dominated", .4, .04, .5), candidate("b", .8, .01, .8),
          candidate("a", .8, .01, .8), candidate("utility", .9, .03, .8)]
    constraints = {"max_delta_eopp_at_k": .05, "min_coverage": .5}
    result = select_candidate(cs, constraints)
    assert result["selected"]["candidate_id"] == "a"
    assert "dominated" not in result["pareto_candidate_ids"]
    assert select_candidate(cs[::-1], constraints)["selected"] == result["selected"]
    assert select_candidate(cs, constraints, ["max_utility"])["selected"]["candidate_id"] == "utility"
    assert select_candidate(cs, constraints, tolerances={"min_abs_delta_eopp": .03})["selected"]["candidate_id"] == "utility"
    assert select_candidate(cs, {"min_coverage": 1})["selected"] is None
    assert select_candidate([], constraints)["status"] == "infeasible"


def test_real_policy_grid_and_case_order_have_same_selection():
    scores=np.array([.99,.99,.8,.5,.2,.01]); y=np.array([1,1,1,0,0,0]); groups=np.array([0,1,0,1,0,1])
    ids=np.array(["b","a","c","d","e","f"])
    policy={"topk":{"k":1},"abstain":{"enabled":True,"gamma_entropy":.1},
            "ecl":{"enabled":True,"constraints":{"max_delta_eopp_at_k":1,"min_coverage":0}},
            "mas":{"grid":{"k":[1,2],"gamma_entropy":[.1,1]}}}
    a=evaluate_policy_candidates(scores,y,groups,policy,ids)
    b=evaluate_policy_candidates(scores[::-1],y[::-1],groups[::-1],policy,ids[::-1])
    assert a["n_candidates"]==4
    assert a["selected"]["candidate_id"]==b["selected"]["candidate_id"]


def test_oulad_target_and_sensitive_feature_separation(tmp_path):
    import zipfile
    import pandas as pd
    from compass.data.oulad import build_oulad_processed_from_zip
    frame=pd.DataFrame({"code_module":["A"]*4,"code_presentation":["X"]*4,
        "region":["R"]*4,"highest_education":["H"]*4,"imd_band":["0-10%"]*4,
        "age_band":["0-35"]*4,"disability":["N"]*4,"num_of_prev_attempts":[0]*4,
        "studied_credits":[60]*4,"gender":["F","M","F","M"],
        "final_result":["Pass","Distinction","Fail","Withdrawn"]})
    raw=tmp_path/"oulad.zip"
    with zipfile.ZipFile(raw,"w") as z:z.writestr("studentInfo.csv",frame.to_csv(index=False))
    folder=tmp_path/"processed_dataset"
    build_oulad_processed_from_zip(raw,folder)
    assert np.load(folder/"processed/y.npy").tolist()==[1,1,0,0]
    names=json.loads((folder/"schema.json").read_text())["feature_names"]
    assert not any(name.startswith(("gender", "final_result")) for name in names)


def test_runner_fail_closed_and_evidence_tampering(tmp_path, monkeypatch):
    import yaml
    from compass.pipeline.run import run_recipe
    from compass.snapshots.fetch import fetch_snapshot
    repo = Path(__file__).resolve().parents[1]
    for folder in ["configs", "snapshots", "paper_template"]:
        shutil.copytree(repo/folder, tmp_path/folder)
    monkeypatch.chdir(tmp_path)
    fetch_snapshot("synthetic_v1", tmp_path/"snapshots/catalog.yaml")
    recipe = yaml.safe_load((tmp_path/"configs/recipes/synthetic.yaml").read_text())
    recipe["policy"]["ecl"]["constraints"]["min_coverage"] = 1
    recipe["outputs"]["bundle_zip"] = False
    recipe["outputs"]["decision_brief"] = False
    file = tmp_path/"recipe.yaml"
    file.write_text(yaml.safe_dump(recipe))
    out = run_recipe(file)
    assert verify_run(out)["score"] == 4
    assert not json.loads((out/"deployment_gate.json").read_text())["deployment_authorized"]
    assert not (out/"authorized_decisions.json").exists()
    assert (out/"review_required.json").exists()
    # A feasible run exports only after evidence verification; no human delivery is implied.
    recipe["policy"]["abstain"]["gamma_entropy"] = 1
    recipe["policy"]["ecl"]["constraints"] = {"min_coverage":0, "max_delta_eopp_at_k":1}
    file.write_text(yaml.safe_dump(recipe))
    good = run_recipe(file)
    assert verify_run(good)["score"] == 4
    assert json.loads((good/"deployment_gate.json").read_text())["deployment_authorized"]
    assert (good/"authorized_decisions.json").exists()
    model=good/"model.pkl"
    model.write_bytes(model.read_bytes()+b"changed")
    assert not verify_run(good)["packet_complete"]
    packet = out/"artifacts/decision_packets.jsonl"
    lines = packet.read_text().splitlines()
    row = json.loads(lines[0]); row["score"] = 0.5
    lines[0] = json.dumps(row); packet.write_text("\n".join(lines)+"\n")
    assert not verify_run(out)["replayable"]
    (out/"policy.json").unlink()
    assert verify_run(out)["score"] < 4
