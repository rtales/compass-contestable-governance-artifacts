import numpy as np
from compass.policy.decision import binary_entropy


def test_entropy_bounds():
    p = np.array([0.0, 0.5, 1.0], dtype=np.float32)
    h = binary_entropy(p)
    assert h.shape == (3,)
    assert h[1] > h[0] and h[1] > h[2]
