from siem.wrfchemi import create_date_s19
import numpy as np

def test_create_date_s19_default() -> None:
    dates = create_date_s19("2023-09-01_00:00:00")
    assert len(dates) == 24
    assert len(dates[0]) == 19
    assert isinstance(dates, np.ndarray)
    assert isinstance(dates[0], np.bytes_)

