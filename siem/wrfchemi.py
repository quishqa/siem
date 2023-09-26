'''
Functions to create wrfchemi file
- Change units for gas and pm
- speciate
- write attributes for species
- write global attributes
- add date
'''
import xarray as xr


def transform_wrfchemi_units(spatial_emiss: xr.DataArray,
                             pol_ef_mw: dict,
                             pm_name: str = "PM") -> xr.Dataset:
    for pol_name, pol_mw in pol_ef_mw.items():
        spatial_emiss[pol_name] = spatial_emiss[pol_name] / pol_mw[1]
        if pol_name == pm_name:
            spatial_emiss[pm_name] = spatial_emiss[pm_name] / 3600
    return spatial_emiss

def speciate_wrfchemi(spatial_emiss_units: xr.Dataset, 
                      voc_species: dict, pm_species: dict, 
                      cell_area: float | int,
                      wrfinput: xr.Dataset,
                      voc_name: str = "VOC", 
                      pm_name: str = "PM") -> xr.Dataset:
    speciated_wrfchemi = speciate_emission(spatial_emiss_units,
                                           voc_name, voc_species,
                                           cell_area)
    speciated_wrfchemi = speciated_wrfchemi(speciated_wrfchemi,
                                            pm_name, pm_species,
                                            cell_area)
    return speciated_wrfchemi

def add_emission_attributes(speciated_wrfchemi, pol_ef_mw, voc_species,
                            pm_species, wrfinput):
    for pol in speciated_wrfchemi.data_vars:
        speciated_wrfchemi[pol].attrs["FieldType"] = 104
        speciated_wrfchemi[pol].attrs["MemoryOrder"] = 'XYZ'
        speciated_wrfchemi[pol].attrs["description"] = 'EMISSIONS'
        if (pol == "PM") or (pol in pm_species.keys()):
            speciated_wrfchemi[pol].attrs["units"] = 'ug m^-2 s^-1'
        else:
            speciated_wrfchemi[pol].attrs["units"] = 'mol km^-2 hr^-1'
        speciated_wrfchemi[pol].attrs["stagger"] = ''
        speciated_wrfchemi[pol].attrs["coordinates"] = 'XLONG XLAT'

        return speciated_wrfchemi


        



