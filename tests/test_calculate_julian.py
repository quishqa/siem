from siem.cmaq import calculate_julian
import pandas as pd


def test_calculate_julian() -> None:
    date = "2018-07-01"
    date_dt = pd.to_datetime(date)
    date_julian = calculate_julian(date_dt)

    assert isinstance(date_julian, int)
    assert date_julian == 2018182
