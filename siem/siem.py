import xarray as xr
import siem.spatial as spt
import siem.temporal as temp
import siem.emiss as em
import siem.wrfchemi as wemi


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
        total_emiss = em.calculate_emission(self.number,
                                            self.use_intensity,
                                            self.pol_ef[pol_name][0])
        if ktn_year:
            return total_emiss * 365 / 10 ** 9
        return total_emiss

    def spatial_emission(self, pol_name: str,
                         cell_area: int | float) -> xr.DataArray:
        return spt.distribute_spatial_emission(self.spatial_proxy,
                                               self.number,
                                               cell_area,
                                               self.use_intensity,
                                               self.pol_ef[pol_name][0],
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
        speciated_emiss = em.speciate_emission(spatio_temporal,
                                               pol_name, pol_species,
                                               cell_area)
        return speciated_emiss

    def speciate_all(self, voc_species: dict, pm_species: dict,
                     cell_area: int | float, voc_name: str = "VOC",
                     pm_name: str = "PM"):
        spatio_temporal = self.spatiotemporal_emission(self.pol_ef.keys(),
                                                       cell_area)
        speciated_emiss = em.speciate_emission(spatio_temporal,
                                               voc_name, voc_species,
                                               cell_area)
        speciated_emiss = em.speciate_emission(speciated_emiss,
                                               pm_name, pm_species,
                                               cell_area)
        return speciated_emiss

    def to_wrfchemi(self, voc_species: dict, pm_species: dict,
                    cell_area: int | float, wrfinput: xr.Dataset,
                    pm_name: str = "PM", voc_name: str = "VOC",
                    write_netcdf: bool = False, 
                    path: str= "../results") -> xr.Dataset:
        spatio_temporal = self.spatiotemporal_emission(self.pol_ef.keys(),
                                                       cell_area)
        spatio_temporal = wemi.transform_wrfchemi_units(spatio_temporal,
                                                        self.pol_ef,
                                                        pm_name)
        speciated_emiss = wemi.speciate_wrfchemi(spatio_temporal,
                                                 voc_species, pm_species,
                                                 cell_area, wrfinput, voc_name,
                                                 pm_name)
        wrfchemi_netcdf = wemi.prepare_wrfchemi_netcdf(speciated_emiss,
                                                       wrfinput)

        if write_netcdf:
            wemi.write_wrfchemi_netcdf(wrfchemi_netcdf, path)
        return wrfchemi_netcdf


class GroupSources:
    def __init__(self, sources_list: list[EmissionSource]):
        self.sources = {source.name: source for source in sources_list}

    def to_wrfchemi(self, voc_species: dict, pm_species: dict,
                    cell_area: int | float, wrfinput: xr.Dataset,
                    pm_name: str = "PM", voc_name: str = "VOC",
                    write_netcdf: bool = False, 
                    path: str= "../results") -> xr.Dataset:
        wrfchemis = {source: emiss.to_wrfchemi(voc_species, pm_species,
                                               cell_area, wrfinput, pm_name,
                                               voc_name, write_netcdf=False)
                     for source, emiss in self.sources.items()}
        return wrfchemis
        


    



