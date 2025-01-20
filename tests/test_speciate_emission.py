import xarray as xr
import numpy as np
from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy


def test_speciate_emission() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       (24, 14),
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

    speaciate_emiss = test_source.speciate_emission("NOX",
                                                    {"NO": 0.9,
                                                     "NO2": 0.1},
                                                    1)

    nox_total = speaciate_emiss.NOX.sum()
    no_total = speaciate_emiss.NO.sum()
    no2_total = speaciate_emiss.NO2.sum()

    assert isinstance(speaciate_emiss, xr.Dataset)
    assert np.round(nox_total) == np.round(no_total + no2_total)
