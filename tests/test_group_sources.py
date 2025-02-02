from siem.siem import EmissionSource
from siem.siem import GroupSources
from siem.spatial import read_spatial_proxy
from siem.wrfchemi import transform_wrfchemi_units
from siem.wrfchemi import speciate_wrfchemi
from siem.wrfchemi import prepare_wrfchemi_netcdf
import numpy as np
import netCDF4
import xarray as xr


def test_group_sources() -> None:
    spatial_proxy = read_spatial_proxy("./tests/test_data/highways_hdv.csv",
                                       (24, 14),
                                       ["id", "x", "y", "urban"])
    voc_species = {"HC3": 0.5, "HC5": 0.25, "HC8": 0.25}
    pm_species = {"PM10": 0.3, "PM25_I": 0.7 * 0.5, "PM25_J": 0.7 * 0.5}

    wrfinput = xr.open_dataset("./tests/test_data/wrfinput_d01_siem_test")

    test_source_one = EmissionSource("test source1",
                                     1_000_000,
                                     1,
                                     {"NOX": (1, 30),
                                      "PM": (1, 30),
                                      "VOC": (1, 100)},
                                     spatial_proxy,
                                     np.random.normal(1, 0.5, size=24),
                                     voc_species,
                                     pm_species)

    test_source_two = EmissionSource("test source2",
                                     1_000_000,
                                     1,
                                     {"NOX": (1, 30),
                                      "PM": (1, 30),
                                      "VOC": (1, 100)},
                                     spatial_proxy,
                                     np.random.normal(1, 0.5, size=24),
                                     voc_species,
                                     pm_species)
    test_source_three = EmissionSource("test source3",
                                       1_000_000,
                                       1,
                                       {"NOX": (1, 30),
                                        "PM": (1, 30),
                                        "VOC": (1, 100)},
                                       spatial_proxy,
                                       np.random.normal(1, 0.5, size=24),
                                       voc_species,
                                       pm_species)
    sources_list = [test_source_one, test_source_two, test_source_three]
    sources = GroupSources(sources_list)

    assert sources.names() == ["test source1", "test source2", "test source3"]
