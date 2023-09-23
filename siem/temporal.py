import xarray as xr
import numpy as np
import pandas as pd

def split_by_time(spatial_emiss: xr.DataArray,
                  temporal_profile: list) -> xr.DataArray:
    emiss_time = xr.concat(
            [spatial_emiss * time for time in temporal_profile],
            dim=pd.Index(np.arange(len(temporal_profile)),
                         name="Time")
            )
    return emiss_time

