import os
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
from siem.proxy import create_wrf_grid, configure_grid_spatial
from siem.point import create_gpd_from, create_emiss_point


def test_calculate_sum_points() -> None:
    wrf_path = "./tests/test_data/geo_em.d01.siem_test.nc"
    geo = xr.open_dataset(wrf_path)
    wrf_grid = create_wrf_grid(wrf_path,
                               save=False)
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
    point_src = create_gpd_from("sample_geo.csv")
    wrf_grid = configure_grid_spatial(wrf_grid, point_src)

    emiss_point = create_emiss_point(point_src, wrf_grid)

    os.remove("sample_geo.csv")

    assert isinstance(emiss_point, gpd.GeoDataFrame)
    assert sample.so2.sum() - emiss_point.so2.sum() < 1e-10
    assert len(wrf_grid.index) == len(emiss_point.index)
