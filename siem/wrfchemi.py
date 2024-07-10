import numpy as np
import pandas as pd
import xarray as xr
from siem.emiss import (speciate_emission, ktn_year_to_mol_hr,
                        ktn_year_to_ug_seg)
from siem.user import check_create_savedir


def transform_wrfchemi_units(spatial_emiss: xr.DataArray,
                             pol_ef_mw: dict,
                             pm_name: str = "PM") -> xr.Dataset:
    for pol_name, pol_mw in pol_ef_mw.items():
        if pol_name == pm_name:
            spatial_emiss[pm_name] = (
                    spatial_emiss[pm_name] / 3600
                    ).astype("float32")
        spatial_emiss[pol_name] = (
                spatial_emiss[pol_name] / pol_mw[1]
                ).astype("float32")
    return spatial_emiss


def transform_wrfchemi_units_point(spatial_emiss: xr.Dataset,
                                   pols_mw: dict,
                                   cell_area: int | float,
                                   pm_name: str = "PM") -> xr.Dataset:
    emiss_units = spatial_emiss.copy()
    for pol_name, pol_mw in pols_mw.items():
        if pol_name == pm_name:
            emiss_units[pol_name] = ktn_year_to_ug_seg(
                    emiss_units[pol_name]) / (cell_area * 1000 * 1000)
        emiss_units[pol_name] = ktn_year_to_mol_hr(emiss_units[pol_name],
                                                   pol_mw) / cell_area
    return emiss_units


def add_emission_attributes(speciated_wrfchemi: xr.Dataset,
                            voc_species: dict,
                            pm_species: dict, pm_name: str,
                            wrfinput: xr.Dataset) -> xr.Dataset:
    for pol in speciated_wrfchemi.data_vars:
        speciated_wrfchemi[pol].attrs["FieldType"] = 104
        speciated_wrfchemi[pol].attrs["MemoryOrder"] = 'XYZ'
        speciated_wrfchemi[pol].attrs["description"] = 'EMISSIONS'
        if (pol == pm_name) or (pol in pm_species.keys()):
            speciated_wrfchemi[pol].attrs["units"] = 'ug m^-2 s^-1'
        else:
            speciated_wrfchemi[pol].attrs["units"] = 'mol km^-2 hr^-1'
        speciated_wrfchemi[pol].attrs["stagger"] = ''
        speciated_wrfchemi[pol].attrs["coordinates"] = 'XLONG XLAT'

    return speciated_wrfchemi


def speciate_wrfchemi(spatial_emiss_units: xr.Dataset,
                      voc_species: dict, pm_species: dict,
                      cell_area: float | int,
                      wrfinput: xr.Dataset,
                      voc_name: str = "VOC",
                      pm_name: str = "PM",
                      add_attr: bool = True) -> xr.Dataset:
    speciated_wrfchemi = speciate_emission(spatial_emiss_units,
                                           voc_name, voc_species,
                                           cell_area)
    speciated_wrfchemi = speciate_emission(speciated_wrfchemi,
                                           pm_name, pm_species,
                                           cell_area)
    if add_attr:
        speciated_wrfchemi = add_emission_attributes(speciated_wrfchemi,
                                                     voc_species, pm_species,
                                                     pm_name,
                                                     wrfinput)
    name_dict = {pol: f"E_{pol}" for pol in speciated_wrfchemi.data_vars}
    speciated_wrfchemi = speciated_wrfchemi.rename(name_dict)

    return speciated_wrfchemi


def create_date_s19(start_date: str, periods: int = 24) -> np.ndarray:
    date_format = "%Y-%m-%d_%H:%M:%S"
    date_start = pd.to_datetime(start_date,
                                format=date_format)
    dates = pd.date_range(date_start, periods=periods, freq="h")
    dates_s19 = np.array(
            dates.strftime(date_format).values,
            dtype=np.dtype(("S", 19))
            )
    return dates_s19


def prepare_wrfchemi_netcdf(speciated_wrfchemi: xr.Dataset,
                            wrfinput: xr.Dataset) -> xr.Dataset:
    wrfchemi = (speciated_wrfchemi
                .assign_coords(emissions_zdim=0)
                .expand_dims("emissions_zdim")
                .transpose("Time", "emissions_zdim",
                           "south_north", "west_east"))
    wrfchemi["Times"] = xr.DataArray(
            create_date_s19(wrfinput.START_DATE, wrfchemi.sizes["Time"]),
            dims=["Time"],
            coords={"Time": wrfchemi.Time.values}
            )

    wrfchemi.XLAT.attrs = wrfinput.XLAT.attrs
    wrfchemi.XLONG.attrs = wrfinput.XLONG.attrs
    wrfchemi = wrfchemi.drop_vars("Time")

    for attr_name, attr_value in wrfinput.attrs.items():
        wrfchemi.attrs[attr_name] = attr_value

    wrfchemi.attrs["TITLE"] = "OUTPUT FROM LAPAT PREPROCESSOR"

    return wrfchemi


def create_wrfchemi_name(wrfchemi: xr.Dataset) -> str | tuple:
    if len(wrfchemi.Times) != 24:
        date_start = wrfchemi.START_DATE
        return f"wrfchemi_d{wrfchemi.GRID_ID:02}_{date_start}"
    else:
        file_name_00z = f"wrfchemi_00z_d{wrfchemi.GRID_ID:02}"
        file_name_12z = f"wrfchemi_12z_d{wrfchemi.GRID_ID:02}"
        return (file_name_00z, file_name_12z)


def write_netcdf(wrfchemi_netcdf: xr.Dataset, file_name: str,
                 path: str = "../results/") -> None:
    check_create_savedir(path)
    wrfchemi_netcdf.to_netcdf(f"{path}/{file_name}",
                              encoding={
                                  "Times": {"char_dim_name": "DateStrLen"}
                                  },
                              unlimited_dims={"Time": True},
                              format="NETCDF3_64BIT")


def write_wrfchemi_netcdf(wrfchemi_netcdf: xr.Dataset,
                          path: str) -> None:
    if len(wrfchemi_netcdf.Times) == 24:
        file_names = create_wrfchemi_name(wrfchemi_netcdf)
        wrfchemi00z = wrfchemi_netcdf.isel(Time=slice(0, 12))
        wrfchemi12z = wrfchemi_netcdf.isel(Time=slice(12, 24))
        write_netcdf(wrfchemi00z, file_names[0], path)
        write_netcdf(wrfchemi12z, file_names[1], path)
    else:
        write_netcdf(wrfchemi_netcdf,
                     create_wrfchemi_name(wrfchemi_netcdf),
                     path)
