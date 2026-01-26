import numpy as np
from compass.policy.decision import binary_entropy

def test_entropy_no_nan_at_edges_float32():
    p = np.array([0.0, 1.0, 0.5], dtype=np.float32)
    h = binary_entropy(p)
    assert np.isfinite(h).all()
    assert h[2] > h[0] and h[2] > h[1]
