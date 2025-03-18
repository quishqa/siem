# siem/cmaq.py
"""Functions to build the CMAQ emission file.

This module allows you to build dayly CMAQ emission files.
It requires the wrfinput, and GRIDDESC files.

It contains the following functions:

    - `calculate_julian(date)` - Returns: timestamp in julian date.
    - `convert_str_to_julian(date, fmt)` - Returns: date string in julian.
    - `create_date_limits(date, fmt)` - Returns: day and the next day in julian.
    - `create_hour_matrix(date, hour, n_var)` - Returns: a matrix for one hour of day.
    - `create_tflag_matrix(date, n_var)` - Returns: tflag matrix for 25 hours.
    - `create_tflag_variable(date, n_var)` - Returns: TFLAG variable in xr.DataArray.
    - `to_25hr_profile(temporal_profile)` - Returns: a 25 hour temporal profile (added first hour of next day).
    - `transform_cmaq_units(spatial_emiss, pol_ef_mw, cell_area, pm_name)` - Returns: spatial emissions in CMAQ units.
    - `transform_cmaq_units_points(spatial_emiss, pol_mw, pm_name)` - Returns: points emissions in CMAQ units.
    - `speciate_cmaq(spatial_emiss_units, voc_spc, pm_spc, cell_area, voc_name, pm_name)` - Returns: speciated VOC and PM emissions.
    - `add_cmaq_emission_attrs(speciated_cmap, voc_spc, pm_spc, voc_name, pm_name)` - Returns: CMAQ emission dataset with each variables with attributes.
    - `create_var_list_attrs(speciated_cmaq_attrs)` - Returns: the VAR list global attribute.
    - `create_global_attrs(speciated_cmaq_attrs, griddesc_path)` - Returns: global attributes of CMAQ emission file.
    - `prepare_netcdf_cmaq(specated_cmaq, date, griddesc_path, btrim, voc_spc, pm_spc, voc_name, pm_name)` - Returns: xr.Dataset with CMAQ netcdf format.
    - `save_cmaq_file(cmaq, path)` - Saves xr.dataset CMAQ emission into netcdf.
    - `merge_cmaq_source_emiss(cmaq_sources_day)` - Returns: different sources emission adition per day by source.
    - `sum_cmaq_source(day_source_emission)`- Returns: total emissions from different sources.
    - `update_tflag_sources(sum_sources_by_day)`- Corrects/update TFLAGS variable of sum_cmaq_source product.

"""

import typing
import numpy as np
import pandas as pd
import xarray as xr
import PseudoNetCDF as pnc
import datetime as dt
from siem.emiss import (speciate_emission, ktn_year_to_g_seg,
                        ktn_year_to_mol_seg)
from siem.user import check_create_savedir


def calculate_julian(date: pd.Timestamp) -> int:
    """Calculate julian date.

    Args:
        date: Date to transform to julian day.

    Returns:
        Julian day.
    """
    year = date.year
    jul = date.day_of_year
    return year * 1000 + jul


def convert_str_to_julian(date: str, fmt: str = "%Y-%m-%d") -> int:
    """Convert date in string to julian (int).

    Args:
        date: Date in string.
        fmt: Date format.

    Returns:
        Julian day.

    """
    date_dt = pd.to_datetime(date, format=fmt)
    return calculate_julian(date_dt)


def create_date_limits(date: str, fmt: str = "%Y-%m-%d") -> tuple:
    """Create day and the day after as julian.

    Args:
        date: Date in string.
        fmt: Date format.

    Returns:
        Date and the date after in julian.
    """
    date = pd.to_datetime(date, format=fmt)
    next_date = date + pd.DateOffset(1)
    start_julian = calculate_julian(date)
    end_julian = calculate_julian(next_date)
    return (start_julian, end_julian)


