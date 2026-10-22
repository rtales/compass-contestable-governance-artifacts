import importlib.util
from pathlib import Path


def test_integrity_and_gate_detect_faults_replay_alone_cannot():
    file = Path(__file__).resolve().parents[1] / "scripts/verify_fault_contracts.py"
    spec = importlib.util.spec_from_file_location("fault_contracts", file)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    cases = {r["case"]: r for r in module.run_contracts()["cases"]}
    assert cases["unchanged"]["gate_authorizes"]
    for name in ["score_changed_without_rehash", "case_omitted", "wrong_model_bytes", "wrong_entropy_unit"]:
        assert cases[name]["replay_only_accepts"]
        assert not cases[name]["evidence_verifies"]
        assert not cases[name]["gate_authorizes"]
    assert not cases["policy_missing"]["replay_only_accepts"]
    assert cases["constraint_violation"]["evidence_verifies"]
    assert not cases["constraint_violation"]["gate_authorizes"]
