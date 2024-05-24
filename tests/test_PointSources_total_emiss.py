import os
import numpy as np
import pandas as pd
import xarray as xr
from siem.siem import PointSources


def test_PointSources_total_emiss() -> None:
    geo_path = "./data/geo_em.d02.nc"
    geo = xr.open_dataset(geo_path)
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

    pol_spc = {"SO2": 32 + 2 * 16,
               "NO2": 14 + 2 * 16, "VOC": 100, "PM": 1}

    voc_spc = {"HC2": 0.3, "ETH": 0.2, "HC8": 0.15,
               "C2OH": 0.15, "ALD": 0.2}

    pm_spc = {"PM2.5": 0.3, "PM10": 0.3, "OC": 0.2,
              "EC": 0.3}

    temporal_profile = np.random.random(24)
    my_point_source = PointSources(name="Test sources",
                                   point_path="sample_geo.csv", sep="\t",
                                   geo_path=geo_path,
                                   lat_name="LAT", lon_name="LON",
                                   pol_emiss=pol_spc,
                                   temporal_prof=temporal_profile,
                                   voc_spc=voc_spc,
                                   pm_spc=pm_spc)
    os.remove("sample_geo.csv")

    emi_report = my_point_source.report_emissions()
    no2_report = emi_report.total_emiss.loc["NO2"]

    assert isinstance(emi_report, pd.DataFrame)
    assert no2.sum() - my_point_source.total_emission("NO2") < 1e-10
    assert no2.sum() - no2_report < 1e-10

