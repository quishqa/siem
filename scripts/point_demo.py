"""
This is an example on how to use siem
for reading point sources emission files in a .csv
"""

import numpy as np
import pandas as pd
import xarray as xr
import siem.point as pt
import siem.wrfchemi as wc
import siem.temporal as tt
from siem.siem import PointSources
from siem.point import read_point_sources
import warnings

warnings.filterwarnings(
    "ignore", message="IOAPI_ISPH is assumed to be 6370000.; consistent with WRF"
)


def create_sample_data(geogrid: xr.Dataset) -> pd.DataFrame:
    lat = np.arange(geogrid.XLAT_M.min(), geogrid.XLAT_M.max(), 0.05)
    lon = np.linspace(geogrid.XLONG_M.min(), geogrid.XLONG_M.max(), len(lat))
    no = np.random.random(len(lat)) * 10
    no2 = np.random.random(len(lat)) * 100
    co = np.random.random(len(lat)) * 10
    so2 = np.random.random(len(lat)) * 10
    pm = np.random.random(len(lat)) * 100
    voc = np.random.random(len(lat)) * 100
    rcho = np.random.random(len(lat)) * 100

    sample = pd.DataFrame.from_dict(
        {
            "LAT": lat,
            "LON": lon,
            "NO": no,
            "NO2": no2,
            "SO2": so2,
            "CO": co,
            "PM": pm,
            "VOC": voc,
            "RCHO": rcho,
        }
    )
    return sample


if __name__ == "__main__":
    geogrid_path = "../data/geo_em.d01.siem_test.nc"
    wrfinput_path = "../data/wrfinput_d01_siem_test"
    emiss_path = "../data/point_emiss_veih.csv"

    geo = xr.open_dataset(geogrid_path)
    _, nrow, ncol = geo.XLAT_M.shape
    wrfinput = xr.open_dataset(wrfinput_path)

    emiss = create_sample_data(geo)
    emiss.to_csv("../data/point_emiss_veih.csv", sep="\t")
    print("saving point_emiss_veih.csv in ../data")

    pol_spc = {
        "CO": 12 + 16,
        "SO2": 32 + 2 * 16,
        "NO2": 14 + 2 * 16,
        "VOC": 100,
        "PM": 1,
    }

    voc_spc = {"HC2": 0.3, "ETH": 0.2, "HC8": 0.15, "C2OH": 0.15, "ALD": 0.2}

    pm_spc = {"PM2.5": 0.3, "PM10": 0.3, "OC": 0.2, "EC": 0.3}

    so2_factor = 1000 * 1000 / (365 * 24 * pol_spc["SO2"])
    pm_factor = 1000 * 1000 * 10**6 / (3600 * 24 * 365)

    temporal_profile = np.random.random(24)

    point_source = read_point_sources(
        point_path=emiss_path,
        geo_path=geogrid_path,
        ncol=ncol,
        nrow=nrow,
        sep="\t",
        lat_name="LAT",
        lon_name="LON",
    )

    my_spc = PointSources(
        name="test source",
        point_emiss=point_source,
        pol_emiss=pol_spc,
        temporal_prof=temporal_profile,
        voc_spc=voc_spc,
        pm_spc=pm_spc,
    )

    week_profile = np.random.rand(7)

    griddesc = "../data/GRIDDESC"

    my_cmaq = my_spc.to_cmaq(
        wrfinput,
        griddesc,
        5,
        "2024-05-10",
        "2024-05-15",
        week_profile,
        write_netcdf=True,
        path="../results/",
    )

    print("All Done")
