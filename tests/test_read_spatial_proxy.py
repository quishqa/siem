import xarray as xr
from siem.spatial import read_spatial_proxy


def test_read_spatial_proxy_col_names() -> None:
   spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                      col_names=["id", "x", "y",
                                                 "main", "lon", "urban"])
   assert type(spatial_proxy) == type(xr.DataArray())
