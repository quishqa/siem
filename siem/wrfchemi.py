# siem/wrfchemi.py
"""Functions to create wrfchemi file.

This module has function to create the WRF-Chem emission file.

It contains the following functions:
    - `transform_wrfchemi_units(spatial_emiss, pol_ef_mw, pm_name)` - Returns: emissions in wrf-chem units for gas and aerosols.
    - `transform_wrfchemi_units_point(spatial_emiss, pol_ef_mw, cell_area, pm_name)` - Returns: point emissions in wrf-chem units for gas and aerosol.
    - `add_emission_attributes(speciated_wrfchemi, voc_species, pm_name, wrfinput)` - Returns: speciated emission with wrf-chem attributes.
    - `speciate_wrfchemi(spatial_emiss_units, voc_species, pm_species, cell_area, wrfinput)` - Returns: emissions with speciated PM and VOC.
    - `create_date_s19(start_date, periods)` - Returns: date in s19 type.
    - `prepare_wrfchemi_netcdf(speciated_wrfchemi, wrfinput)` - Returns: a xr.Dataset with wrfchemi format (attributes).
    - `create_wrfchemi_name(wrfchemi)` - Return file name based on the number of periods.
    - `write_netcdf(wrfchemi_netcdf, file_name, path)` - Write wrfchemi file on disk.
    - `write_wrfchemi_netcdf(wrfchemi_netcdf, path)` - Write wrfchemi file on disk based on Times variable.
"""

import typing
import numpy as np
import pandas as pd
import xarray as xr
from siem.emiss import speciate_emission
from siem.user import check_create_savedir


def transform_wrfchemi_units(
    spatial_emiss: xr.Dataset, pol_ef_mw: typing.Dict[str, tuple], pm_name: str = "PM"
) -> xr.Dataset:
    """Transform to WRF-Chem units.

    Convert emission units (g hr^-1) to WRF-Chem require units.
    Gas species      to mol km^-2 hr^-1 and,
    aerossol species to ug m^-2 s^-1.

    Args:
        spatial_emiss: Spatial distributed pollutant emission.
        pol_ef_mw: Key are pollutant name and value the molecular weight.
        pm_name: Name of particular matter emission in pols_ef_mw.

    Returns:
        Emission species in WRF-Chem units.
    """
    for pol_name, pol_mw in pol_ef_mw.items():
        if pol_name == pm_name:
            spatial_emiss[pm_name] = (
                spatial_emiss[pm_name] / 3600  # 1E6 to ug / 1E6 to m2
            ).astype("float32")
        spatial_emiss[pol_name] = (
            spatial_emiss[pol_name] / pol_mw[1]  # ok
        ).astype("float32")
    return spatial_emiss


def transform_wrfchemi_units_point(
    spatial_emiss: xr.Dataset,
    pols_mw: typing.Dict[str, float],
    cell_area: int | float,
    pm_name: str = "PM",
) -> xr.Dataset:
    """Transform emissions units to WRF-Chem units. It is used for PointSources.

    Args:
        spatial_emiss: Spatial distributed emissions.
        pols_mw: Key are pollutant names, values are molecular weight.
        cell_area: wrfinput cell area
        pm_name: Particular matter name in pols_mw.

    Returns:
        Emission species in WRF-Chem units.
    """
    emiss_units = spatial_emiss.copy()  # units in g hr^-1
    for pol_name, pol_mw in pols_mw.items():
        if pol_name == pm_name:
            emiss_units[pol_name] /= cell_area * 3600  # ug  m^-2 s^-1
        else:
            emiss_units[pol_name] /= pol_mw * cell_area  # mol km^-2 hr^-1
    return emiss_units


