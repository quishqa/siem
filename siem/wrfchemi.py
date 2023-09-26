'''
Functions to create wrfchemi file
- Change units for gas and pm
- speciate
- write attributes for species
- write global attributes
- add date and vertical dimension
'''
import xarray as xr
from siem.emiss import speciate_emission


def transform_wrfchemi_units(spatial_emiss: xr.DataArray,
                             pol_ef_mw: dict,
                             pm_name: str = "PM") -> xr.Dataset:
    for pol_name, pol_mw in pol_ef_mw.items():
        spatial_emiss[pol_name] = spatial_emiss[pol_name] / pol_mw[1]
        if pol_name == pm_name:
            spatial_emiss[pm_name] = spatial_emiss[pm_name] / 3600
    return spatial_emiss

def add_emission_attributes(speciated_wrfchemi: xr.Dataset, 
                            voc_species: dict,
                            pm_species: dict, pm_name: str,
                            wrfinput: xr.Dataset) -> xr.Dataset:
    for pol in speciated_wrfchemi.data_vars:
        speciated_wrfchemi[pol].attrs["FieldType"] = 104
        speciated_wrfchemi[pol].attrs["MemoryOrder"] = 'XYZ'
        speciated_wrfchemi[pol].attrs["description"] = 'EMISSIONS'
        if (pol == pm_name) or (pol in pm_species.keys()):
            speciated_wrfchemi[pol].attrs["units"] = 'ug m^-2 s^-1'
        else:
            speciated_wrfchemi[pol].attrs["units"] = 'mol km^-2 hr^-1'
        speciated_wrfchemi[pol].attrs["stagger"] = ''
        speciated_wrfchemi[pol].attrs["coordinates"] = 'XLONG XLAT'
    return speciated_wrfchemi

def speciate_wrfchemi(spatial_emiss_units: xr.Dataset, 
                      voc_species: dict, pm_species: dict, 
                      cell_area: float | int,
                      wrfinput: xr.Dataset,
                      voc_name: str = "VOC", 
                      pm_name: str = "PM",
                      add_attr: bool = True) -> xr.Dataset:
    speciated_wrfchemi = speciate_emission(spatial_emiss_units,
                                           voc_name, voc_species,
                                           cell_area)
    speciated_wrfchemi = speciate_emission(speciated_wrfchemi,
                                           pm_name, pm_species,
                                           cell_area)
    if add_attr:
        speciated_wrfchemi = add_emission_attributes(speciated_wrfchemi,
                                                     voc_species, pm_species, pm_name,
                                                     wrfinput)
    return speciated_wrfchemi

