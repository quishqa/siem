from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy

spatial_proxy = read_spatial_proxy("../data/ldv_s3.txt",
                                   ["id", "x", "y", "lon", "pp", "urban"],
                                   proxy="lon")

temporal_profile = [0.019, 0.012, 0.008, 0.004, 0.003, 0.003,
                    0.006, 0.017, 0.047, 0.074, 0.072, 0.064,
                    0.055, 0.052, 0.051, 0.048, 0.052, 0.057,
                    0.068, 0.087, 0.085, 0.057, 0.035, 0.034]

gasoline_vehicles = EmissionSource("Gasoline vehicles",
                                   2_686_528,
                                   13_495 / 365,
                                   {"NOX": 0.01, "CO": 0.173},
                                   spatial_proxy,
                                   temporal_profile)
                                    

