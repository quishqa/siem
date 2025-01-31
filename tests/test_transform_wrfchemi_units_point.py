import os
import numpy as np
import pandas as pd
import xarray as xr
from siem.point import read_point_sources
from siem.wrfchemi import transform_wrfchemi_units_point


def test_transform_wrfchemi_units_point() -> None:
    geo_path = "./tests/test_data/geo_em.d01.siem_test.nc"
    geo = xr.open_dataset(geo_path)
    lat = np.arange(geo.XLAT_M.min(), geo.XLAT_M.max(), 0.05)
    lon = np.linspace(geo.XLONG_M.min(), geo.XLONG_M.max(), len(lat))
    so2 = np.random.random(len(lat)) * 10
    no2 = np.random.random(len(lat)) * 100
    pm = np.random.random(len(lat)) * 100

    sample = pd.DataFrame.from_dict({
        "LAT": lat,
        "LON": lon,
        "so2": so2,
        "no2": no2,
        "PM": pm})

    sample.to_csv("sample_geo.csv", sep="\t", index=False)

    emiss_ready = read_point_sources("sample_geo.csv", geo_path,
                                     "\t", "LAT", "LON")
    os.remove("sample_geo.csv")
    pols_mw = {"no2": 28, "so2": 32 + 2 * 16, "PM": 1}
    emiss_ready_units = transform_wrfchemi_units_point(emiss_ready,
                                                       pols_mw,
                                                       1)

    pm_factor = 1000 * 1000 * 10 ** 6 / (365 * 24 * 3600)
    so2_factor = 1000 * 1000 / (365 * 24 * (32 + 2 * 16))

    assert isinstance(emiss_ready_units, xr.Dataset)
    assert (emiss_ready.so2 * so2_factor).sum() - emiss_ready_units.so2.sum() <= 1e-10
    assert (emiss_ready.PM * pm_factor).sum() - emiss_ready_units.PM.sum() <= 1e-10
