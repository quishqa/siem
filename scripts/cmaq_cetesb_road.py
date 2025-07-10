# ======================== Emissions for MASP ========================
# Created by Alejandro D. Peralta
# last update Jun 11 2025
# conda activate siem
# ====================================================================

import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
import siem.point as pt
import siem.temporal as tt
from siem.siem import (PointSources, GroupSources)
from siem.point import read_point_sources
from siem.spatial import read_spatial_proxy
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore",
                        message="IOAPI_ISPH is assumed to be 6370000.; consistent with WRF")

###############################################################################
#
# This is an example to distribute emissions inventory to CMAQ model
#
###############################################################################
#
# Namelists ===================================================================
#> This inventory applies to the Metropolitan Area of São Paulo

APPL          = "3km"          # Application name (model horizontal resolution)
dom           = "d02"          # Model domain
mech          = "cmaq_cb6ae7"  # Speciation mechanism name
GridName      = "RMSP"         # Should match with GRIDDESC to implement    
tipo          = "roads"        # Area-line emission sources
scen          = 'cetesb'       # Scenario of emission factors and fleet
frac_exh      = 0.7765         # PM2.5 fraction in exhaust 
frac_res      = 0.2419         # PM2.5 fraction in resuspension 
fleet_domain  = 7_284_990      # Fleet circulation in the model domain
fleet_cetesb  = 7_284_990      # Fleet circulation according to CETESB
frac_ldv      = 0.936382       # LDV fraction in São Paulo State
frac_hdv      = 1- frac_ldv    # HDV fraction in São Paulo State
gaso_frac     = 0.335738       # Fraction of gasohol from LDV                    
etha_frac     = 0.015567       # Fraction of ethanol from LDV            
flex_frac     = 0.648695       # Fraction of flex from LDV               
etha_flex     = 0.50           # Fraction of flex-fuel (hydrated ethanol)
gaso_flex     = 1 - etha_flex  # Fraction of flex-fuel (gasohol)
date_start    = "2018-05-01"
date_end      = "2018-05-02"

# Reading data ================================================================
proj_path     = '/your_path/of_your/project/data/'          # < --- EDIT HERE
hdv_csv       = 'highways_hdv_'+dom+'.csv'
ldv_csv       = 'highways_ldv_'+dom+'.csv'
geo           = xr.open_dataset(proj_path + 'geo_em.'+dom+'.nc')
west_east     = len(geo.west_east)
south_north   = len(geo.south_north)
proxy_ldv     = read_spatial_proxy(proj_path + ldv_csv, (west_east, south_north))
proxy_hdv     = read_spatial_proxy(proj_path + hdv_csv, (west_east, south_north))
wrfinput      = xr.open_dataset(proj_path + "wrfinput_"+dom, engine= "scipy")
daily_profile = pd.read_csv(proj_path + "daily_profile_sum.csv")   # Sum  1 (columns ldv, hdv)
week_profile  = pd.read_csv(proj_path + "week_profile.csv")        # Mean 1 (frac) 

#> Molecular weight (g mol^-1)-------------------------------------------------                                                  
mol_w = {"CO"    : 12+16,                 # Carbon monoxide                     
         "NO"    : 14+12,                 # Nitrogen oxide    
         "NO2"   : 14+12*2,               # Nitrogen dioxide    
         "SO2"   : 32+16*2,               # Sulfur dioxide                      
         "VOC"   : 100,                   # Volatile Organic Compounds          
         "VOC_INV":1,                     #                                     
         "PM"    : 1,                     # Particulate matter                  
        }

# =============================================================================
# Total emissions in kt/year in the modeling domain area
# =============================================================================
print(f"Processing emissions for {scen}.")

inv   = pd.DataFrame.from_dict(# Units are in Gg (gigagrams or kilotonnes)
            columns = [     'ldv',     'hdv' ],
            data    = {#---------| -----------
            'CO'    : [   50.0000,    25.000 ],
            'NO'    : [   95.0000,   150.000 ],
            'NO2'   : [   10.0000,    15.000 ],
            'SO2'   : [    1.0000,     2.000 ],
            'VOC'   : [   50.0000,    10.000 ],
            'PM'    : [    1.0000,     3.000 ]
            }, orient = 'index'
)

