from siem.temporal import assign_factor_simulation_days
import pandas as pd


def test_assign_factor_simulation_days_more_than_a_week() -> None:
    start_day = "2024-02-04"
    end_day= "2024-03-11"
    
    sim_period = pd.date_range(start_day, end_day, freq="D")

    week_prof = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    factor_days = assign_factor_simulation_days(start_day, 
                                                end_day,
                                                week_prof)
    assert isinstance(factor_days, pd.Series)
    assert len(sim_period) == len(factor_days)


def test_assign_factor_simulation_days_less_than_a_week() -> None:
    start_day = "2024-02-04"
    end_day= "2024-03-07"

    sim_period = pd.date_range(start_day, end_day, freq="D")

    week_prof = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    factor_days = assign_factor_simulation_days(start_day, 
                                                end_day,
                                                week_prof)
    assert isinstance(factor_days, pd.Series)
    assert len(sim_period) == len(factor_days)
