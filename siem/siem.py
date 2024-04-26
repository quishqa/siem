import typing
import numpy as np
import pandas as pd
import xarray as xr
import siem.spatial as spt
import siem.temporal as temp
import siem.emiss as em
import siem.wrfchemi as wemi
import siem.cmaq as cmaq
import siem.point as pt


class EmissionSource:
    def __init__(self, name: str, number: int | float, use_intensity: float,
                 pol_ef: dict, spatial_proxy: xr.DataArray,
                 temporal_prof: list, voc_spc: dict, pm_spc: dict):
        self.name = name
        self.number = number
        self.use_intensity = use_intensity
        self.pol_ef = pol_ef
        self.spatial_proxy = spatial_proxy
        self.temporal_prof = temporal_prof
        self.voc_spc = voc_spc
        self.pm_spc = pm_spc

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

    def spatiotemporal_emission(self, pol_names: str | list[str],
                                cell_area: int | float,
                                is_cmaq: bool = False) -> xr.DataArray:
        if isinstance(pol_names, str):
            pol_names = [pol_names]

        spatial_emissions = {
                pol: self.spatial_emission(pol, cell_area)
                for pol in pol_names
                }

        temp_prof = self.temporal_prof
        if is_cmaq:
            temp_prof = cmaq.to_25hr_profile(self.temporal_prof)

        spatio_temporal = {
                pol: temp.split_by_time(spatial, temp_prof)
                for pol, spatial in spatial_emissions.items()
                }
        return xr.merge(spatio_temporal.values())

    def speciate_emission(self, pol_name: str, pol_species: dict,
                          cell_area: int | float,
                          is_cmaq: bool = False) -> xr.DataArray:
        spatio_temporal = self.spatiotemporal_emission(pol_name,
                                                       cell_area, is_cmaq)
        speciated_emiss = em.speciate_emission(spatio_temporal,
                                               pol_name, pol_species,
                                               cell_area)
        return speciated_emiss

    def speciate_all(self, cell_area: int | float, voc_name: str = "VOC",
                     pm_name: str = "PM", is_cmaq: bool = False):
        spatio_temporal = self.spatiotemporal_emission(self.pol_ef.keys(),
                                                       cell_area, is_cmaq)
        speciated_emiss = em.speciate_emission(spatio_temporal,
                                               voc_name, self.voc_spc,
                                               cell_area)
        speciated_emiss = em.speciate_emission(speciated_emiss,
                                               pm_name, self.pm_spc,
                                               cell_area)
        return speciated_emiss

    def to_wrfchemi(self, wrfinput: xr.Dataset,
                    start_date: str, end_date: str,
                    week_profile: list[float] = [1],
                    pm_name: str = "PM", voc_name: str = "VOC",
                    write_netcdf: bool = False,
                    path: str = "../results") -> xr.Dataset:
        cell_area = (wrfinput.DX / 1000) ** 2
        spatio_temporal = self.spatiotemporal_emission(self.pol_ef.keys(),
                                                       cell_area)
        if len(week_profile) == 7:
            spatio_temporal = temp.split_by_weekday(spatio_temporal,
                                                    week_profile,
                                                    start_date,
                                                    end_date)
        spatio_temporal = wemi.transform_wrfchemi_units(spatio_temporal,
                                                        self.pol_ef,
                                                        pm_name)
        speciated_emiss = wemi.speciate_wrfchemi(spatio_temporal,
                                                 self.voc_spc, self.pm_spc,
                                                 cell_area, wrfinput, voc_name,
                                                 pm_name)
        wrfchemi_netcdf = wemi.prepare_wrfchemi_netcdf(speciated_emiss,
                                                       wrfinput)

        if write_netcdf:
            wemi.write_wrfchemi_netcdf(wrfchemi_netcdf, path)
        return wrfchemi_netcdf

    def to_cmaq(self, wrfinput: xr.Dataset, griddesc_path: str,
                n_points: int, start_date: str, end_date: str,
                week_profile: list[float] = [1],
                pm_name: str = "PM", voc_name: str = "VOC",
                write_netcdf: bool = False,
                path: str = "../results") -> typing.Dict[str, xr.Dataset]:
        cell_area = wrfinput.DX / 1000
        spatio_temporal = self.spatiotemporal_emission(self.pol_ef.keys(),
                                                       cell_area, is_cmaq=True)
        # Units
        # Speciation
        # speciated_emiss = self.speciate_all(1, voc_name, pm_name, is_cmaq=True)

        for emi in speciated_emiss.data_vars:
            speciated_emiss[emi] = speciated_emiss[emi].astype("float32")

        days_factor = temp.assign_factor_simulation_days(start_date, end_date,
                                                         week_profile)
        cmaq_files = {day: cmaq.prepare_netcdf_cmaq(speciated_emiss * np.float32(fact),
                                                    day, griddesc_path, n_points,
                                                    self.voc_spc, self.pm_spc)
                      for day, fact in zip(days_factor.day, days_factor.frac)}
        if write_netcdf:
            for cmaq_nc in cmaq_files.values():
                cmaq.save_cmaq_file(cmaq_nc, path)
        return cmaq_files


