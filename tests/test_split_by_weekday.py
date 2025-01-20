import xarray as xr
import numpy as np
from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy
from siem.temporal import split_by_weekday


def test_spatiotemporal_emission() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       (24, 14),
                                       ["id", "x", "y", "urban"])
    voc_spc = {}
    pm_spc = {}

    test_source = EmissionSource("test source",
                                 1_000_000,
                                 1,
                                 {"NOX": (1, 30),
                                  "CO": (1, 28)},
                                 spatial_proxy,
                                 np.random.normal(1, 0.5, size=24),
                                 voc_spc,
                                 pm_spc)

    spatio_temp = test_source.spatiotemporal_emission(["NOX", "CO"], 1)
    week_profile = np.random.normal(1, 0.5, size=7)
    emiss_week = split_by_weekday(spatio_temp, week_profile,
                                  "2024-03-01", "2024-03-04")

    assert isinstance(emiss_week, xr.Dataset)
    assert emiss_week.sizes["Time"] == 24 * 4
