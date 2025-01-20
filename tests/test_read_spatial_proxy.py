import xarray as xr
from siem.spatial import read_spatial_proxy


def test_read_spatial_proxy_col_names() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       (24, 14),
                                       col_names=["id", "x", "y", "lon"],
                                       proxy="lon")
    assert isinstance(spatial_proxy, xr.DataArray)
    assert spatial_proxy.min() >= 0.0
