import numpy as np
import pandas as pd
import xarray as xr
import siem.spatial as spt
import siem.temporal as temp


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

    def spatiotemporal_emission(self, pol_names: str | list,
                                cell_area: int | float) -> xr.DataArray:
        if isinstance(pol_names, str):
            pol_names = [pol_names]

        spatial_emissions = {
                pol: self.spatial_emission(pol, cell_area)
                for pol in pol_names
                }
        spatio_temporal = {
                pol: temp.split_by_time(spatial, self.temporal_prof)
                for pol, spatial in spatial_emissions.items()
                }
        return xr.merge(spatio_temporal.values())


    def speciate_emission(self, pol_name: str, pol_species: dict,
                          cell_area: int | float) -> xr.DataArray:
        spatio_temporal = self.spatiotemporal_emission(pol_name, cell_area)
        for new_pol, pol_fraction in pol_species.items():
            spatio_temporal[new_pol] = spatio_temporal[pol_name] * pol_fraction
        return spatio_temporal



def calculate_emission(number_source, activity_rate, pol_ef):
    return number_source * activity_rate * pol_ef
