from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy
from siem.wrfchemi import transform_wrfchemi_units
import numpy as np
import xarray as xr


def test_transform_wrfchemi_units() -> None:
    spatial_proxy = read_spatial_proxy("./tests/test_data/highways_hdv.csv",
                                       (24, 14),
                                       ["id", "x", "y", "a", "b", "urban"])
    voc_spc = {}
    pm_spc = {}
    test_source = EmissionSource("test source",
                                 1_000_000,
                                 1,
                                 {"NOX": (1, 30),
                                  "PM": (1, 30),
                                  "VOC": (1, 100)},
                                 spatial_proxy,
                                 np.random.normal(1, 0.5, size=24),
                                 voc_spc,
                                 pm_spc)

    speciated = test_source.spatiotemporal_emission(test_source.pol_ef.keys(),
                                                    9)
    speciated_copy = speciated.copy()
    wrfchemi = transform_wrfchemi_units(speciated_copy, test_source.pol_ef)

    assert isinstance(wrfchemi, xr.Dataset)
    assert np.round(speciated.NOX.sum() / 30) == np.round(wrfchemi.NOX.sum())


