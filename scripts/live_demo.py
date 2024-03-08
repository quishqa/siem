import xarray as xr
from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy

wrfinput_1km = xr.open_dataset("../data/wrfinput_d02") 
spatial_ldv = read_spatial_proxy("../data/highways_ldv.csv",
                                 ["id", "x", "y", "lon"],
                                 proxy="lon")
spatial_points = read_spatial_proxy("../data/points_fuel.csv",
                                    ["id", "x", "y", "n_points"],
                                    proxy="n_points")
spatial_hdv = read_spatial_proxy("../data/highways_hdv.csv",
                                 ["id", "x", "y", "lon"],
                                 proxy="lon")
# Vamos criar as emissões do gasolina ldv
gaso_ef = {"CO": (0.173, 28), "NOX": (0.01, 28), "VOC": (0.012, 100),
           "PM": (0.001, 1)}
gaso_voc = {"HC6": 0.5, "HC5": 0.3, "OLE2": 0.2, "ETH": 0.1}
gaso_pm = {"BC": 0.5, "EC": 0.3, "ORGI": 0.2, "ORGJ": 0.3}

import random
gaso_emiss = EmissionSource("Veiculos ldv gasolina exh",
                            number=1_483_236,
                            use_intensity=41.09,
                            pol_ef=gaso_ef,
                            spatial_proxy=spatial_ldv,
                            temporal_prof=[random.uniform(0, 1) for  i in range(24)],
                            voc_spc=gaso_voc,
                            pm_spc=gaso_pm)

truck_ef = {"CO": (0.266, 28), "NOX": (1.637, 28), "VOC": (0.022, 100), "CO2": (5, 12 + 36),
           "PM": (0.018, 1)}
truck_voc = {"HC6": 0.5, "HC5": 0.3, "OLE2": 0.2, "ETH": 0.1, "TOL": 0.1}
truck_pm = {"BC": 0.5, "EC": 0.3, "ORGI": 0.2, "ORGJ": 0.3}

fc = 0.7
truck_emiss = EmissionSource("Truck diesel",
                             number=48_807 *  fc,
                             use_intensity=164.38,
                             pol_ef=truck_ef,
                             temporal_prof=[random.uniform(0, 1) for i in range(24)],
                             spatial_proxy=spatial_hdv,
                             pm_spc=truck_pm,
                             voc_spc=truck_voc)

res_ef = {"VOC": (0, 100), "PM": (0.7, 1)}
res_pm = {"PM10": 0.5, "SO4": 0.2}

ressuspension = EmissionSource("resuspensao",
                             number= gaso_emiss.number,
                             use_intensity=164.38,
                             pol_ef=res_ef,
                             temporal_prof=[random.uniform(0, 1) for i in range(24)],
                             spatial_proxy=spatial_hdv,
                             pm_spc=res_ef,
                             voc_spc=gaso_ef)

ressuspension = EmissionSource("resuspensao",
                             number= gaso_emiss.number,
                             use_intensity=164.38, # nivel_atividade
                             pol_ef=res_ef,
                             temporal_prof=[random.uniform(0, 1) for i in range(24)],
                             spatial_proxy=spatial_hdv,
                             pm_spc=res_ef,
                             voc_spc=gaso_ef)





from siem.siem import GroupSources

my_emiss = GroupSources([gaso_emiss, truck_emiss])





