import xarray as xr

def transform_wrfchemi_units(spatial_emiss: xr.DataArray,
                             pol_ef_mw: dict, 
                             pm_name: str = "PM") -> xr.Dataset:
    for pol_name, (pol_ef, pol_mw) in pol_ef_mw.items():
        spatial_emiss[pol_name] = spatial_emiss[pol_name] / pol_mw
        if pol_name == pm_name:
            spatial_emiss[pm_name] = spatial_emiss[pm_name] / 3600
    return spatial_emiss


