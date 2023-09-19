import numpy as np
import pandas as pd
import xarray as xr

class EmissionSource:
    def __init__(self, name: str, number: int | float, use_intensity: float,
                 pol_ef: dict, spatial_proxy: xr.DataArray, 
                 temporal_prof: list):
        self.name = name
        self.number = number
        self.use_intensity = use_intensity
        self.pol_ef = pol_ef
        self.temporal_prof = temporal_prof
        self.spatial_proxy = spatial_proxy


