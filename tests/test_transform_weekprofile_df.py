from siem.temporal import transform_week_profile_df
import pandas as pd


def test_transform_week_profile_df() -> None:
    profile = [0.3, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1]
    week = transform_week_profile_df(profile)

    assert isinstance(week, pd.DataFrame)
    assert len(week) == len(profile)
    assert week.frac.sum() - 1.0 < 1.e-10

