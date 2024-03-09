import numpy as np
import pandas as pd
import xarray as xr
import PseudoNetCDF as pnc
import datetime as dt


def calculate_julian(date: pd.Timestamp) -> int:
    year = date.year
    jul = date.day_of_year
    return year * 1000 + jul


def convert_str_to_julian(date: str, fmt: str = "%Y-%m-%d") -> int:
    date_dt = pd.to_datetime(date, format=fmt)
    return calculate_julian(date_dt)


def create_date_limits(date: str, fmt: str = "%Y-%m-%d") -> tuple:
    date = pd.to_datetime(date, format=fmt)
    next_date = date + pd.DateOffset(1)
    start_julian = calculate_julian(date)
    end_julian = calculate_julian(next_date)
    return (start_julian, end_julian)


def create_hour_matrix(date: int, hour: int, n_var: int) -> np.ndarray:
    hour = np.array([[date, hour * 10000]], dtype="int32")
    return np.repeat(hour, n_var, axis=0)


def create_tflag_matrix(date: str, n_var: int) -> np.ndarray:
    day_start, day_end = create_date_limits(date)
    tflag_m = np.empty((25, n_var, 2))
    for hour in range(24):
        tflag_m[hour] = create_hour_matrix(day_start, hour, n_var)
    tflag_m[-1] = create_hour_matrix(day_end, 0, n_var)
    return tflag_m.astype("int32")


def create_tflag_variable(date: str, n_var: int) -> xr.DataArray:
    tflag = xr.DataArray(
            data=create_tflag_matrix(date, n_var),
            dims=["TSTEP", "VAR", "DATE-TIME"],
            attrs={
                "units": "<YYYYDD,HHMMSS>",
                "long_name": "TFLAG",
                "var_desc": f'{"Timestep-valid flags:  (1) YYYYDDD or (2) HHMMSS":<80}'
                }
            )
    tflag.name = "TFLAG"
    return tflag


