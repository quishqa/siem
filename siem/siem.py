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
        self.spatial_proxy = spatial_proxy
        self.temporal_prof = temporal_prof

    def total_emission(self, pol_name: str, ktn_year: bool = False):
        total_emiss = calculate_emission(self.number,
                                         self.use_intensity,
                                         self.pol_ef[pol_name])
        if ktn_year:
            return total_emiss * 365 / 10 ** 9
        return total_emiss

    def spatial_emission(self, pol_name: str,
                         cell_area: int | float) -> xr.DataArray:
        return spt.distribute_spatial_emission(self.spatial_proxy,
                                               self.number,
                                               cell_area,
                                               self.use_intensity,
                                               self.pol_ef[pol_name],
                                               pol_name)

    def spatiotemporal_emission(self, pol_name: str,
                                cell_area: int | float) -> xr.DataArray:
        
        spatial_emission = self.spatial_emission(pol_name, cell_area)
        spatio_temporal = xr.concat(
                [spatial_emission * time for time in self.temporal_prof],
                dim=pd.Index(np.arange(0, len(self.temporal_prof)),
                             name="Time")
                )
        return spatio_temporal


def calculate_emission(number_source, activity_rate, pol_ef):
    return number_source * activity_rate * pol_ef
