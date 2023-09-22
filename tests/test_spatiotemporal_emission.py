import xarray as xr
import numpy as np
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
                                 np.random.normal(1, 0.5, size=24))
    spatio_temp = test_source.spatiotemporal_emission("NOX", 1)

    assert isinstance(spatio_temp, xr.DataArray)
    assert len(spatio_temp.Time) == len(test_source.temporal_prof)

                                 


