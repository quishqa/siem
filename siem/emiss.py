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
        

