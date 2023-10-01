from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy
from siem.wrfchemi import transform_wrfchemi_units
from siem.wrfchemi import speciate_wrfchemi
import numpy as np
import xarray as xr


def test_speciate_wrfchemi() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       ["id", "x", "y", "a", "b", "urban"])
    test_source = EmissionSource("test source",
                                 1_000_000,
                                 1,
                                 {"NOX": (1, 30),
                                  "PM": (1, 30),
                                  "VOC": (1, 100)},
                                 spatial_proxy,
                                 np.random.normal(1, 0.5, size=24))

    voc_species = {"HC3": 0.5, "HC5": 0.25, "HC8": 0.25}
    pm_species = {"PM10": 0.3, "PM25_I": 0.7 * 0.5, "PM25_J": 0.7 * 0.5}

    wrfinput = xr.Dataset()

    speciated = test_source.spatiotemporal_emission(test_source.pol_ef.keys(),
                                                    9)
    wrfchemi = transform_wrfchemi_units(speciated, test_source.pol_ef)
    wrfchemi = speciate_wrfchemi(wrfchemi, voc_species, pm_species,
                                 9, wrfinput, "VOC", "PM")

    assert isinstance(wrfchemi, xr.Dataset)
    assert wrfchemi.E_PM.units == "ug m^-2 s^-1"
    assert wrfchemi.E_PM25_I.units == "ug m^-2 s^-1"
    assert wrfchemi.E_NOX.units == "mol km^-2 hr^-1"
    assert wrfchemi.E_HC3.units == "mol km^-2 hr^-1"


def test_speciate_wrfchemi_add_attr() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       ["id", "x", "y", "a", "b", "urban"])
    test_source = EmissionSource("test source",
                                 1_000_000,
                                 1,
                                 {"NOX": (1, 30),
                                  "PM": (1, 30),
                                  "VOC": (1, 100)},
                                 spatial_proxy,
                                 np.random.normal(1, 0.5, size=24))

    voc_species = {"HC3": 0.5, "HC5": 0.25, "HC8": 0.25}
    pm_species = {"PM10": 0.3, "PM25_I": 0.7 * 0.5, "PM25_J": 0.7 * 0.5}

    wrfinput = xr.Dataset()

    speciated = test_source.spatiotemporal_emission(test_source.pol_ef.keys(),
                                                    9)
    wrfchemi = transform_wrfchemi_units(speciated, test_source.pol_ef)
    wrfchemi = speciate_wrfchemi(wrfchemi, voc_species, pm_species,
                                 9, wrfinput, "VOC", "PM", add_attr=False)

    assert wrfchemi.E_PM25_I.attrs == {}
    assert wrfchemi.E_NOX.attrs == {}
    assert wrfchemi.E_HC3.attrs != "mol km^-2 hr^-1"
    assert wrfchemi.E_PM.attrs != "ug m^-2 s^-1"

