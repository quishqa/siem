import numpy as np
import pandas as pd
import xarray as xr


def read_spatial_proxy(proxy_path: str,
                       col_names: list = ["id", "x", "y", "urban"],
                       sep: str = " ",
                       proxy: str = "urban",
                       lon_name: str = "x",
                       lat_name: str = "y") -> xr.DataArray:

    spatial_proxy = pd.read_csv(proxy_path, names=col_names, sep=sep)
    lon1d = spatial_proxy[lon_name].unique()
    lat1d = spatial_proxy[lat_name].unique()

    lon, lat = np.meshgrid(lon1d, lat1d)

    urban = (spatial_proxy[proxy]
             .values
             .reshape(len(lat1d), len(lon1d)))

    spatial_proxy = xr.DataArray(
            urban,
            dims=("south_north", "west_east"),
            coords={"XLAT": (("south_north", "west_east"), lat),
                    "XLONG": (("south_north", "west_east"), lon)})
    return spatial_proxy

    