def create_hour_matrix(date: int, hour: int, n_var: int
                       ) -> np.ndarray:
    """Create hour matrix.

    First column is date in julian. The second column is the hours.

    Args:
        date: Date in julian.
        hour: Hour of day.
        n_var: Number of emissions species in emission file.

    Returns:
        Date, hour matrix to create TFLAG variable.
    """
    hour = np.array([[date, hour * 10000]], dtype="int32")
    return np.repeat(hour, n_var, axis=0)


def create_tflag_matrix(date: str, n_var: int) -> np.ndarray:
    """Create the tflag matrix based on 25 hour emission.

    Args:
        date: Day of emission.
        n_var: Number of emission species in emission file.

    Returns:
        TFLAG matrix with correct dimensions.
    """
    day_start, day_end = create_date_limits(date)
    tflag_m = np.empty((25, n_var, 2))
    for hour in range(24):
        tflag_m[hour] = create_hour_matrix(day_start, hour, n_var)
    tflag_m[-1] = create_hour_matrix(day_end, 0, n_var)
    return tflag_m.astype("int32")


def create_tflag_variable(date: str, n_var: int) -> xr.DataArray:
    """Create TFLAG variable with correct dimensions and time.

    Args:
        date: Day of emission.
        n_var: Number of species emission on emission file.

    Returns:
        TFLAG variable with correct dimensions and attributes.
    """
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
    """Create a 25 hour temporal profile from the 24 hour temporal_profile.

    Args:
        temporal_profile: 24 hour temporal profile.

    Returns:
        25 hour temporal profile for CMAQ emission file.
    """
    prof_25h = [h for h in temporal_profile]
    prof_25h.append(prof_25h[0])
    return prof_25h


def transform_cmaq_units(spatial_emiss: xr.Dataset,
                         pol_ef_mw: typing.Dict[str, float],
                         cell_area: float,
                         pm_name: str = "PM") -> xr.Dataset:
    """Transform emission into CMAQ emission file units.

    Args:
        spatial_emiss: Spatial distributed emission.
        pol_ef_mw: Keys are emitted species. Values are the molecular weight.
        cell_area: wrfinput cell are in km^2.
        pm_name: PM name in pol_ef_mw.

    Returns:
        Emitted species (not speciated) in CMAQ units.
    """
    for pol_name, pol_mw in pol_ef_mw.items():
        if pol_name == pm_name:
            spatial_emiss[pol_name] = (spatial_emiss[pol_name] *
                                       cell_area / pol_mw[1] / 3600)
    return spatial_emiss


def transform_cmaq_units_point(spatial_emiss: xr.Dataset, pol_mw: dict,
                               pm_name: str = "PM") -> xr.Dataset:
    """Transform point emission units in kTn (Gg) per year emission into CMAQ emission units.

    Args:
        spatial_emiss: Spatial distributed emissions.
        pol_mw: Keys are emitted species. Values are the molecular weight.
        pm_name: PM name in pol_ef_mw.

    Returns:
        Emitted species (not speciated) in CMAQ units.
    """
    emiss_units = spatial_emiss.copy()
    for pol_name, pol_mw in pol_mw.items():
        if pol_name == pm_name:
            emiss_units[pol_name] = ktn_year_to_g_seg(emiss_units[pol_name])
        emiss_units[pol_name] = ktn_year_to_mol_seg(emiss_units[pol_name],
                                                    pol_mw)
    return emiss_units


def speciate_cmaq(spatial_emiss_units: xr.Dataset,
                  voc_species: typing.Dict[str, float],
                  pm_species: typing.Dict[str, float],
                  cell_area: float,
                  voc_name: str = "VOC", pm_name: str = "PM") -> xr.Dataset:
    """Speciate VOC and PM emission already in CMAQ units.

    Args:
        spatial_emiss_units: Spatial distributed emission in CMAQ units.
        voc_species: Keys are VOC specias and values are the VOC fraction.
        pm_species: Keys are PM specias and values are the PM fraction.
        cell_area: wrfinput cell area in km^2
        voc_name: VOC emission name.
        pm_name: PM emission name.

    Returns:
        Speciated emission in CMAQ units.
    """
    speciated_cmaq = speciate_emission(spatial_emiss_units,
                                       voc_name, voc_species,
                                       cell_area)
    speciated_cmaq = speciate_emission(speciated_cmaq, pm_name,
                                       pm_species, cell_area)
    return speciated_cmaq


