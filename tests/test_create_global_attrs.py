import os
import numpy as np
from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy
from siem.cmaq import prepare_netcdf_cmaq
from siem.cmaq import create_global_attrs


def test_create_global_attrs() -> None:
    spatial_proxy = read_spatial_proxy("./tests/test_data/highways_hdv.csv",
                                       (24, 14),
                                       ["id", "x", "y", "a", "b", "urban"])
    voc_species = {"HC3": 0.5, "HC5": 0.25, "HC8": 0.25}
    pm_species = {"PM10": 0.3, "PM25_I": 0.7 * 0.5, "PM25_J": 0.7 * 0.5}

    test_source = EmissionSource("test source",
                                 1_000_000,
                                 1,
                                 {"NOX": (1, 30),
                                  "PM": (1, 30),
                                  "VOC": (1, 100)},
                                 spatial_proxy,
                                 np.random.normal(1, 0.5, size=24),
                                 voc_species,
                                 pm_species)
    cell_area = 1
    speciated = test_source.speciate_all(cell_area, is_cmaq=True)
    speciated_attrs = prepare_netcdf_cmaq(speciated, "2018-07-01",
                                          "./tests/test_data/GRIDDESC", 6,
                                          voc_species,
                                          pm_species,
                                          pm_name="PM", voc_name="VOC")

    global_attrs = create_global_attrs(speciated_attrs, "./tests/test_data/GRIDDESC")

    assert isinstance(global_attrs, dict)
    assert len(global_attrs.keys()) == 33
    assert len(global_attrs["FILEDESC"]) == 80
    assert len(global_attrs["VAR-LIST"]) == 16 * 7
    assert global_attrs["GDTYP"] == 7
