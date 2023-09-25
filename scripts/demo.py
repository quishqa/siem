from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy

spatial_proxy = read_spatial_proxy("../data/ldv_s3.txt",
                                   ["id", "x", "y", "lon", "pp", "urban"],
                                   proxy="lon")

temporal_profile = [0.019, 0.012, 0.008, 0.004, 0.003, 0.003,
                    0.006, 0.017, 0.047, 0.074, 0.072, 0.064,
                    0.055, 0.052, 0.051, 0.048, 0.052, 0.057,
                    0.068, 0.087, 0.085, 0.057, 0.035, 0.034]

gasoline_ef = {"CO": 0.173, "VOC": 0.012, "NOX": 0.010,
               "RCHO": 0.0005, "PM": 0.001}

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
                                   temporal_profile)

emiss = gasoline_vehicles.speciate_emission("NOX", {"NO": 0.9, "NO2": 0.1},
                                            9)

