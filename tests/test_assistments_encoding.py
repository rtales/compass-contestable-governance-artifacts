from pathlib import Path
import pytest

def test_assistments_csv_robust_encoding(tmp_path: Path):
    pd = pytest.importorskip("pandas")
    from compass.data.assistments import build_assistments_processed_from_csv

    # Minimal required columns with a non-utf8 character in a string field
    rows = [
        "correct,school_id,attempt_count,ms_first_response,hint_count,hint_total,overlap_time,opportunity,original,tutor_mode,answer_type,type,skill_id",
        "1,10,1,1000,0,0,0,1,1,tutor,choice,Algebra,123",
        "0,11,2,2000,1,1,10,2,0,tutór,string,Geometry,124",  # ó forces non-ascii
    ]
    raw = tmp_path / "sb.csv"
    # write cp1252 (common in older datasets)
    raw.write_bytes(("\n".join(rows)).encode("cp1252", errors="replace"))

    out_dir = tmp_path / "out"
    build_assistments_processed_from_csv(raw, out_dir)

    processed = out_dir / "processed"
    assert (processed / "X.npz").exists()
    assert (processed / "y.npy").exists()
    assert (processed / "sensitive.npy").exists()
