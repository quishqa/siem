# siem/siem.py
"""SIEM: SImplified Emission Model.

SIEM produces the emission file required to run WRF-Chem and CMAQ air quality models.

This modules defined the classes used by siem to create this emissions files:
    - `EmissionSource` - Class to spatially and temporal distribute emissions, especially vehicular emissions.
    - `PointSources` - Class to spatially and temporal distribute point sources from a .csv table.
    - `GroupSources` - Class to group EmissionSources and PointSources, useful to create one emission file.

"""

import typing
import pandas as pd
import xarray as xr
import siem.spatial as spt
import siem.temporal as temp
import siem.emiss as em
import siem.wrfchemi as wemi
import siem.cmaq as cmaq


class EmissionSource:
    """Emission source.

    A class used to represent and emission source to
    be estimated from spatial proxy.

    Attributes
    ----------
    name : Name of Source.
    number : Number of Sources.
    use_intensity : Use intensity
    pol_ef : Pollutant emission factors and molecular weight.
    spatial_proxy : Spatial proxy to spatial distribute emissions.
    temporal_prof : Temporal profile to temporal distribute emissions.
    voc_spc : VOC species to speciate with their fraction.
    pm_spc : PM species to speciate with their fraction.

    """

    def __init__(self, name: str, number: int | float, use_intensity: float,
                 pol_ef: dict, spatial_proxy: xr.DataArray,
                 temporal_prof: list[float], voc_spc: dict, pm_spc: dict):
        """
        Create the EmissionSource object.

        Parameters
        ----------
        name : str
            Name of the source.
        number : int | float
            Number of sources (e.g., number of vehicles)
        use_intensity : float
            Emission source activity rate.
        pol_ef : dict
            Keys are pollutants in the inventory,
            values are a tuple with pollutant emission factors
            and molecular weight.
        spatial_proxy : xr.DataArray
            Proxy to spatially distribute emissions.
        temporal_prof : list[float]
            Hourly fractions to temporally distribute emissions.
        voc_spc : dict
            Keys are VOC species, and values are the fraction
            of the total VOC.
        pm_spc : dict
            Keys are PM species, and values are the fraction
            of the total PM.

        """
        self.name = name
        self.number = number
        self.use_intensity = use_intensity
        self.pol_ef = pol_ef
        self.spatial_proxy = spatial_proxy
        self.temporal_prof = temporal_prof
        self.voc_spc = voc_spc
        self.pm_spc = pm_spc

    def __str__(self):
        """
        Print summary of EmissionSource attributes.

        Returns
        -------
            Print name, number, pollutants,
            and VOC and PM species information
            from EmissionSource.

        """
        source_summary = (
            f"Source name: {self.name}\n"
            f"Number: {self.number}\n"
            f"Pollutants: {list(self.pol_ef.keys())}\n"
            f"Number VOC species: {len(self.voc_spc.keys())}\n"
            f"Number PM species: {len(self.pm_spc.keys())}\n"
        )
        return source_summary

    def total_emission(self, pol_name: str, ktn_year: bool = False) -> float:
        """
        Calculate total emission of a pollutant.

        Parameters
        ----------
        pol_name : str
            Pollutant name to calculate the total emission.
        ktn_year : bool
            If total is calculated in KTn (Gg) year^-1

        Returns
        -------
            Total emission of a pollutant.

        """
        total_emiss = em.calculate_emission(self.number,
                                            self.use_intensity,
                                            self.pol_ef[pol_name][0])
        if ktn_year:
            return total_emiss * 365 / 10 ** 9
        return total_emiss

    def report_emissions(self) -> pd.DataFrame:
        """
        Return the total emission for each pollutant in pol_ef.

        Returns
        -------
        pd.DataFrame
            A table with pollutants as index and total emissions
            as columns.

        """
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
        """
        Distribute one pollutant.

        Parameters
        ----------
        pol_name : str
            Key value in pol_ef.
        cell_area : int | float
            Area of wrfinput.

        Returns
        -------
        xr.DataArray
            Spatially distributed emissions.

        """
        return spt.distribute_spatial_emission(self.spatial_proxy,
                                               self.number,
                                               cell_area,
                                               self.use_intensity,
                                               self.pol_ef[pol_name][0],
                                               pol_name)

    def spatiotemporal_emission(self, pol_names: str | list[str],
                                cell_area: int | float,
                                is_cmaq: bool = False) -> xr.DataArray:
        """
        Spatial and temporal distribution of emissions.

        Parameters
        ----------
        pol_names : str | list[str]
            Name or names of pollutants to distribute.
        cell_area : int | float
            Wrfinput cell area.
        is_cmaq : bool
            If it will be used for CMAQ.

        Returns
        -------
        xr.DataArray
            Spatial and temporal emission distribution.

        """
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
        """
        Speciate one pollutant emissions. Used especially for VOC or NOX.

        Parameters
        ----------
        pol_name : str
            Pollutant name in pol_ef to speciate.
        pol_species : dict
            Keys are pollutants speciated from pol_name.
            Values are the fraction.
        cell_area : int | float
            wrfinput cell area km^2
        is_cmaq : bool
            If output is for CMAQ.

        Returns
        -------
        xr.DataArray
            Spatial and temporal distribution of speciated emission.

        """
        spatio_temporal = self.spatiotemporal_emission(pol_name,
                                                       cell_area, is_cmaq)
        speciated_emiss = em.speciate_emission(spatio_temporal,
                                               pol_name, pol_species,
                                               cell_area)
        return speciated_emiss

    def speciate_all(self, cell_area: int | float, voc_name: str = "VOC",
                     pm_name: str = "PM", is_cmaq: bool = False) -> xr.Dataset:
        """
        Speciate VOC and PM.

        Parameters
        ----------
        cell_area : int | float
            wrfinput cell area.
        voc_name : str
            Name of VOC in pol_ef keys.
        pm_name : str
            Name of PM in pol_ef keys.
        is_cmaq : bool
            If output for CMAQ.

        Returns
        -------
        xr.Dataset
            Spatial and temporal distributed emissions with
            VOC and PM speciated.

        """
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
        """
        Create WRF-Chem emission file (wrfchemi).

        Parameters
        ----------
        wrfinput : xr.Dataset
            WRF-Chem wrfinput file.
        start_date : str
            Start date of emissions.
        end_date : str
            End date of emissions.
        week_profile : list[float]
            List of seven fraction of each week day.
        pm_name : str
            PM name in pol_ef keys.
        voc_name : str
            VOC name in pol_ef keys
        write_netcdf : bool
            Write the NetCDF file.
        path : str
            Location to save wrfchemi.

        Returns
        -------
        xr.Dataset
            Dataset with wrfchemi netCDF format.

        """
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
        """
        Create CMAQ emission file.

        Parameters
        ----------
        wrfinput : xr.Dataset
            wrfinput from WRF simulation.
        griddesc_path : str
            Location of GRIDDESC file.
        btrim : int
            BTRIM option in MCIP.
        start_date : str
            Start date of emission files.
        end_date : str
            End date of emission files.
        week_profile : list[float]
            List of seven fraction of each week day.
        pm_name : str
            PM name in pol_ef keys.
        voc_name : str
            VOC name in pol_ef keys.
        write_netcdf : bool
            Write the netCDF file.
        path : str
            Location to save CMAQ emission file.

        Returns
        -------
        typing.Dict[str, xr.Dataset]
            Keys are simulation days and values the emission file for CMAQ
            for that day.

        """
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
    """Point sources.

    A class to read points emission sources in a
    table where columns are longitude, latitude, and
    the total emissions of diferent pollutants in
    kTn (Gg) year^-1

    Attributes
    ----------
    name : Name of the point emission sources.
    spatial_emission : Spatially distributed emissions in simulation domain.
    pol_emiss : Names of considered pollutants (columns).
    temporal_prof : Temporal profile to temporal emission distribution.
    voc_spc : VOC speciation dict. Keys are VOC species, values are fractions.
    pm_spc : PM speciation dict. Keys are PM species, values are fractions.

    """

    def __init__(self, name: str, point_emiss: xr.Dataset,
                 pol_emiss: dict, temporal_prof: list[float],
                 voc_spc: dict, pm_spc: dict):
        """
        Create PointSource  object.

        Parameters
        ----------
        name : str
            Name of point sources emissions.
        point_emiss : xr.Dataset
            Points sources in table read with
        pol_emiss : dict
            Keys are columns in point_emiss.
            values are the molecular weight.
        temporal_prof : list[float]
            Hourly fractions to temporally distribute emissions.
        voc_spc : dict
            Keys are VOC species. Values are fractions from the total VOC.
        pm_spc : dict
            Keys are PM species. Values are fractions from the total PM.

        """
        self.name = name
        self.spatial_emission = point_emiss
        self.pol_emiss = pol_emiss
        self.temporal_prof = temporal_prof
        self.voc_spc = voc_spc
        self.pm_spc = pm_spc

    def __str__(self):
        """
        Print summary of PointSource attributes.

        Returns
        -------
            Print name, number, pollutants,
            and VOC and PM species information
            from EmissionSource.

        """
        source_summary = (
            f"Source name: {self.name}\n"
            f"Pollutants: {list(self.pol_emiss.keys())}\n"
            f"Number VOC species: {len(self.voc_spc.keys())}\n"
            f"Number PM species: {len(self.pm_spc.keys())}\n"
        )
        return source_summary

    def total_emission(self, pol_name: str) -> float:
        """
        Calculate total emission of a pollutant.

        Parameters
        ----------
        pol_name : str
            Pollutant name to calculate the total emission.

        Returns
        -------
            Total emission of a pollutant in KTn (Gg) year^-1

        """
        if pol_name in self.pol_emiss.keys():
            return self.spatial_emission[pol_name].sum().values
        else:
            print(f"{pol_name} not include in data")

    def report_emissions(self) -> pd.DataFrame:
        """
        Return the total emission for each pollutant in pol_ef.

        Returns
        -------
        pd.DataFrame
            A table with pollutants as index and total emissions
            as columns.

        """
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
        """
        Create WRF-Chem emission file.

        Parameters
        ----------
        wrfinput : xr.Dataset
            WRF wrfinput.
        start_date : str
            Start date of emission.
        end_date : str
            End date of emission.
        week_profile : list[float]
            Emission weights of days of week.
        pm_name : str
            PM name in pol_emiss.
        voc_name : str
            VOC name in pol_emiss.
        write_netcdf : bool
            Write wrfchemi netCDF.
        path : str
            Location to save wrfchemi files.

        Returns
        -------
        xr.Dataset
            Emission file in wrfchemi netCDF format.

        """
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
        """Create CMAQ emission file.

        Create and save CMAQ emission file.

        Parameters
        ----------
        wrfinput : xr.Dataset
            WRF wrfinput.
        griddesc_path : str
            Location of GRIDDESC file.
        btrim : int
            BTRIM value in MCIP.
        start_date : str
            Start date of emission.
        end_date : str
            End date of emission.
        week_profile : list[float]
            Emission weights of days of week.
        pm_name : str
            PM name in pol_emiss.
        voc_name : str
            VOC name in pol_emiss.
        write_netcdf : bool
            Save CMAQ emission file.
        path : str
            Location to save CMAQ emission file.

        Returns
        -------
        typing.Dict[str, xr.Dataset]
            Keys are simulation day.
            Values are Daset in CMAQ emission file netcdf format.

        """
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
    """
    A class that group EmissionSources and PointSources object.

    Attributes
    ----------
    sources : A list of EmissionSources and PointSources objects.

    """

    def __init__(self, sources_list: list[EmissionSource | PointSources]):
        """
        Create a GroupSource object.

        Parameters
        ----------
        sources_list : list[EmissionSource | PointSources]
            List with EmissionSource and PointSources to group.

        """
        self.sources = {source.name: source for source in sources_list}

    def __str__(self):
        """
        Print summary of GroupSources attributes.

        Returns
        -------
            Print number and types of Sources.
        """
        type_of_sources = [type(source) for source in self.sources.values()]
        source_summary = (
            f"Number of sources: {len(self.names())}\n"
            f"Type of sources: {set(type_of_sources)}\n"
        )
        return source_summary

    def names(self):
        """
        Print names of source emission in GroupSources.

        Returns
        -------
            Names of source emissions.
        """
        names = list(self.sources.keys())
        return names

    def report_emissions(self) -> pd.DataFrame:
        """
        Return the total emission for each pollutant in pol_emiss.

        Returns
        -------
        pd.DataFrame
            Table with emission source and pollutant as index.

        """
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
        """
        Create WRF-Chem emission file.

        Parameters
        ----------
        wrfinput : xr.Dataset
            WRF-Chem wrfinput.
        start_date : str
            Start date of emission.
        end_date : str
            End date of emission.
        week_profile : list[float]
            Emission weights of days of week.
        pm_name : str
            PM name in emissions.
        voc_name : str
            VOC name in emissions.
        write_netcdf : bool
            Save wrfchemi file.
        path : str
            Location to save wrfchemi file.

        Returns
        -------
        xr.Dataset
            Emission file in WRF-Chem wrfchemi netCDF format.

        """
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
        """Create CMAQ emission file.

        Create CMAQ emission file. All EmissionSource and GroupSources
        need to have same speciation.

        Parameters
        ----------
        wrfinput : xr.Dataset
            WRF wrfinput file.
        griddesc_path : str
            Location of GRIDDESC file.
        btrim : int
            BTRIM value in MCIP.
        start_date : str
            Start date of emissions.
        end_date : str
            End date of emissions.
        week_profile : list[float]
            Emission weights of days of week.
        pm_name : str
            PM name in pol_ef or pol_emiss.
        voc_name : str
            VOC name in pol_ef or pol_emiss.
        write_netcdf : bool
            Save CMAQ emission file.
        path : str
            Location to save CMAQ emission file.

        Returns
        -------
        typing.Dict[str, dict]
            Keys are emission days. Values are emission in CMAQ
            emission file netCDF format.

        """
        cmaq_files = {source: emiss.to_cmaq(wrfinput, griddesc_path,
                                            btrim, start_date, end_date,
                                            week_profile, pm_name, voc_name)
                      for source, emiss in self.sources.items()}
        cmaq_source_day = cmaq.merge_cmaq_source_emiss(cmaq_files)
        sum_sources = cmaq.sum_cmaq_sources(cmaq_source_day)
        cmaq_sum_by_day = cmaq.update_tflag_sources(sum_sources)

        if write_netcdf:
            for cmaq_nc in cmaq_sum_by_day.values():
                cmaq.save_cmaq_file(cmaq_nc, path)
        return cmaq_sum_by_day