inv.loc['VOC_INV']  = inv.loc['VOC', :]

# Emissions to domain fleet circulation
inv *= fleet_domain / fleet_cetesb

# to normalize for spatial distribution (each proxy sum to 1) !!! IMPORTANT ¡¡¡        
proxy_ldv /= proxy_ldv.sum()
proxy_hdv /= proxy_hdv.sum()

# -----------------------------------------------------------------------------
# Point emissions require xr.Dataset(), so we calculate from each xr.DataArray()
# -----------------------------------------------------------------------------

exh_ldv_src = xr.Dataset({para:inv.loc[para,'ldv'] * proxy_ldv for para in inv.index})
exh_hdv_src = xr.Dataset({para:inv.loc[para,'hdv'] * proxy_hdv for para in inv.index})

# =============================================================================
print(f"Emission speciation for VOC and PM by fuel and vehicle for {scen}")
# =============================================================================
# Edit here your chemical speciation

# VOC exhaust speciation ------------------------------------------------------
voc_spc_exh = pd.DataFrame.from_dict(# CB6 mechanism
    #                 ------ (mol/100 g VOC) --------
    #                 LDV                 HDV
    #                 Gas-E25   Eth95     Diesel B10
    columns =        ['gaso' ,  'etha',  'diesel'],
    data={ #         ---------------------------------
        'ETHA':       [0.2826,  0.0000,  0.0000  ],
        'PRPA':       [0.4352,  0.0000,  0.0490  ],
        'PAR':        [0.4630,  1.1300,  0.4430  ],
        'OLE':        [0.0765,  0.0000,  0.2966  ],
        'ETH':        [0.3416,  0.9489,  0.3189  ],
        'ETOH':       [0.6051,  0.0000,  0.0000  ],
        'FORM':       [0.0211,  0.0164,  0.0585  ],
        'ALD2':       [0.0196,  0.0318,  0.0399  ],
        'TOL':        [0.1405,  0.0151,  0.2351  ],
        'XYLMN':      [0.1575,  0.0395,  0.0084  ],
        'ALDX':       [0.1291,  0.0000,  0.0000  ],
        'BENZ':       [0.0384,  0.0000,  0.0142  ],
        'IOLE':       [0.0196,  0.0000,  0.0196  ],
          },
    orient='index'
    )

# Emission speciation for particulate matter ----------------------------------
pm_spc_exh = {
          "PMC"   : 1 - frac_exh,
          "POC"   : 0.240   * frac_exh,
          "PEC"   : 0.380   * frac_exh,
          "PSO4"  : 0.03    * frac_exh,
          "PNO3"  : 0.012   * frac_exh,
          "PMOTHR": 0.338   * frac_exh,
          }

# =============================================================================
# Emission calculations (PointSources function)                    ok rev by AD  
# =============================================================================
# 1. LDV        -> Gasohol, Ethanol, Flex
# 2. HDV        -> Diesel

gaso_exh = PointSources(name = "LDV_exh_gasohol",
                        point_emiss = exh_ldv_src * (gaso_frac+flex_frac*gaso_flex),
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_spc_exh.gaso.to_dict(),
                        pm_spc = pm_spc_exh)

etha_exh = PointSources(name = "LDV_exh_ethanol",
                        point_emiss = exh_ldv_src * (etha_frac+flex_frac*etha_flex),
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_spc_exh.etha.to_dict(),
                        pm_spc = pm_spc_exh)

hdv_exh = PointSources(name = "HDV with diesel",
                        point_emiss = exh_hdv_src,
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.hdv,
                        voc_spc = voc_spc_exh.diesel.to_dict(),
                        pm_spc = pm_spc_exh)

# =============================================================================
# Merge sources using the GroupSources function
# ============================================================================= 
road_sources  = GroupSources(sources_list = [gaso_exh, hdv_exh])

road_emiss    =  road_sources.to_cmaq(wrfinput = wrfinput,
                                      griddesc_path = proj_path + f"GRIDDESC_{GridName}",
                                      btrim =  0,
                                      start_date = date_start,
                                      end_date = date_end,
                                      week_profile = week_profile.frac,
                                      write_netcdf = True,
                                      path = "../results/" +GridName+'_'+APPL + '_'+ scen + '_' + tipo
                                      )
