import numpy as np
import pandas as pd
import xarray as xr
import siem.spatial as spt

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

    def total_emission(self, pol_name: str, ktn_year: bool = False):
        total_emiss = calculate_emission(self.number,
                                         self.use_intensity,
                                         self.pol_ef[pol_name])
        if ktn_year:
            return total_emiss * 365 / 10 ** 9
        return total_emiss

    def spatial_emission(self, pol_name: str,
                         wrfinput: xr.Dataset) -> xr.DataArray:
        return spt.distribute_spatial_emission(self.spatial_proxy,
                                               self.number,
                                               wrfinput,
                                               self.use_intensity,
                                               self.pol_ef[pol_name],
                                               pol_name)






def calculate_emission(number_source, activity_rate, pol_ef):
    return number_source * activity_rate * pol_ef
