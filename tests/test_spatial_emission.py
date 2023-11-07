import xarray as xr
from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy


def test_spatial_emission() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       ["id", "x", "y", "lon", "pp", "urban"],
                                       proxy="lon")
    temporal_prof = []
    voc_spc = {}
    pm_spc = {}

    test_source = EmissionSource("test source",
                                 1_000_000,
                                 1,
                                 {"NOX": (1, 30)},
                                 spatial_proxy,
                                 temporal_prof,
                                 voc_spc,
                                 pm_spc)

    assert isinstance(test_source.spatial_emission("NOX", 1), xr.DataArray)
