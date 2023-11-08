from siem.siem import EmissionSource
from siem.siem import GroupSources
from siem.spatial import read_spatial_proxy
import numpy as np
import xarray as xr


def test_group_sources() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       ["id", "x", "y", "a", "b", "urban"])
    voc_species = {"HC3": 0.5, "HC5": 0.25, "HC8": 0.25}
    pm_species = {"PM10": 0.3, "PM25_I": 0.7 * 0.5, "PM25_J": 0.7 * 0.5}

    wrfinput = xr.open_dataset("./data/wrfinput_d01")
    temp_prof = np.random.normal(1, 0.5, size=24)

    test_source_one = EmissionSource("test source1",
                                     1_000_000,
                                     1,
                                     {"NOX": (1, 30),
                                      "PM": (1, 30),
                                      "VOC": (1, 100)},
                                     spatial_proxy,
                                     temp_prof,
                                     voc_species,
                                     pm_species)

    test_source_two = EmissionSource("test source2",
                                     1_000_000,
                                     1,
                                     {"NOX": (1, 30),
                                      "PM": (1, 30),
                                      "VOC": (1, 100)},
                                     spatial_proxy,
                                     temp_prof,
                                     voc_species,
                                     pm_species)

    test_source_three = EmissionSource("test source3",
                                       1_000_000,
                                       1,
                                       {"NOX": (1, 30),
                                        "PM": (1, 30),
                                        "VOC": (1, 100)},
                                       spatial_proxy,
                                       temp_prof,
                                       voc_species,
                                       pm_species)

    cell_area = 9
    test1 = test_source_one.to_wrfchemi(cell_area, wrfinput)

    sources_list = [test_source_one, test_source_two, test_source_three]
    sources = GroupSources(sources_list)
    wrfchemi = sources.to_wrfchemi(cell_area, wrfinput)

    assert len(wrfchemi.dims) == 5
    assert "source" in wrfchemi.dims
    assert (test1.E_NOX.sum() * 3).values == wrfchemi.E_NOX.sum(dim="source").sum().values




