import os
import numpy as np
import pandas as pd
import xarray as xr
from siem.siem import PointSources
from siem.point import read_point_sources
from siem.wrfchemi import transform_wrfchemi_units_point


def test_PointSources() -> None:
    geo_path = "./tests/test_data/geo_em.d01.siem_test.nc"
    wrfinput_path = "./wrfpoint_emiss.csv"
    geo = xr.open_dataset(geo_path)
    _, nrow, ncol = geo.XLAT_M.shape
    lat = np.arange(geo.XLAT_M.min(), geo.XLAT_M.max(), 0.05)
    lon = np.linspace(geo.XLONG_M.min(), geo.XLONG_M.max(), len(lat))
    so2 = np.random.random(len(lat)) * 10
    no2 = np.random.random(len(lat)) * 100
    pm = np.random.random(len(lat)) * 100
    voc = np.random.random(len(lat)) * 100

    sample = pd.DataFrame.from_dict({
        "LAT": lat,
        "LON": lon,
        "SO2": so2,
        "NO2": no2,
        "PM": pm,
        "VOC": voc})

    sample.to_csv("sample_geo.csv", sep="\t", index=False)
    
    pol_spc = {"CO": 12 + 16, "SO2": 32 + 2 * 16,
               "NO2": 14 + 2 * 16, "VOC": 100, "PM": 1}

    voc_spc = {"HC2": 0.3, "ETH": 0.2, "HC8": 0.15,
               "C2OH": 0.15, "ALD": 0.2}

    pm_spc = {"PM2.5": 0.3, "PM10": 0.3, "OC": 0.2,
              "EC": 0.3}
    
    temporal_profile = np.random.random(24)
    my_point_emiss = read_point_sources(point_path="sample_geo.csv",
                                        geo_path=geo_path,
                                        ncol = ncol,
                                        nrow = nrow,
                                        sep="\t",
                                        lat_name="LAT",
                                        lon_name="LON")
    my_point_source = PointSources(name="Test sources",
                                   point_emiss=my_point_emiss,
                                   pol_emiss=pol_spc,
                                   temporal_prof=temporal_profile,
                                   voc_spc=voc_spc,
                                   pm_spc=pm_spc)
    os.remove("sample_geo.csv")
    assert(isinstance(my_point_source, PointSources))
    assert(isinstance(my_point_source.spatial_emission, xr.Dataset))
    assert len(my_point_emiss.south_north)== nrow
    assert len(my_point_emiss.west_east) == ncol
