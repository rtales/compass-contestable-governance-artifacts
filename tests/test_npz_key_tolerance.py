import numpy as np
from pathlib import Path
from compass.data.io import load_processed

def test_load_processed_npz_accepts_named_key(tmp_path: Path):
    processed = tmp_path / "processed"
    processed.mkdir()
    X = np.ones((5, 3), dtype=np.float32)
    y = np.zeros((5,), dtype=np.int64)
    s = np.zeros((5,), dtype=np.int64)
    # Save with named key (historical bug)
    np.savez_compressed(processed / "X.npz", X=X)
    np.save(processed / "y.npy", y)
    np.save(processed / "sensitive.npy", s)

    X2, y2, s2 = load_processed(processed)
    assert X2.shape == (5, 3)
    assert X2.dtype == np.float32
    assert y2.shape == (5,)
    assert s2.shape == (5,)
