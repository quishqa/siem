import os
import numpy as np
from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy
from siem.cmaq import prepare_netcdf_cmaq
from siem.cmaq import create_cmaq_file_name


def test_create_cmaq_file_name() -> None:
    spatial_proxy = read_spatial_proxy("./tests/test_data/highways_hdv.csv",
                                       (24, 14),
                                       ["id", "x", "y", "a", "b", "urban"])
    voc_species = {"HC3": 0.5, "HC5": 0.25, "HC8": 0.25}
    pm_species = {"PM10": 0.3, "PM25_I": 0.7 * 0.5, "PM25_J": 0.7 * 0.5}

    with open('GRIDDESC', 'w') as gf:
        gf.write(
           "' '\n'LamCon_40N_97W'\n 2 33.000 45.000 -97.000 -97.000 40.000\n" +
           "' '\n'12US1'\n'LamCon_40N_97W' " +
           "-2556000.0 -1728000.0 12000.0 12000.0 459 299 1\n' '"
        )

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
    _, ori_row, ori_col = speciated.PM10.shape

    n_point = 6
    speciated_attrs = prepare_netcdf_cmaq(speciated, "2018-07-01",
                                          "GRIDDESC", n_point,
                                          voc_species,
                                          pm_species,
                                          pm_name="PM", voc_name="VOC")
    file_name = create_cmaq_file_name(speciated_attrs)

    os.remove("GRIDDESC")

    assert file_name == "cmaq_emissions_20180701.nc"
