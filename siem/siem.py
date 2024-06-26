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

    def __str__(self):
        source_summary = (
                f"Source name: {self.name}\n"
                f"Number: {self.number}\n"
                f"Pollutants: {list(self.pol_ef.keys())}\n"
                f"Number VOC species: {len(self.voc_spc.keys())}\n"
                f"Number PM species: {len(self.pm_spc.keys())}\n"
                )
        return source_summary

    def total_emission(self, pol_name: str, ktn_year: bool = False):
        total_emiss = em.calculate_emission(self.number,
                                            self.use_intensity,
                                            self.pol_ef[pol_name][0])
        if ktn_year:
            return total_emiss * 365 / 10 ** 9
        return total_emiss

    def report_emissions(self) -> pd.DataFrame:
        total_emission = {
                pol: self.total_emission(pol, ktn_year=True)
                for pol in self.pol_ef.keys()
                }
        total_emission = pd.DataFrame.from_dict(
                total_emission, orient="index", columns=["total_emiss"]
                )
        return total_emission

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
                btrim: int, start_date: str, end_date: str,
                week_profile: list[float] = [1],
                pm_name: str = "PM", voc_name: str = "VOC",
                write_netcdf: bool = False,
                path: str = "../results") -> typing.Dict[str, xr.Dataset]:
        cell_area = (wrfinput.DX / 1000) ** 2
        spatio_temporal = self.spatiotemporal_emission(self.pol_ef.keys(),
                                                       cell_area, is_cmaq=True)
        spatio_temporal_units = cmaq.transform_cmaq_units(spatio_temporal,
                                                          self.pol_ef,
                                                          cell_area)
        speciated_emiss = cmaq.speciate_cmaq(spatio_temporal_units,
                                             self.voc_spc, self.pm_spc,
                                             cell_area)

        # TODO: Change it to a function
        for emi in speciated_emiss.data_vars:
            speciated_emiss[emi] = speciated_emiss[emi].astype("float32")

        days_factor = temp.assign_factor_simulation_days(start_date, end_date,
                                                         week_profile,
                                                         is_cmaq=True)
        cmaq_files = {
                day: cmaq.prepare_netcdf_cmaq(speciated_emiss * fact,
                                              day, griddesc_path, btrim,
                                              self.voc_spc, self.pm_spc)
                for day, fact in zip(days_factor.day, days_factor.frac)
                      }
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
        self.pol_emiss = pol_emiss
        self.temporal_prof = temporal_prof
        self.voc_spc = voc_spc
        self.pm_spc = pm_spc

    def __str__(self):
        source_summary = (
                f"Source name: {self.name}\n"
                f"Pollutants: {list(self.pol_emiss.keys())}\n"
                f"Number VOC species: {len(self.voc_spc.keys())}\n"
                f"Number PM species: {len(self.pm_spc.keys())}\n"
                )
        return source_summary

    def total_emission(self, pol_name: str) -> float:
        if pol_name in self.pol_emiss.keys():
            return self.spatial_emission[pol_name].sum().values
        else:
            print(f"{pol_name} not include in data")

    def report_emissions(self) -> pd.DataFrame:
        total_emission = {
                pol: self.total_emission(pol)
                for pol in self.pol_emiss.keys()
                }
        total_emission = pd.DataFrame.from_dict(
                total_emission, orient="index", columns=["total_emiss"]
                )
        return total_emission

    def to_wrfchemi(self, wrfinput: xr.Dataset,
                    start_date: str, end_date: str,
                    week_profile: list[float] = [1],
                    pm_name: str = "PM", voc_name: str = "VOC",
                    write_netcdf: bool = False,
                    path: str = "../results/"
                    ) -> xr.Dataset:
        cell_area = (wrfinput.DX / 1000) ** 2
        point = self.spatial_emission
        point_spc = wemi.transform_wrfchemi_units_point(point, self.pol_emiss,
                                                        cell_area)
        point_spc_time = temp.split_by_time_from(point_spc, self.temporal_prof)
        if len(week_profile) == 7:
            point_spc_time = temp.split_by_weekday(point_spc_time,
                                                   week_profile,
                                                   start_date,
                                                   end_date)
        point_speciated = wemi.speciate_wrfchemi(point_spc_time, self.voc_spc,
                                                 self.pm_spc, cell_area,
                                                 wrfinput)
        wrfchemi_netcdf = wemi.prepare_wrfchemi_netcdf(point_speciated,
                                                       wrfinput)
        if write_netcdf:
            wemi.write_wrfchemi_netcdf(wrfchemi_netcdf, path)
        return wrfchemi_netcdf

    def to_cmaq(self, wrfinput: xr.Dataset, griddesc_path: str,
                btrim: int, start_date: str, end_date: str,
                week_profile: list[float] = [1],
                pm_name: str = "PM", voc_name: str = "VOC",
                write_netcdf: bool = False,
                path: str = "../results") -> typing.Dict[str, xr.Dataset]:
        cell_area = (wrfinput.DX / 1000) ** 2
        spatio_temporal = self.spatial_emission
        cmaq_temp_prof = cmaq.to_25hr_profile(self.temporal_prof)

        point_time = temp.split_by_time_from(spatio_temporal,
                                             cmaq_temp_prof)
        point_time_units = cmaq.transform_cmaq_units_point(point_time,
                                                           self.pol_emiss,
                                                           pm_name)
        speciated_emiss = cmaq.speciate_cmaq(point_time_units,
                                             self.voc_spc, self.pm_spc,
                                             cell_area)
        for emi in speciated_emiss.data_vars:
            speciated_emiss[emi] = speciated_emiss[emi].astype("float32")

        days_factor = temp.assign_factor_simulation_days(start_date, end_date,
                                                         week_profile,
                                                         is_cmaq=True)
        cmaq_files = {
                day: cmaq.prepare_netcdf_cmaq(speciated_emiss * fact,
                                              day, griddesc_path, btrim,
                                              self.voc_spc, self.pm_spc)
                for day, fact in zip(days_factor.day, days_factor.frac)
                }
        if write_netcdf:
            for cmaq_nc in cmaq_files.values():
                cmaq.save_cmaq_file(cmaq_nc, path)
        return cmaq_files


