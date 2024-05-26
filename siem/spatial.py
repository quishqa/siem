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
    total_proxy = spatial_proxy.sum()
    ratio = number_sources / total_proxy
    return spatial_proxy * ratio / cell_area


def distribute_spatial_emission(spatial_proxy: xr.DataArray,
                                number_sources: int | float,
                                cell_area: float,
                                use_intensity: float,
                                pol_ef: float,
                                pol_name: str) -> xr.DataArray:
    density_map = calculate_density_map(spatial_proxy,
                                        number_sources,
                                        cell_area)
    spatial_emission = em.calculate_emission(density_map,
                                             use_intensity,
                                             pol_ef)
    spatial_emission.name = pol_name
    return spatial_emission
