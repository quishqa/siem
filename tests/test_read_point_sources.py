import os
import numpy as np
import pandas as pd
import xarray as xr
from siem.point import read_point_sources


def test_read_point_sources() -> None:
    geo_path = "./tests/test_data/geo_em.d01.siem_test.nc"
    geo = xr.open_dataset(geo_path)
    _, nrow, ncol = geo.XLAT_M.shape
    # Testing points outside domain
    lat = np.arange(geo.XLAT_M.min() + 2.5, geo.XLAT_M.max() + 2.5, 0.05)
    lon = np.linspace(geo.XLONG_M.min() + 2.5, geo.XLONG_M.max() + 2.5, len(lat))
    so2 = np.random.random(len(lat)) * 10
    no2 = np.random.random(len(lat)) * 100

    sample = pd.DataFrame.from_dict({
        "LAT": lat,
        "LON": lon,
        "so2": so2,
        "no2": no2})

    sample.to_csv("sample_geo.csv", sep="\t", index=False)

    emiss_ready = read_point_sources("sample_geo.csv", geo_path,
                                     ncol, nrow,
                                     "\t", "LAT", "LON")
    os.remove("sample_geo.csv")

    assert isinstance(emiss_ready, xr.Dataset)
    assert emiss_ready.no2.sum().values - sample.no2.sum() <= 1e-10
    assert emiss_ready.so2.sum().values - sample.no2.sum() <= 1e-10
