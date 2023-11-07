import xarray as xr
import numpy as np
from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy


def test_spatiotemporal_emission() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       ["id", "x", "y", "a", "b", "urban"])
    voc_spc = {}
    pm_spc = {}

    test_source = EmissionSource("test source",
                                 1_000_000,
                                 1,
                                 {"NOX": (1, 30)},
                                 spatial_proxy,
                                 np.random.normal(1, 0.5, size=24),
                                 voc_spc,
                                 pm_spc)
    spatio_temp = test_source.spatiotemporal_emission("NOX", 1)

    nox_total_spatiotemp = spatio_temp.NOX.sum()
    nox_total_source = (sum(test_source.temporal_prof) *
                        test_source.total_emission("NOX"))

    assert isinstance(spatio_temp, xr.Dataset)
    assert len(spatio_temp.Time) == len(test_source.temporal_prof)
    assert nox_total_spatiotemp - nox_total_source <= 0.00000001


def test_spatiotemporal_emission_pol_names() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       ["id", "x", "y", "a", "b", "urban"])
    voc_spc = {}
    pm_spc = {}
    test_source = EmissionSource("test source",
                                 1_000_000,
                                 1,
                                 {"NO": (1, 30), "CO": (0.5, 28)},
                                 spatial_proxy,
                                 np.random.normal(1, 0.5, size=24),
                                 voc_spc,
                                 pm_spc)
    spatio_temp = (test_source
                   .spatiotemporal_emission(
                       test_source.pol_ef.keys(), 1
                       )
                   )

    assert isinstance(spatio_temp, xr.Dataset)
    assert len(spatio_temp.data_vars) == len(test_source.pol_ef.keys())
