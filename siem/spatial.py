"""
Functions to read and process spatial emission proxy.
"""
import numpy as np
import pandas as pd
import xarray as xr
import siem.emiss as em


def read_spatial_proxy(proxy_path: str,
                       col_names: list = ["id", "x", "y", "urban"],
                       sep: str = " ",
                       proxy: str = "urban",
                       lon_name: str = "x",
                       lat_name: str = "y") -> xr.DataArray:
    """
    Read spatial proxy (emission weights) csv file.
    It has to have the same number of points as wrfinput file.

    Parameters
    ----------
    proxy_path : str
        The location of the csv file.
    col_names : list
        Columns name of the csv file.
    sep : str
        csv file separator.
    proxy : str
        The column with the proxy value.
    lon_name : str
        Column name of the longitude.
    lat_name : str
        Column name of the latitude.

    Returns
    -------
    xr.DataArray
        Spatial proxy with dimensions as wrfinput.

    """
    spatial_proxy = pd.read_csv(proxy_path, names=col_names, sep=sep)
    lon1d = spatial_proxy[lon_name].round(5).unique()
    lat1d = spatial_proxy[lat_name].round(5).unique()

    lon, lat = np.meshgrid(lon1d, lat1d)

    urban = (spatial_proxy[proxy]
             .values
             .reshape(len(lat1d), len(lon1d)))

    spatial_proxy = xr.DataArray(
        urban,
        dims=("south_north", "west_east"),
        coords={"XLAT": (("south_north", "west_east"), lat),
                "XLONG": (("south_north", "west_east"), lon)})
    spatial_proxy["XLAT"] = spatial_proxy.XLAT.astype("float32")
    spatial_proxy["XLONG"] = spatial_proxy.XLONG.astype("float32")
    return spatial_proxy


def calculate_density_map(spatial_proxy: xr.DataArray,
                          number_sources: int | float,
                          cell_area: int | float) -> xr.DataArray:
    """
    Transforms the proxy (emission weigth) into a density of emission
    sources (# emission sources / km ^2).

    Parameters
    ----------
    spatial_proxy : xr.DataArray
        Spatial emission weights.
    number_sources : int | float
        Number of sources in the domain.
    cell_area : int | float
        wrfinput cell area (km^2)

    Returns
    -------
    xr.DataArray
        Spatial distribution of number of sources by square km^2.

    """
    total_proxy = spatial_proxy.sum()
    ratio = number_sources / total_proxy
    return spatial_proxy * ratio / cell_area


def distribute_spatial_emission(spatial_proxy: xr.DataArray,
                                number_sources: int | float,
                                cell_area: float,
                                use_intensity: float,
                                pol_ef: float,
                                pol_name: str) -> xr.DataArray:
    """
    Calculate the total emission of a pollutant in each cell.

    Parameters
    ----------
    spatial_proxy : xr.DataArray
        Spatial emission weights.
    number_sources : int | float
        Number of sources in the domain.
    cell_area : float
        wrfinput cell area (km^2)
    use_intensity : float
        Emission source use intensity.
    pol_ef : float
        Pollutant emission factor.
    pol_name : str
        Pollutant name.

    Returns
    -------
    xr.DataArray
        Emission of a single pollutant.    

    """
    density_map = calculate_density_map(spatial_proxy,
                                        number_sources,
                                        cell_area)
    spatial_emission = em.calculate_emission(density_map,
                                             use_intensity,
                                             pol_ef)
    spatial_emission.name = pol_name
    return spatial_emission
