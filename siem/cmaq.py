import typing
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


def to_25hr_profile(temporal_profile: list[float]) -> list[float]:
    prof_25h = [h for h in temporal_profile]
    prof_25h.append(prof_25h[0])
    return prof_25h


def add_cmaq_emission_attrs(speciated_cmaq: xr.Dataset,
                            voc_species: dict,
                            pm_species: dict, pm_name: str = "PM",
                            voc_name: str = "VOC") -> xr.Dataset:
    for pol in speciated_cmaq.data_vars:
        var_desc = "Model species " + pol
        speciated_cmaq[pol].attrs["units"] = "moles/s"
        if (pol == pm_name) or (pol in pm_species.keys()):
            speciated_cmaq[pol].attrs["units"] = "g/s"
        speciated_cmaq[pol].attrs["long_name"] = f"{pol:<16}"
        speciated_cmaq[pol].attrs["var_desc"] = f"{var_desc:<80}"

    return speciated_cmaq.drop_vars([voc_name, pm_name])


def create_var_list_attrs(speciated_cmaq_attrs: xr.Dataset) -> list[str]:
    var_list = [f"{pol:<16}" for pol in speciated_cmaq_attrs.data_vars
                if pol != "TFLAG"]
    return "".join(var_list)


def create_global_attrs(speciated_cmaq_attr: xr.Dataset,
                        griddesc_path: str) -> xr.Dataset:
    griddesc = pnc.pncopen(griddesc_path, format="griddesc")
    emiss_vars = [emi for emi in speciated_cmaq_attr.data_vars if emi != "TFLAG"]
    now_date = dt.datetime.now()

    global_attrs = {}
    global_attrs["IOAPI_VERSION"] = f"{'ioapi-3.2: $Id: init3.F90 98 2018-04-05 14:35:07Z coats $':<80}"
    global_attrs["EXEC_ID"] = f"{'?' * 16:<80}"
    global_attrs["FTYPE"] = np.int32(1)
    global_attrs["CDATE"] = calculate_julian(pd.to_datetime(now_date))
    global_attrs["CTIME"] = int(f"{now_date.hour}{now_date.minute}{now_date.second}")
    global_attrs["WDATE"] = calculate_julian(pd.to_datetime(now_date))
    global_attrs["WTIME"] = int(f"{now_date.hour}{now_date.minute}{now_date.second}") 
    global_attrs["SDATE"] = speciated_cmaq_attr.TFLAG.isel(TSTEP=0, VAR=0).values[0]
    global_attrs["STIME"] = 0
    global_attrs["TSTEP"] = 10000
    global_attrs["NTHIK"] = 1
    global_attrs["NCOLS"] = speciated_cmaq_attr.sizes["COL"]
    global_attrs["NROWS"] = speciated_cmaq_attr.sizes["ROW"]
    global_attrs["NLAYS"] = speciated_cmaq_attr.sizes["LAY"]
    global_attrs["NVARS"] = speciated_cmaq_attr.sizes["VAR"]
    global_attrs["GDTYP"] = griddesc.GDTYP
    global_attrs["P_ALP"] = griddesc.P_ALP
    global_attrs["P_BET"] = griddesc.P_BET
    global_attrs["P_GAM"] = griddesc.P_GAM
    global_attrs["XCENT"] = griddesc.XCENT
    global_attrs["YCENT"] = griddesc.YCENT
    global_attrs["XORIG"] = griddesc.XORIG
    global_attrs["YORIG"] = griddesc.YORIG
    global_attrs["XCELL"] = griddesc.XCELL
    global_attrs["YCELL"] = griddesc.YCELL
    global_attrs["VGTYP"] = griddesc.VGTYP
    global_attrs["VGTOP"] = griddesc.VGTOP
    global_attrs["VGLVLS"] = griddesc.VGLVLS
    global_attrs["GDNAM"] = griddesc.GDNAM
    global_attrs["UPNAM"] = griddesc.UPNAM
    global_attrs["VAR-LIST"] = create_var_list_attrs(speciated_cmaq_attr)
    global_attrs["FILEDESC"] = f"{'Merged emissions output file from Mrggrid':<80}"
    global_attrs["HISTORY"] = ""

    return global_attrs


def prepare_netcdf_cmaq(speciated_cmaq: xr.Dataset, date: str,
                        griddesc_path: str, n_point: int,
                        voc_species: dict,
                        pm_species: dict, pm_name: str = "PM",
                        voc_name: str = "VOC") -> xr.Dataset:
    speciated_cmaq = add_cmaq_emission_attrs(speciated_cmaq,
                                             voc_species,
                                             pm_species,
                                             pm_name,
                                             voc_name)
    speciated_cmaq = speciated_cmaq.rename_dims(
            {"Time": "TSTEP", "west_east": "COL", "south_north": "ROW"}
            )
    speciated_cmaq = speciated_cmaq.drop_vars(["Time", "XLAT", "XLONG"])
    speciated_cmaq = (speciated_cmaq
                      .expand_dims("LAY")
                      .transpose("TSTEP", "LAY", "ROW", "COL"))
    n_vars = len(speciated_cmaq.data_vars)
    speciated_cmaq["TFLAG"] = create_tflag_variable(date, n_vars)

    ori_row, ori_col = speciated_cmaq.sizes["ROW"], speciated_cmaq.sizes["COL"]
    speciated_cmaq = speciated_cmaq.isel(
            ROW=slice(n_point, ori_row - 6), COL=slice(n_point, ori_col - 6)
            )
    speciated_cmaq.attrs = create_global_attrs(speciated_cmaq,
                                               griddesc_path)
    return speciated_cmaq
