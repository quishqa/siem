import xarray as xr
import numpy as np
from siem.siem import EmissionSource
from siem.siem import GroupSources
from siem.spatial import read_spatial_proxy
from siem.cmaq import prepare_netcdf_cmaq

spatial_proxy = read_spatial_proxy("../data/highways_hdv.csv",
                                   ["id", "x", "y", "longKm"], proxy="longKm")
wrfinput = xr.open_dataset("../data/wrfinput_d02")

temporal_profile = [0.019, 0.012, 0.008, 0.004, 0.003, 0.003,
                    0.006, 0.017, 0.047, 0.074, 0.072, 0.064,
                    0.055, 0.052, 0.051, 0.048, 0.052, 0.057,
                    0.068, 0.087, 0.085, 0.057, 0.035, 0.034]
week_profile = [1.02, 1.01, 1.02, 1.03, 1.03, 0.99, 0.9]

gasoline_ef = {"CO": (0.173, 28), "VOC": (0.012, 100), "NO": (0.010 * .9, 30),
               "NO2": (0.010 * .1, 64), "RCHO": (0.0005, 32), "PM": (0.001, 1)}

flex_gasol_ef = {"CO": (0.253, 28), "VOC": (0.019, 100), "NO": (0.012 * .9, 30),
                 "NO2": (0.012 * .1, 64), "RCHO": (0.001, 32), "PM": (0.001, 1)}

flex_ethanol_ef = {"CO": (0.338, 28), "VOC": (0.047, 100), "NO": (0.012 * .9, 30),
                   "NO2": (0.012 * .1, 64), "RCHO": (0.0067, 32), "PM": (0.000, 1)}


gas_voc_exa = {"ETH": 0.282625, "HC3": 0.435206, "HC5": 0.158620,
               "HC8": 0.076538, "OL2": 0.341600, "OLT": 0.143212,
               "OLI": 0.161406, "ISO": 0.004554, "TOL": 0.140506,
               "XYL": 0.157456, "KET": 0.000083, "CH3OH": 0.001841}

pm_exa = {"PM25I": 0.670 * 0.193 * 0.250,
          "PM25J": 0.670 * 0.193 * 0.750,
          "SO4I": 0.670 * 0.027 * 0.136,
          "SO4J": 0.670 * 0.027 * 0.864,
          "NO3I": 0.670 * 0.015 * 0.230,
          "NO3J": 0.670 * 0.015 * 0.770,
          "ORGI": 0.670 * 0.436 * 0.190,
          "ORGJ": 0.670 * 0.436 * 0.810,
          "ECI": 0.670 * 0.940 * 0.940,
          "ECJ": 0.670 * 0.940 * 0.060,
          "PM10": 0.330,
          "SO4C": 0.0, "NO3C": 0.0,
          "ORGC": 0.0, "ECC": 0.0}

gasoline_vehicles = EmissionSource("Gasoline vehicles",
                                   2_686_528,
                                   13_495 / 365,
                                   gasoline_ef,
                                   spatial_proxy,
                                   temporal_profile,
                                   gas_voc_exa,
                                   pm_exa)

emiss = gasoline_vehicles.speciate_all(1, is_cmaq=True)

emiss_cmaq = prepare_netcdf_cmaq(emiss, "2018-07-01", "../data/GRIDDESC",
                                 6,
                                 gas_voc_exa, pm_exa)
