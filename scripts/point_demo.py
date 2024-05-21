import numpy as np
import pandas as pd
import xarray as xr
import siem.point as pt
import siem.wrfchemi as wc
import siem.temporal as tt
from siem.siem import PointSources

def create_sample_data(geogrid: xr.Dataset) -> pd.DataFrame:
    lat = np.arange(geogrid.XLAT_M.min(), geogrid.XLAT_M.max(), 0.05)
    lon = np.linspace(geogrid.XLONG_M.min(), geogrid.XLONG_M.max(), len(lat))
    so2 = np.random.random(len(lat)) * 10
    nox = np.random.random(len(lat)) * 100
    co = np.random.random(len(lat)) * 10
    pm = np.random.random(len(lat)) * 100
    voc = np.random.random(len(lat)) * 100

    sample = pd.DataFrame.from_dict({
        "LAT": lat,
        "LON": lon,
        "SO2": so2,
        "NO2": nox,
        "CO": co,
        "PM": pm,
        "VOC": voc})
    return sample


if __name__ == "__main__":
    geogrid_path = "../data/geo_em.d02.nc"
    wrfinput_path = "../data/wrfinput_d02"
    emiss_path = "../data/point_emiss.csv"
    geo = xr.open_dataset(geogrid_path)
    wrfinput = xr.open_dataset(wrfinput_path)
    # emiss = create_sample_data(geo)
    # emiss.to_csv("../data/point_emiss.csv", sep="\t")
    pol_spc = {"CO": 12 + 16, "SO2": 32 + 2 * 16,
               "NO2": 14 + 2 * 16, "VOC": 100, "PM": 1}

    voc_spc = {"HC2": 0.3, "ETH": 0.2, "HC8": 0.15,
               "C2OH": 0.15, "ALD": 0.2}

    pm_spc = {"PM2.5": 0.3, "PM10": 0.3, "OC": 0.2,
              "EC": 0.3}

    so2_factor = 1000 * 1000 / (365 * 24 * pol_spc["SO2"])
    pm_factor = 1000 * 1000 * 10 ** 6 / (3600 * 24 * 365)

    temporal_profile = np.random.random(24)
    print(len(temporal_profile))

    my_spc = PointSources(name="test source",
                          point_path=emiss_path,
                          sep="\t",
                          geo_path=geogrid_path,
                          lat_name="LAT", lon_name="LON",
                          pol_emiss=pol_spc,
                          temporal_prof=temporal_profile,
                          voc_spc=voc_spc,
                          pm_spc=pm_spc)

    week_profile = np.random.rand(7)
    a = my_spc.to_wrfchemi(wrfinput, "2024-05-10", "2024-05-15",
                           write_netcdf=True, week_profile=week_profile)
    # point = pt.point_sources_to_dataset(emiss_path, geogrid_path,
    #                                     "\t", "LAT", "LON")
    # point_spc = wc.transform_wrfchemi_units_point(point, pol_spc, 1)
    # point_spc_time = tt.split_by_time_from(point_spc, temporal_profile)
    # week_profile = np.random.rand(7)
    #
    # point_speciated = wc.speciate_wrfchemi(point_spc_time, voc_spc, pm_spc,
    #                                        1, wrfinput)
    # point_speciated = point_speciated.rename({"x": "west_east", "y": "south_north"})
    # wrfchemi_netcdf = wc.prepare_wrfchemi_netcdf(point_speciated, wrfinput)
    griddesc = "../data/GRIDDESC"
    my_cmaq = my_spc.to_cmaq(wrfinput, griddesc, 5,
                             "2024-05-10", "2024-05-15",
                             week_profile)

 
