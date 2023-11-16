import geopandas as gpd
import xarray as xr
from siem.proxy import create_wrf_grid


def test_create_wrf_grid() -> None:
    wrf_path = "./data/geo_em.d02.nc"
    geo = xr.open_dataset(wrf_path)
    geo_shape = geo.XLAT_M.isel(Time=0).shape
    wrf_grid = create_wrf_grid(wrf_path,
                               save=False)
    assert isinstance(wrf_grid, gpd.GeoDataFrame)
    assert wrf_grid.shape[0] == geo_shape[0] * geo_shape[1]