class PointSources:
    def __init__(self, name: str, point_path: str, sep: str, geo_path: str,
                 lat_name: str, lon_name: str, pol_emiss: dict,
                 temporal_prof: list[float], voc_spc: dict, pm_spc: dict):
        self.name = name
        self.spatial_emission = pt.point_sources_to_dataset(
                point_path, geo_path, sep, lat_name, lon_name)
        self.temporal_porf = temporal_prof
        self.voc_spc = voc_spc
        self.pm_spc = pm_spc

    def to_wrfchemi():
        pass


class GroupSources:
    def __init__(self, sources_list: list[EmissionSource]):
        self.sources = {source.name: source for source in sources_list}

    def names(self):
        names = list(self.sources.keys())
        print(names)
        return names

    def to_wrfchemi(self, wrfinput: xr.Dataset,
                    start_date: str, end_date: str,
                    week_profile: list[float] = [1],
                    pm_name: str = "PM", voc_name: str = "VOC",
                    write_netcdf: bool = False,
                    path: str = "../results") -> xr.Dataset:
        wrfchemis = {source: emiss.to_wrfchemi(wrfinput, start_date, end_date,
                                               week_profile, pm_name,
                                               voc_name, write_netcdf=False)
                     for source, emiss in self.sources.items()}
        wrfchemi = xr.concat(wrfchemis.values(),
                             pd.Index(wrfchemis.keys(), name="source"))
        if write_netcdf:
            wrfchemi = wrfchemi.sum(dim="source", keep_attrs=True)
            wrfchemi["Times"] = xr.DataArray(
                    wemi.create_date_s19(wrfinput.START_DATE,
                                         wrfchemi.sizes["Time"]),
                    dims=["Time"],
                    coords={"Time": wrfchemi.Time.values}
                    )
            wemi.write_wrfchemi_netcdf(wrfchemi, path=path)
        return wrfchemi

    def to_cmaq(self, wrfinput: xr.Dataset, griddesc_path: str,
                n_points: int, start_date: str, end_date: str,
                week_profile: list[float] = [1],
                pm_name: str = "PM", voc_name: str = "VOC",
                write_netcdf: bool = False,
                path: str = "../results") -> typing.Dict[str, dict]:
        cmaq_files = {source: emiss.to_cmaq(wrfinput, griddesc_path,
                                            n_points, start_date, end_date,
                                            week_profile, pm_name, voc_name)
                      for source, emiss in self.sources.items()}
        cmaq_source_day = cmaq.merge_cmaq_source_emiss(cmaq_files)
        sum_sources = cmaq.sum_cmaq_sources(cmaq_source_day)
        cmaq_sum_by_day = cmaq.update_tflag_sources(sum_sources)

        if write_netcdf:
            for cmaq_nc in cmaq_sum_by_day.values():
                cmaq.save_cmaq_file(cmaq_nc, path)
        return cmaq_sum_by_day
