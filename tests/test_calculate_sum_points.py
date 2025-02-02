import os
import numpy as np
import pandas as pd
import xarray as xr
from siem.proxy import create_wrf_grid, configure_grid_spatial
from siem.point import create_gpd_from, calculate_sum_points


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

    points_in_grid = calculate_sum_points(point_src, wrf_grid)

    os.remove("sample_geo.csv")

    assert isinstance(points_in_grid, pd.DataFrame)
    assert "geometry" not in points_in_grid.columns
    assert sample.so2.sum() - points_in_grid.so2.sum() < 1e-10
