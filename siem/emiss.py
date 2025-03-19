# siem/emiss.py
"""Calculate emission totals.

This module provide functions to calculate emissions rates.

The module contains the following functions:
    - `calculate_emission(number_source, use_intensity, pol_ef)` - Returns: the emission rate.
    - `speciate_emission(spatio_temporal, pol_name, pol_species)` - Returns: speciated pollutant (VOC or PM).
    - `ktn_year_to_mol_hr(spatial_emiss, pol_mw)` - Returns: emissions in mol hr^-1.
    - `ktn_year_to_ug_seg(spatial_emiss)` - Returns: emissions in ug s^-1.
    - `ktn_year_to_mol_seg(spatial_emiss, pol_mw)` - Returns: emissions in mol s^-1.
    - `ktn_year_to_g_seg(spatial_emiss)` - Returns: emissions in g s^-1.
"""

import typing
import xarray as xr


def calculate_emission(number_source: int | float,
                       use_intensity: float,
                       pol_ef: float) -> float:
    """Calculate pollutant total emission. Be aware of units.

    Args:
        number_source: Number of emission sources.
        use_intensity: Activity rate.
        pol_ef: Emission factor.

    Returns:
        Total pollutant emissions.
    """
    return number_source * use_intensity * pol_ef


def speciate_emission(spatio_temporal: xr.DataArray,
                      pol_name: str, pol_species: typing.Dict[str, float],
                      cell_area: int | float) -> xr.Dataset:
    """Speciate pollutant emission into other pollutant species.

    Args:
        spatio_temporal: Spatial distribution of pollutant to speciate.
        pol_name: Name of pollutant to speciate.
        pol_species: Keys are the new species and values the fraction of pol_name.
        cell_area: Cell area of wrfinput.

    Returns:
        Speciated emissions.
    """
    for new_pol, pol_fraction in pol_species.items():
        spatio_temporal[new_pol] = spatio_temporal[pol_name] * pol_fraction
    return spatio_temporal

# For WRF-Chem


def ktn_year_to_mol_hr(spatial_emiss: xr.DataArray,
                       pol_mw: float) -> xr.DataArray:
    """Ktn per year to mol per hour.

    Transform pollutant total emission from kTn or Gg per year
    to mol hr^-1. This is mainly used for gases species of
    Point sources.

    Args:
        spatial_emiss: Spatial pollutant total emission in kTn year^-1.
        pol_mw : Pollutant specie molecular weight. 
    Returns:
        Total emission in mol hr^-1.
    """
    convert_factor = 1000 * 1000 * 1000 / (365 * 24 * pol_mw)
    return spatial_emiss * convert_factor


def ktn_year_to_ug_seg(spatial_emiss: xr.DataArray) -> xr.DataArray:
    """Ktn per year to ug per second.

    Transform pollutant total emission in kTn or (Gg) to microgram per second.
    Mainly use for aerosol species in Point sources.

    Args:
        spatial_emiss: Spatial pollutant total emission in kTn year^-1.

    Returns:
        Total emission in ug s^-1.
    """
    convert_factor = 1000 * 1000 * 1000 * 10 ** 6 / (365 * 24 * 3600)
    return spatial_emiss * convert_factor

# For CMAQ


def ktn_year_to_mol_seg(spatial_emiss: xr.DataArray,
                        pol_mw: float) -> xr.DataArray:
    """Ktn per year to mol per second.

    Transform pollutant total emission from kTn or Gg per year
    to mol s^-1. This is mainly used for gases species of
    Point sources.

    Args:
        spatial_emiss: Spatial pollutant total emission in kTn year^-1.
        pol_mw: Pollutant molecular weight.

    Returns:
        Total emission in mol s^-1.
    """
    convert_factor = 1000 * 1000 * 1000 / (365 * 24 * 3600 * pol_mw)
    return spatial_emiss * convert_factor


def ktn_year_to_g_seg(spatial_emiss: xr.DataArray) -> xr.DataArray:
    """Ktn per year to gram per second.

    Transform pollutant total emission in kTn or (Gg) to grams per second.
    Mainly use for aerossol species in Point sources.

    Args:
        spatial_emiss: Spatial pollutant total emission in kTn year^-1.

    Returns:
        Total emission in ug s^-1.
    """
    convert_factor = 1000 * 1000 * 1000 / (365 * 24 * 3600)
    return spatial_emiss * convert_factor
