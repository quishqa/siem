# siem/temporal.py
"""
Functions for emission temporal disaggregations.

This modules contains functions to temporal distribute emissions by hour of the day
and by day of week.

It contains the following functions:
    - `split_by_time(spatial_emiss, temporal_emiss)` - Returns one pollutant emission by hour.
    - `split_by_time_from(spatial_sources, temporal_profiles)` - Returns all pollutants emissions by hour.
    - `transform_week_profile_df(weekday_profile)` - Returns a dataframe from a list of weekday weights.
    - `assign_factor_simulation_days(date_start, date_end, week_profile, is_cmaq)` - Returns simulation days table with the correct weekday weight according to the day.
    - `split_by_weekday(emiss_day, weekday_profile, date_start, date_end)` - Returns emissions temporally distributed by day of the week.

"""
import xarray as xr
import numpy as np
import pandas as pd


def split_by_time(spatial_emiss: xr.DataArray,
                  temporal_profile: list[float]) -> xr.DataArray:
    """Distribute temporally one pollutant emission.

    Temporal disaggregation of a pollutant emission.
    It is used to distribute daily emission into hourly emissions.

    Parameters
    ----------
    spatial_emiss : xr.DataArray
        Pollutant spatial emission (e.g. g km^2 day^-1).
    temporal_profile : list
        A list of temporal fractions. For example,
        if spatial_emiss has emissions by day, then
        the hour emission are calculated based on a list of
        length 24 with the fraction by hour.

    Returns
    -------
    xr.DataArray
        Emissions disaggregated by time.

    """
    emiss_time = xr.concat(
        [spatial_emiss * time for time in temporal_profile],
        dim=pd.Index(np.arange(len(temporal_profile)),
                     name="Time")
    )
    return emiss_time


def split_by_time_from(spatial_sources: xr.Dataset,
                       temporal_profile: list[float]) -> xr.Dataset:
    """Distribute temporally all pollutant emission.

    Temporal disaggregation of many pollutant emissions.
    It is used to distribute daily emission into hourly emissions.

    Parameters
    ----------
    spatial_emiss : xr.Dataset
        Spatial emission of many pollutants (e.g. g km^2 day^-1).
    temporal_profile : list
        A list of temporal fractions. For example,
        if spatial_emiss has emissions by day, then
        the hour emission are calculated based on a list of
        length 24 with the fraction by hour.

    Returns
    -------
    xr.Dataset
        Pollutants emissions distributed by time.

    """
    spatial = spatial_sources.copy()
    spatio_temporal = {pol: split_by_time(spatial, temporal_profile)
                       for pol, spatial in spatial.items()}
    return xr.merge(spatio_temporal.values())


def transform_week_profile_df(weekday_profile: list[float]) -> pd.DataFrame:
    """Transfor weekday profile to dataframe.

    Transform a list of weekly weight from Monday to Sunday.
    into a DataFrame.

    Parameters
    ----------
    weekday_profile : list[float]
        A list with weekly weight from Monday to Sunday.
    Returns
    -------
    pd.DataFrame
        Week profile as DataFrame index are the days.

    """
    week = pd.DataFrame()
    week["day"] = np.arange(7)
    week["frac"] = np.array(weekday_profile)
    week.set_index("day", inplace=True)
    return week


def assign_factor_simulation_days(date_start: str, date_end: str,
                                  week_profile: list[float],
                                  is_cmaq: bool = False) -> pd.DataFrame:
    """
    Match the weekly weight to each day of the simulation period.

    Parameters
    ----------
    date_start : str
        Simulation start date.
    date_end : str
        Simulation end date.
    week_profile : list[float]
        A list with weekly weight from Monday to Sunday.
    is_cmaq : bool
        If is it for CMAQ emissions.

    Returns
    -------
    pd.DataFrame


    """
    simulation_days = pd.date_range(date_start, date_end, freq="D")
    week_prof = transform_week_profile_df(week_profile)
    days_factor = week_prof.frac.loc[simulation_days.weekday].to_frame()
    days_factor["day"] = simulation_days.strftime("%Y-%m-%d")
    if is_cmaq:
        days_factor["frac"] = days_factor.frac.astype("float32")
    return days_factor


def split_by_weekday(emiss_day: xr.Dataset,
                     weekday_profile: list[float],
                     date_start: str,
                     date_end: str) -> xr.Dataset:
    """
    Apply week profile to 24 hour emissions Dataset.

    Parameters
    ----------
    emiss_day : xr.Dataset
        24 hour emissions.
    weekday_profile : list[float]
        A list with weekly weight from Monday to Sunday.
    date_start : str
        Simulation start date.
    date_end : str
        Simulation end date.

    Returns
    -------
    xr.Dataset
        Emission with weekly variation.
    """
    days_factor = assign_factor_simulation_days(date_start, date_end,
                                                weekday_profile)
    days_emiss = {day: emiss_day * factor
                  for day, factor in enumerate(days_factor.frac)}
    days_emiss_all = xr.concat(days_emiss.values(), dim="Time")
    days_emiss_all["Time"] = np.arange(days_emiss_all.sizes["Time"])
    return days_emiss_all
