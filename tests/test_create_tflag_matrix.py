from siem.cmaq import create_tflag_matrix
import numpy as np


def test_create_tflag_matrix() -> None:
    date = "2018-07-01"
    tflag_m = create_tflag_matrix(date, 124)

    assert isinstance(tflag_m, np.ndarray)
    assert tflag_m.shape == (25, 124, 2)
    assert tflag_m.dtype == np.dtype("int32")
    assert tflag_m[0, 0, 0] == 2018182
    assert tflag_m[-1, 0, 0] == 2018183