class GroupSources:
    def __init__(self, sources_list: list[EmissionSource | PointSources]):
        self.sources = {source.name: source for source in sources_list}

    def __str__(self):
        type_of_sources = [type(source) for source in self.sources.values()]
        source_summary = (
                f"Number of sources: {len(self.names())}\n"
                f"Type of sources: {set(type_of_sources)}\n"
                )
        return source_summary

    def names(self):
        names = list(self.sources.keys())
        return names

    def report_emissions(self) -> pd.DataFrame:
        total_emissions = {
                src_name: src.report_emissions()
                for src_name, src in self.sources.items()}
        return pd.concat(total_emissions, names=["src", "pol"])

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
                btrim: int, start_date: str, end_date: str,
                week_profile: list[float] = [1],
                pm_name: str = "PM", voc_name: str = "VOC",
                write_netcdf: bool = False,
                path: str = "../results") -> typing.Dict[str, dict]:
        cmaq_files = {source: emiss.to_cmaq(wrfinput, griddesc_path,
                                            btrim, start_date, end_date,
                                            week_profile, pm_name, voc_name)
                      for source, emiss in self.sources.items()}
        cmaq_source_day = cmaq.merge_cmaq_source_emiss(cmaq_files)
        sum_sources = cmaq.sum_cmaq_sources(cmaq_source_day)
        cmaq_sum_by_day = cmaq.update_tflag_sources(sum_sources)

        if write_netcdf:
            for cmaq_nc in cmaq_sum_by_day.values():
                cmaq.save_cmaq_file(cmaq_nc.drop_vars("day"), path)
        return cmaq_sum_by_day