def add_cmaq_emission_attrs(speciated_cmaq: xr.Dataset,
                            voc_species: typing.Dict[str, float],
                            pm_species: typing.Dict[str, float],
                            pm_name: str = "PM",
                            voc_name: str = "VOC") -> xr.Dataset:
    """Add attributes to emission species variables.

    Args:
        speciated_cmaq: Speciated spatial distributed emissions.
        voc_species: Keys are VOC specias and values are the VOC fraction.
        pm_species: Keys are PM specias and values are the PM fraction.
        pm_name: PM emission name.
        voc_name: VOC emission name.

    Returns:
        Speciated emissions with variables with attributes.
    """
    for pol in speciated_cmaq.data_vars:
        var_desc = "Model species " + pol
        speciated_cmaq[pol].attrs["units"] = "moles/s"
        if (pol == pm_name) or (pol in pm_species.keys()):
            speciated_cmaq[pol].attrs["units"] = "g/s"
        if (pol in ["IOLE", "VOC_INV", "NVOL"]):
            speciated_cmaq[pol].attrs["units"] = "g/s"
        speciated_cmaq[pol].attrs["long_name"] = f"{pol:<16}"
        speciated_cmaq[pol].attrs["var_desc"] = f"{var_desc:<80}"

    return speciated_cmaq.drop_vars([voc_name, pm_name])


def create_var_list_attrs(speciated_cmaq_attrs: xr.Dataset) -> list[str]:
    """Create a VAR list for global attributes.

    Args:
        speciated_cmaq_attrs: Speciated spatial distributed emissions with attributes.

    Returns:
        List of emission species.
    """
    var_list = [f"{pol:<16}" for pol in speciated_cmaq_attrs.data_vars
                if pol != "TFLAG"]
    return "".join(var_list)


def create_global_attrs(speciated_cmaq_attr: xr.Dataset,
                        griddesc_path: str) -> typing.Dict:
    """Create the global attributes for the emission file.

    Args:
        speciated_cmaq_attr: Speciated spatial distributed emissions with attributes.
        griddesc_path: Location of GRIDDESC file.

    Returns:
        Global attributes of emission file.
    """
    griddesc = pnc.pncopen(griddesc_path, format="griddesc")
    now_date = dt.datetime.now()

    global_attrs = {}
    global_attrs["IOAPI_VERSION"] = f"{'ioapi-3.2: $Id: init3.F90 98 2018-04-05 14:35:07Z coats $':<80}"
    global_attrs["EXEC_ID"] = f"{'?' * 16:<80}"
    global_attrs["FTYPE"] = np.int32(1)
    global_attrs["CDATE"] = calculate_julian(pd.to_datetime(now_date))
    global_attrs["CTIME"] = int(
        f"{now_date.hour}{now_date.minute}{now_date.second}")
    global_attrs["WDATE"] = calculate_julian(pd.to_datetime(now_date))
    global_attrs["WTIME"] = int(
        f"{now_date.hour}{now_date.minute}{now_date.second}")
    global_attrs["SDATE"] = speciated_cmaq_attr.TFLAG.isel(
        TSTEP=0, VAR=0).values[0]
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
                        griddesc_path: str, btrim: int,
                        voc_species: typing.Dict[str, float],
                        pm_species: typing.Dict[str, float],
                        pm_name: str = "PM",
                        voc_name: str = "VOC") -> xr.Dataset:
    """Prepare speciated emission dataset into CMAQ emission netcdf format.

    Args:
        speciated_cmaq: Spatial distributed speciated emissions.
        date: Day of emission.
        griddesc_path: GRIDDESC location.
        btrim: BTRIM value from MCIP run.
        voc_species: Keys are VOC species and values are the VOC fraction.
        pm_species: Keys are PM species and values are the PM fraction.
        pm_name: PM emission name.
        voc_name: VOC emission name.

    Returns:
        Speiciated dataset with CMAQ emission netcdf format.
    """
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
        ROW=slice(btrim + 1, ori_row - (btrim + 1)),
        COL=slice(btrim + 1, ori_col - (btrim + 1))
    )
    speciated_cmaq.attrs = create_global_attrs(speciated_cmaq,
                                               griddesc_path)
    return speciated_cmaq


