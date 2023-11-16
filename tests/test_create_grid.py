import numpy as np
import geopandas as gpd
from siem.proxy import create_grid


def test_create_grid() -> None:
    lat = np.arange(-12, -11.1, 0.1)
    lon = np.arange(-43, -42.1, 0.1)

    grid = create_grid(lat, lon)

    assert isinstance(grid, gpd.GeoDataFrame)
    assert grid.shape[0] == (lat.shape[0] - 1) * (lon.shape[0] - 1)
