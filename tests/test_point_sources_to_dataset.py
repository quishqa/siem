import os
import numpy as np
import pandas as pd
import xarray as xr
from siem.point import point_sources_to_dataset


def test_calculate_centroid() -> None:
    geo_path = "./data/geo_em.d02.nc"
    geo = xr.open_dataset(geo_path)
    lat = np.arange(geo.XLAT_M.min(), geo.XLAT_M.max(), 0.05)
    lon = np.linspace(geo.XLONG_M.min(), geo.XLONG_M.max(), len(lat))
    so2 = np.random.random(len(lat)) * 10
    no2 = np.random.random(len(lat)) * 100

    sample = pd.DataFrame.from_dict({
        "LAT": lat,
        "LON": lon,
        "so2": so2,
        "no2": no2})

    sample.to_csv("sample_geo.csv", sep="\t", index=False)

    emiss_ready = point_sources_to_dataset("sample_geo.csv", geo_path,
                                           "\t", "LAT", "LON")
    os.remove("sample_geo.csv")

    assert isinstance(emiss_ready, xr.Dataset)
    assert emiss_ready.no2.sum().values - sample.no2.sum() <= 1e-10
    assert emiss_ready.so2.sum().values - sample.no2.sum() <= 1e-10
