import xarray as xr
from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy


def test_spatial_emission() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       ["id", "x", "y", "a", "b", "urban"])
    test_source = EmissionSource("test source",
                                 1_000_000,
                                 1,
                                 {"NOX": 1},
                                 spatial_proxy,
                                 [])

    assert isinstance(test_source.spatial_emission("NOX", 1), xr.DataArray)

                                 