def add_emission_attributes(
    speciated_wrfchemi: xr.Dataset,
    voc_species: typing.Dict[str, float],
    pm_species: typing.Dict[str, float],
    pm_name: str,
    wrfinput: xr.Dataset,
) -> xr.Dataset:
    """Add variables attributes to wrfchemi dataset.

    Args:
        speciated_wrfchemi: Speciated emission in wrfchemi units.
        voc_species: Keys are VOC species. Values are the % for speciation.
        pm_species: Keys are PM species. Values are the % for speciation.
        pm_name: PM name in pol_ef_mw.
        wrfinput: wrfinput file open with xr.open_dataset.

    Returns:
        Wrfchemi dataset with species variables with attributes.

    """
    for pol in speciated_wrfchemi.data_vars:
        speciated_wrfchemi[pol].attrs["FieldType"] = 104
        speciated_wrfchemi[pol].attrs["MemoryOrder"] = "XYZ"
        speciated_wrfchemi[pol].attrs["description"] = "EMISSIONS"
        if (pol == pm_name) or (pol in pm_species.keys()):
            speciated_wrfchemi[pol].attrs["units"] = "ug m^-2 s^-1"
        else:
            speciated_wrfchemi[pol].attrs["units"] = "mol km^-2 hr^-1"
        speciated_wrfchemi[pol].attrs["stagger"] = ""
        speciated_wrfchemi[pol].attrs["coordinates"] = "XLONG XLAT"

    return speciated_wrfchemi


def speciate_wrfchemi(
    spatial_emiss_units: xr.Dataset,
    voc_species: typing.Dict[str, float],
    pm_species: typing.Dict[str, float],
    cell_area: float | int,
    wrfinput: xr.Dataset,
    voc_name: str = "VOC",
    pm_name: str = "PM",
    add_attr: bool = True,
) -> xr.Dataset:
    """Speciate VOC and PM emissions.

    Create the base of wrfchemi file by speciating VOC and PM emission
    and adding the attributes.

    Args:
        spatial_emiss_units: Spatial and temporal distributed emissions.
        voc_species: Keys are VOC species and Values the fraction from total VOC.
        pm_species: Keys are PM species and Values the fraction from total PM.
        cell_area: wrfinput cell area (km^2)
        wrfinput: wrfinput open with xr.open_dataset.
        voc_name: Name of VOC emission in spatial_emiss_units dataset.
        pm_name: Name of PM emission in spatial_emiss_units dataset.
        add_attr: Add or not variables attributes.

    Returns:
        Wrfchemi dataset with species variables with attributes.

    """
    speciated_wrfchemi = speciate_emission(
        spatial_emiss_units, voc_name, voc_species, cell_area
    )
    speciated_wrfchemi = speciate_emission(
        speciated_wrfchemi, pm_name, pm_species, cell_area
    )
    if add_attr:
        speciated_wrfchemi = add_emission_attributes(
            speciated_wrfchemi, voc_species, pm_species, pm_name, wrfinput
        )
    name_dict = {pol: f"E_{pol}" for pol in speciated_wrfchemi.data_vars}
    speciated_wrfchemi = speciated_wrfchemi.rename(name_dict)

    return speciated_wrfchemi


def create_date_s19(start_date: str, periods: int = 24) -> np.ndarray:
    """
    Create dates in S19 type for one day.

    Args:
    start_date : str
        simulation start date in "%Y-%m-%d_%H:%M:%S".
    periods : int
        Number of hours of day.

    Returns:
    np.ndarray
        Vector with day hours in S19.

    """
    date_format = "%Y-%m-%d_%H:%M:%S"
    date_start = pd.to_datetime(start_date, format=date_format)
    dates = pd.date_range(date_start, periods=periods, freq="h")
    dates_s19 = np.array(dates.strftime(date_format).values, dtype=np.dtype(("S", 19)))
    return dates_s19


