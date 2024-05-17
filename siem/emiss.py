import xarray as xr


def calculate_emission(number_source: int | float,
                       activity_rate: float,
                       pol_ef: float) -> float:
    return number_source * activity_rate * pol_ef


def speciate_emission(spatio_temporal: xr.DataArray,
                      pol_name: str, pol_species: dict,
                      cell_area: int | float) -> xr.DataArray:
    for new_pol, pol_fraction in pol_species.items():
        spatio_temporal[new_pol] = spatio_temporal[pol_name] * pol_fraction
    return spatio_temporal


def ktn_year_to_mol_hr(spatial_emiss: xr.DataArray,
                       pol_mw: float) -> xr.DataArray:
    convert_factor = 1000 * 1000 / (365 * 24 * pol_mw)
    return spatial_emiss * convert_factor


def ktn_year_to_ug_seg(spatial_emiss: xr.DataArray) -> xr.DataArray:
    convert_factor = 1000 * 1000 * 10 ** 6 / (365 * 24 * 3600)
    return spatial_emiss * convert_factor


def ktn_year_to_mol_seg(spatial_emiss: xr.DataArray,
                        pol_mw: float) -> xr.DataArray:
    convert_factor = 1000 * 1000 * 1000 / (365 * 24 * 3600 * pol_mw)
    return spatial_emiss * convert_factor


def ktn_year_to_g_seg(spatial_emiss: xr.DataArray) -> xr.DataArray:
    convert_factor = 1000 * 1000 * 1000 / (365 * 24 * 3600)
    return spatial_emiss * convert_factor
