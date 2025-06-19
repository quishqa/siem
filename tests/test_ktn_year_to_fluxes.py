import os
import numpy as np
import pandas as pd
import xarray as xr
from siem.point import read_point_sources
from siem.emiss import ktn_year_to_g_day
from siem.wrfchemi import transform_wrfchemi_units_point

def test_calculate_centroid() -> None:
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
        "SO2": so2,
        "NO2": no2,
        "PM": pm})

    sample.to_csv("sample_geo.csv", sep="\t", index=False)

    emiss_ready = read_point_sources("sample_geo.csv", geo_path,
                                     "\t", "LAT", "LON")
    os.remove("sample_geo.csv")

    so2 = emiss_ready["SO2"]
    so2_mw = 32 + 2 * 16
    convert_factor = 1E9 / 365           # ktn year^-1 to g day^-1 
    so2_g_day = ktn_year_to_g_day(so2)

    pm_emi = emiss_ready["PM"]
    pm_g_day = ktn_year_to_g_day(pm_emi)

    assert isinstance(so2_g_day, xr.DataArray)
    assert isinstance(pm_g_day, xr.DataArray)
    assert (so2 * convert_factor).sum() - so2_g_day.sum() <= 1e-10
    assert (pm_emi * convert_factor).sum() - pm_g_day.sum() <= 1e-10
