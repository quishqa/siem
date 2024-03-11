import xarray as xr
import numpy as np
import pandas as pd


def split_by_time(spatial_emiss: xr.DataArray,
                  temporal_profile: list) -> xr.DataArray:
    emiss_time = xr.concat(
            [spatial_emiss * time for time in temporal_profile],
            dim=pd.Index(np.arange(len(temporal_profile)),
                         name="Time")
            )
    return emiss_time


def transform_week_profile_df(weekday_profile: list[float]) -> pd.DataFrame:
    week = pd.DataFrame()
    week["day"] = np.arange(7)
    week["frac"] = np.array(weekday_profile)
    week.set_index("day", inplace=True)
    return week


def assign_factor_simulation_days(start: str, end: str,
                                  week_profile: str) -> pd.DataFrame:
    simulation_days = pd.date_range(start, end, freq="D")
    week_prof = transform_week_profile_df(week_profile)
    days_factor = week_prof.frac.loc[simulation_days.weekday].to_frame()
    days_factor["day"] = simulation_days.strftime("%Y-%m-%d")
    return days_factor


def split_by_weekday(emiss_day: xr.Dataset,
                     weekday_profile: list[float],
                     date_start: str,
                     date_end: str) -> xr.Dataset:
    days_factor = assign_factor_simulation_days(date_start, date_end,
                                                weekday_profile)
    days_emiss = {day: emiss_day * factor
                  for day, factor in enumerate(days_factor.frac)}
    days_emiss_all = xr.concat(days_emiss.values(), dim="Time")
    days_emiss_all["Time"] = np.arange(days_emiss_all.sizes["Time"])
    return days_emiss_all

