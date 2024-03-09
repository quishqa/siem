from siem.cmaq import create_hour_matrix
import numpy  as np

def test_create_hour_matrix() -> None:
    date = 2018182
    hour_0 = create_hour_matrix(date, 0, 124)

    assert isinstance(hour_0, np.ndarray)
    assert hour_0.shape == (124, 2)


def test_create_hour_matrix_23h() -> None:
    date = 2018182
    hour_23 = create_hour_matrix(date, 23, 124)

    assert hour_23[0, 1] == 230000
    assert hour_23.dtype == np.dtype("int32")
