from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy

spatial_proxy = read_spatial_proxy("../data/ldv_s3.txt",
                                   ["id", "x", "y", "lon", "pp", "urban"],
                                   proxy="lon")

gasoline_vehicles = EmissionSource("Gasoline vehicles",
                                   2_686_528,
                                   13_495 / 365,
                                   {"NOX": 0.01},
                                   spatial_proxy,
                                   [])
                                    

