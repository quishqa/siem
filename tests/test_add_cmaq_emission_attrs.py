import xarray as xr
import numpy as np
from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy
from siem.cmaq import add_cmaq_emission_attrs


def test_add_cmaq_emission_attrs() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
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
    speciated_attrs = add_cmaq_emission_attrs(speciated,
                                              voc_species,
                                              pm_species,
                                              pm_name="PM", voc_name="VOC")

    assert isinstance(speciated_attrs, xr.Dataset)
    assert "PM" not in speciated_attrs.data_vars
    assert "VOC" not in speciated_attrs.data_vars
    assert speciated_attrs.NOX.units == "moles/s"
    assert speciated_attrs.PM10.units == "g/s"
    assert len(speciated_attrs.PM10.var_desc) == 80
    assert len(speciated_attrs.PM10.long_name) == 16
