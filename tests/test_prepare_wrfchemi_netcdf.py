from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy
from siem.wrfchemi import transform_wrfchemi_units
from siem.wrfchemi import speciate_wrfchemi
from siem.wrfchemi import prepare_wrfchemi_netcdf
import numpy as np
import xarray as xr


def test_prepare_wrfchemi_netcdf() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       ["id", "x", "y", "urban"])
    voc_species = {"HC3": 0.5, "HC5": 0.25, "HC8": 0.25}
    pm_species = {"PM10": 0.3, "PM25_I": 0.7 * 0.5, "PM25_J": 0.7 * 0.5}

    wrfinput = xr.open_dataset("./data/wrfinput_d02")
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

    speciated = test_source.spatiotemporal_emission(test_source.pol_ef.keys(),
                                                    9)
    wrfchemi = transform_wrfchemi_units(speciated, test_source.pol_ef)
    wrfchemi = speciate_wrfchemi(wrfchemi, voc_species, pm_species,
                                 9, wrfinput, "VOC", "PM")

    wrfchemi_netcdf = prepare_wrfchemi_netcdf(wrfchemi.copy(), wrfinput)

    assert isinstance(wrfchemi_netcdf, xr.Dataset)
    # assert len(wrfchemi_netcdf.Times) == 24
    # assert wrfchemi_netcdf.GRID_ID == wrfinput.GRID_ID
    # assert wrfchemi_netcdf.START_DATE == wrfinput.START_DATE
    # assert wrfchemi_netcdf.Title == "OUTPUT FROM LAPAT PREPROCESSOR"