def create_cmaq_file_name(cmaq_nc: xr.Dataset) -> str:
    """Create CMAQ emission file.

    Args:
        cmaq_nc: Speciated emission CMAQ dataset.

    Returns:
        Emission file name with DATE.
    """
    file_date = (cmaq_nc
                 .TFLAG
                 .isel(TSTEP=0, VAR=0)
                 .isel({"DATE-TIME": 0})
                 .values)
    date = (dt.datetime
            .strptime(str(file_date), "%Y%j")
            .date()
            .strftime("%Y%m%d"))
    return f'cmaq_emissions_{date}.nc'


def save_cmaq_file(cmaq_nc: xr.Dataset,
                   path: str = "../results/") -> None:
    """Save CMAQ file.

    Args:
        cmaq_nc: Speciated CMAQ emission dataset with the correct Netcdf format.
        path: Location to save the emission file.

    """
    check_create_savedir(path)
    file_name = f'{path}/{create_cmaq_file_name(cmaq_nc)}'
    cmaq_nc.to_netcdf(file_name,
                      unlimited_dims={"TSTEP": True},
                      format="NETCDF3_CLASSIC")


def merge_cmaq_source_emiss(cmaq_sources_day: typing.Dict) -> xr.Dataset:
    """Sum different source emission by day. For GroupSources.

    Args:
        cmaq_sources_day: Keys are sources, values are emissions by day.

    Returns:
        CMAQ emission dataset with a source dimension.
    """
    add_day_dimension = {source: xr.concat(emiss.values(),
                                           pd.Index(emiss.keys(), name="day"))
                         for source, emiss in cmaq_sources_day.items()}
    day_source_dimension = xr.concat(add_day_dimension.values(),
                                     pd.Index(add_day_dimension.keys(),
                                              name="source"))
    return day_source_dimension


def sum_cmaq_sources(day_source_dimension: xr.Dataset
                     ) -> typing.Dict[str, xr.Dataset]:
    """Get total emission from different sources. For GroupSources.

    Args:
        day_source_dimension: CMAQ emission dataset with a source dimension.

    Returns:
        Keys are days and values the sum emission of different sources.
    """
    sum_sources = day_source_dimension.sum(dim="source",
                                           keep_attrs=True)
    sum_sources_by_day = {day: sum_sources.sel(day=day)
                          for day in sum_sources.day.values}
    return sum_sources_by_day


def update_tflag_sources(sum_sources_by_day: typing.Dict[str, xr.Dataset]
                         ) -> typing.Dict[str, xr.Dataset]:
    """Update TFLAG variables of total emission from diferent sources.

    Args:
        sum_sources_by_day: Keys are days and values the sum emission of different sources.

    Returns:
        Keys are days and values the sum emission of different sources
        with correct TFLAG value.
    """
    sum_sources_by_day = {day: emis.drop_vars(["day", "TFLAG"])
                          for day, emis in sum_sources_by_day.items()}
    for day, sum_source in sum_sources_by_day.items():
        sum_source["TFLAG"] = create_tflag_variable(day,
                                                    len(sum_source.data_vars))
        sum_source.attrs["SDATE"] = sum_source.TFLAG.isel(
            TSTEP=0, VAR=0).values[0]
    return sum_sources_by_day
