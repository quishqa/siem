import xarray as xr
import numpy as np
from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy


def test_speciate_emission() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       ["id", "x", "y", "a", "b", "urban"])
    voc_species = {"HC3": 0.5, "HC5": 0.25, "HC8": 0.25}
    pm_species = {"PM10": 0.3, "PM25_I": 0.7 * 0.5, "PM25_J": 0.7 * 0.5}

    test_source = EmissionSource("test source",
                                 1_000_000,
                                 1,
                                 {"NOX": (1, 30),
                                  "PM": (1, 30),
                                  "VOC": (1, 100)},
                                 spatial_proxy,
                                 np.random.normal(1, 0.5, size=24),
                                 voc_species,
                                 pm_species)
    cell_area = 1
    speciated = test_source.speciate_all(cell_area)

    assert isinstance(speciated, xr.Dataset)
    assert np.round(speciated.PM.sum()) == np.round(speciated.PM10.sum() +
                                                    speciated.PM25_I.sum() +
                                                    speciated.PM25_J.sum())

def test_speciate_emission_cmaq() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       ["id", "x", "y", "a", "b", "urban"])
    voc_species = {"HC3": 0.5, "HC5": 0.25, "HC8": 0.25}
    pm_species = {"PM10": 0.3, "PM25_I": 0.7 * 0.5, "PM25_J": 0.7 * 0.5}

    test_source = EmissionSource("test source",
                                 1_000_000,
                                 1,
                                 {"NOX": (1, 30),
                                  "PM": (1, 30),
                                  "VOC": (1, 100)},
                                 spatial_proxy,
                                 np.random.normal(1, 0.5, size=24),
                                 voc_species,
                                 pm_species)
    cell_area = 1
    speciated = test_source.speciate_all(cell_area, is_cmaq=True)

    assert isinstance(speciated, xr.Dataset)
    assert np.round(speciated.PM.sum()) == np.round(speciated.PM10.sum() +
                                                    speciated.PM25_I.sum() +
                                                    speciated.PM25_J.sum())
    assert speciated.PM.shape[0] == 25