def prepare_wrfchemi_netcdf(
    speciated_wrfchemi: xr.Dataset, wrfinput: xr.Dataset, start_date: str
) -> xr.Dataset:
    """
    Transform wrfchemi dataset into wrfchemi Netcdf format.

    Args:
    speciated_wrfchemi : xr.Dataset
        Speciated wrfchemi dataset with species with attributes.
    wrfinput : xr.Dataset
        wrfinput open with xr.open_dataset.
    start_date : str
        Start date of emissions files in %Y-%m-%d format.

    Returns:
    xr.Dataset
        Dataset in WRF-Chem wrfchemi netcdf format.
        Same dimensions and global attributes.

    """
    start_date_formated = f"{start_date}_00:00:00"

    wrfchemi = (
        speciated_wrfchemi.assign_coords(emissions_zdim=0)
        .expand_dims("emissions_zdim")
        .transpose("Time", "emissions_zdim", "south_north", "west_east")
    )
    wrfchemi["Times"] = xr.DataArray(
        create_date_s19(start_date_formated, wrfchemi.sizes["Time"]),
        dims=["Time"],
        coords={"Time": wrfchemi.Time.values},
    )

    wrfchemi.XLAT.attrs = wrfinput.XLAT.attrs
    wrfchemi.XLONG.attrs = wrfinput.XLONG.attrs
    wrfchemi = wrfchemi.drop_vars("Time")

    for attr_name, attr_value in wrfinput.attrs.items():
        wrfchemi.attrs[attr_name] = attr_value

    wrfchemi.attrs["TITLE"] = "OUTPUT FROM LAPAT PREPROCESSOR"
    wrfchemi.attrs["START_DATE"] = start_date_formated
    wrfchemi.attrs["SIMULATION_START_DATE"] = start_date_formated

    return wrfchemi


def create_wrfchemi_name(wrfchemi: xr.Dataset) -> str | tuple:
    """
    Create wrfchemi file name to save.

    Args:
    wrfchemi : xr.Dataset
        wrfchemi dataset in WRF-Chem wrfchemi netcdf format.

    Returns:
    str | tuple
        wrfchemi file names.

    """
    if len(wrfchemi.Times) != 24:
        date_start = wrfchemi.START_DATE
        return f"wrfchemi_d{wrfchemi.GRID_ID:02}_{date_start}"
    else:
        file_name_00z = f"wrfchemi_00z_d{wrfchemi.GRID_ID:02}"
        file_name_12z = f"wrfchemi_12z_d{wrfchemi.GRID_ID:02}"
        return (file_name_00z, file_name_12z)


def write_netcdf(
    wrfchemi_netcdf: xr.Dataset,
    file_name: str,
    nc_format: str,
    path: str = "../results/",
) -> None:
    """
    Save netcdf file.

    Args:
        wrfchemi_netcdf: wrfchemi dataset in WRF-Chem wrfchemi netcdf format.
        file_name: wrfchemi file names.
        nc_format: wrfchemi netCDF file format.
        path: Path to save  netcdf.

    Returns:
        None

    """
    check_create_savedir(path)
    wrfchemi_netcdf.to_netcdf(
        f"{path}/{file_name}",
        encoding={"Times": {"char_dim_name": "DateStrLen"}},
        unlimited_dims={"Time": True},
        format=nc_format,
    )


def write_wrfchemi_netcdf(
    wrfchemi_netcdf: xr.Dataset, nc_format: str, path: str
) -> None:
    """
    Save the wrfchemi in WRF-Chem netcdf format in netcdf file.

    Args:
        wrfchemi_netcdf: wrfchemi dataset in WRF-Chem wrfchemi netcdf format.
        nc_format: wrfchemi netCDF file format.
        path: Location to save the wrfchemi file.

    Returns:
        None

    """
    if len(wrfchemi_netcdf.Times) == 24:
        file_names = create_wrfchemi_name(wrfchemi_netcdf)
        wrfchemi00z = wrfchemi_netcdf.isel(Time=slice(0, 12))
        wrfchemi12z = wrfchemi_netcdf.isel(Time=slice(12, 24))
        write_netcdf(wrfchemi00z, file_names[0], nc_format, path)
        write_netcdf(wrfchemi12z, file_names[1], nc_format, path)
    else:
        write_netcdf(
            wrfchemi_netcdf, create_wrfchemi_name(wrfchemi_netcdf), nc_format, path
        )
