# siem/spatial.py
"""Functions for emission spatial disaggregation.

This modules helps you to read proxies to spatially distribute emissions,
and to perform the spatial emission distribution.

It contains the following functions:

    - `read_spatial_proxy(proxy_path, proxy_shape, col_names, sep, proxy, lon_name, lat_name)` - Returns: spatial proxy (weight) in xr.DataArray.
    - `calculate_density_map(spatial_proxy, number_sources, cell_area)` - Returns: number of emissions by km^2.
    - `distribute_spatial_emission(spatial_proxy, number_sources, cell_area, use_intensity, pol_ef, pol_name)` - Calculate total emissions of a pollutant (g day^-1 km^-2)
"""

import pandas as pd
import xarray as xr
import siem.emiss as em


def read_spatial_proxy(
    proxy_path: str,
    proxy_shape: tuple,
    col_names: list = ["id", "x", "y", "urban"],
    sep: str = " ",
    proxy: str = "urban",
    lon_name: str = "x",
    lat_name: str = "y",
) -> xr.DataArray:
    """Read spatial proxy.

    Read spatial proxy (emission weights) csv file.
    It has to have the same number of points as wrfinput file.

    Args:
        proxy_path: The location of the csv file.
        proxy_shap: Dimensions of proxy, number of columns and number of rows.
        col_names: Columns name of the csv file.
        sep: csv file separator.
        proxy: The column with the proxy value.
        lon_name: Column name of the longitude.
        lat_name: Column name of the latitude.

    Returns:
        Spatial proxy with dimensions as wrfinput.
    """
    spatial_proxy = pd.read_csv(proxy_path, names=col_names, sep=sep)
    ncol, nrow = proxy_shape

    urban = spatial_proxy[proxy].values.reshape(nrow, ncol)

    lat = spatial_proxy[lat_name].values.reshape(nrow, ncol)
    lon = spatial_proxy[lon_name].values.reshape(nrow, ncol)

    spatial_proxy = xr.DataArray(
        urban,
        dims=("south_north", "west_east"),
        coords={
            "XLAT": (("south_north", "west_east"), lat),
            "XLONG": (("south_north", "west_east"), lon),
        },
    )
    spatial_proxy["XLAT"] = spatial_proxy.XLAT.astype("float32")
    spatial_proxy["XLONG"] = spatial_proxy.XLONG.astype("float32")
    return spatial_proxy


def calculate_density_map(
    spatial_proxy: xr.DataArray, number_sources: int | float, cell_area: int | float
) -> xr.DataArray:
    """Calculate density map.

    Transform the proxy (emission weight) into a density of emission
    sources (# emission sources / km ^2).

    Args:
        spatial_proxy: Spatial emission weights.
        number_sources: Number of sources in the domain.
        cell_area: wrfinput cell area (km^2)

    Returns:
        Spatial distribution of number of sources by square km^2.
    """
    total_proxy = spatial_proxy.sum()
    ratio = number_sources / total_proxy
    return spatial_proxy * ratio / cell_area


def distribute_spatial_emission(
    spatial_proxy: xr.DataArray,
    number_sources: int | float,
    cell_area: float,
    use_intensity: float,
    pol_ef: float,
    pol_name: str,
) -> xr.DataArray:
    """Calculate the total emission of a pollutant in each cell.

    Args:
        spatial_proxy: Spatial emission weights.
        number_sources: Number of sources in the domain.
        cell_area: wrfinput cell area (km^2)
        use_intensity: Emission source use intensity (km/day).
        pol_ef: Pollutant emission factor (g/km).
        pol_name: Pollutant name.

    Returns:
        Emission of a single pollutant (g/day).
    """
    # TODO: move to emiss.py
    density_map = calculate_density_map(spatial_proxy, number_sources, cell_area)
    spatial_emission = em.calculate_emission(density_map, use_intensity, pol_ef)
    spatial_emission.name = pol_name
    return spatial_emission
