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
# This is an example to distribute emissions inventory to the WRF-Chem model
#
###############################################################################

# Namelists ===================================================================
#> This inventory applies to the Metropolitan Area of São Paulo

APPL          = "3km"          # Application name (model horizontal resolution)
dom           = "d02"          # Model domain
mech          = "cbmz_mosaic"  # Speciation mechanism name
GridName      = "RMSP"         # Grid name as optional
tipo          = "roads"        # Area-line emission sources
scen          = 'cetesb'       # Scenario of emission factors and fleet
frac_exh      = 0.7765         # PM2.5 fraction in exhaust 
frac_res      = 0.2419         # PM2.5 fraction in resuspension 
fleet_domain  = 15_266_361     # Fleet circulation in the model domain
fleet_cetesb  = 15_266_361     # Fleet circulation according to CETESB for Sao Paulo State
frac_ldv      = 0.936382       # LDV fraction in São Paulo State
frac_hdv      = 1- frac_ldv    # HDV fraction in São Paulo State
gaso_frac     = 0.335738       # Fraction of gasohol from LDV                    
etha_frac     = 0.015567       # Fraction of ethanol from LDV            
flex_frac     = 0.648695       # Fraction of flex from LDV               
etha_flex     = 0.50           # Fraction of flex-fuel (hydrated ethanol)
gaso_flex     = 1 - etha_flex  # Fraction of flex-fuel (gasohol)
date_start    = "2018-05-01"
date_end      = "2018-05-01"

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
         "NH3"   : 14+3,                  # Ammonia                             
         "ALD"   : 44,                    # Acetaldehyde          
         "VOC"   : 100,                   # Volatile Organic Compounds          
         "PM"    : 1,                     # Particulate matter                  
        }

# =============================================================================
# Total emissions in kt/year in CETESB to the modeling domain area
# =============================================================================
print(f"Processing emissions for {scen}.")

# 1. LDV exh, res, vap, liq
# where exh, res, vap, liq are sources (exhaust, resuspension, vapor, liquid)
ldv_inv   = pd.DataFrame.from_dict(# Units are in Gg (gigagrams or kilotonnes) 
            columns = [     'exh',    'res' ,    'vap',   'liq'],
            data    = {#---------| ---------|---------|--------|
            'CO'    : [  289.855 ,        0 ,       0 ,      0 ],  # to mol km^-2 hr^-1
            'NO'    : [   23.7956,        0 ,       0 ,      0 ],  # to mol km^-2 hr^-1
            'NO2'   : [    1.2524,        0 ,       0 ,      0 ],  # to mol km^-2 hr^-1
            'SO2'   : [    0.314 ,        0 ,       0 ,      0 ],  # to mol km^-2 hr^-1
            'ALD'   : [    1.695 ,        0 ,       0 ,      0 ],  # to mol km^-2 hr^-1
            'VOC'   : [   33.233 ,        0 ,  16.149 , 12.376 ],  # to mol km^-2 hr^-1
            'PM'    : [    0.282 ,    0.100 ,       0 ,      0 ],  # to ug m^-2 s^-1
            }, orient = 'index'
)

hdv_inv   = pd.DataFrame.from_dict(
            columns = [     'exh',      'res'],
            data    = {#---------| -----------
            'CO'    : [   24.992 ,          0],
            'NO'    : [  116.5004,          0],
            'NO2'   : [    6.1316,          0],
            'SO2'   : [    4.039 ,          0],
            'ALD'   : [    0.0   ,          0],
            'VOC'   : [    5.070 ,          0],
            'PM'    : [    3.608 ,    1.0000 ],
            }, orient = 'index'
)

# Emissions to domain fleet circulation
ldv_inv *= fleet_domain / fleet_cetesb
hdv_inv *= fleet_domain / fleet_cetesb
inv      = (ldv_inv + hdv_inv).sum(axis=1)

# to normalize for spatial distribution (each proxy sum to 1) !!! IMPORTANT ¡¡¡        
proxy_ldv /= proxy_ldv.sum()
proxy_hdv /= proxy_hdv.sum()

# -----------------------------------------------------------------------------
# Point emissions require xr.Dataset(), so we calculate from each xr.DataArray()
# -----------------------------------------------------------------------------

exh_ldv_src = xr.Dataset({para:ldv_inv.loc[para,'exh'] * proxy_ldv for para in ldv_inv.index})
res_ldv_src = xr.Dataset({para:ldv_inv.loc[para,'res'] * proxy_ldv for para in ldv_inv.index})
vap_ldv_src = xr.Dataset({para:ldv_inv.loc[para,'vap'] * proxy_ldv for para in ldv_inv.index})
liq_ldv_src = xr.Dataset({para:ldv_inv.loc[para,'liq'] * proxy_ldv for para in ldv_inv.index})
exh_hdv_src = xr.Dataset({para:hdv_inv.loc[para,'exh'] * proxy_hdv for para in hdv_inv.index})
res_hdv_src = xr.Dataset({para:hdv_inv.loc[para,'res'] * proxy_hdv for para in hdv_inv.index})

# =============================================================================
print(f"Emission speciation for VOC and PM by fuel and vehicle for {scen}")
# =============================================================================

# VOC exhaust speciation ------------------------------------------------------
voc_spc_exh = pd.DataFrame.from_dict(# CBMZ mechanism
    #                 ------ (mol/100 g VOC) --------
    #                 LDV                 HDV
    #                 Gas-E25   Eth95     Diesel B10
    columns =        ['gaso' ,  'etha',  'diesel'],
    data={ #         ---------------------------------
        'ETH' :       [0.2826,  0.0000,  0.0000  ],
        'HC3' :       [0.4352,  0.0000,  0.0490  ],
        'HC5' :       [0.4630,  0.9778,  0.0577  ],
        'HC8' :       [0.0765,  0.0000,  0.2966  ],
        'OL2' :       [0.3416,  0.9489,  0.3189  ],
        'OLT' :       [0.1432,  0.0762,  0.3853  ],
        'OLI' :       [0.1614,  0.0762,  0.0000  ],
        'C2H5OH':     [0.0000,  0.0000,  0.0000  ],
        'HCHO':       [0.0211,  0.0000,  0.0000  ],
       #'ALD' :       [0.0000,  0.0000,  0.0000  ],
        'ISO' :       [0.0046,  0.0000,  0.0000  ],
        'TOL':        [0.1405,  0.0151,  0.2351  ],
        'XYL'  :      [0.1575,  0.0395,  0.0084  ],
        'KET':        [0.0001,  0.0168,  0.0000  ], # methyl ethyl ketone, other ketones
        'CH3OH':      [0.0018,  0.0055,  0.0000  ], # methanol
        'ORA2':       [0.0000,  0.0000,  0.0000  ]  # m-Xylene, ethylbenzen, trimethylbenzen
          },
    orient='index'
    )

voc_spc_vap = pd.DataFrame.from_dict(# CBMZ mechanism                               
    #                 ------ (mol/100 g VOC) --------                           
    #                 LDV                 HDV                                   
    #                 Gas-E25   Eth95     Diesel B10                            
    columns =        ['gaso' ,  'etha',  'diesel'],
    data={ #         ---------------------------------                          
        'ETH' :       [0.0250,  0.0000,  0.0000  ],
        'HC3' :       [0.2400,  0.0000,  0.0000  ],
        'HC5' :       [0.4500,  0.0000,  0.0000  ],
        'HC8' :       [0.0000,  0.0000,  0.0000  ],
        'OL2' :       [0.0382,  0.0000,  0.0000  ],
        'OLT' :       [0.2000,  0.0000,  0.0000  ],
        'OLI' :       [0.4600,  0.0000,  0.0000  ],
        'C2H5OH':     [0.3500,  2.1706,  0.0000  ],
        'HCHO':       [0.0000,  0.0000,  0.0000  ],
       #'ALD' :       [0.0000,  0.0000,  0.0000  ],
        'ISO' :       [0.0000,  0.0000,  0.0000  ],
        'TOL':        [0.0850,  0.0000,  0.0000  ],
        'XYL'  :      [0.0000,  0.0000,  0.0000  ],
        'KET':        [0.0000,  0.0001,  0.0000  ], # methyl ethyl ketone, other ketones
        'CH3OH':      [0.0000,  0.0022,  0.0000  ], # methanol
        'ORA2':       [0.0000,  0.0000,  0.0000  ]  # m-Xylene, ethylbenzen, trimethylbenzen
          },
    orient='index'
    )

voc_spc_liq = pd.DataFrame.from_dict(# CBMZ mechanism
    #                 ------ (mol/100 g VOC) --------
    #                 LDV                 HDV
    #                 Gas-E25   Eth95     Diesel B10
    columns =        ['gaso' ,  'etha',  'diesel'],
    data={ #         ---------------------------------
        'ETH' :       [0.0000,  0.0000,  0.0000  ],
        'HC3' :       [0.2132,  0.0000,  0.0000  ],
        'HC5' :       [0.1573,  0.0000,  0.0000  ],
        'HC8' :       [0.1926,  0.0000,  0.0000  ],
        'OL2' :       [0.0000,  0.0000,  0.0000  ],
        'OLT' :       [0.0820,  0.0000,  0.0000  ],
        'OLI' :       [0.1798,  0.0000,  0.0000  ],
        'C2H5OH':     [0.6051,  2.1706,  0.0000  ],
        'HCHO':       [0.0000,  0.0000,  0.0000  ],
      # 'ALD' :       [0.0595,  0.0000,  0.0000  ],
        'ISO' :       [0.0011,  0.0000,  0.0000  ],
        'TOL':        [0.0584,  0.0000,  0.0000  ],
        'XYL'  :      [0.1193,  0.0000,  0.0000  ],
        'KET':        [0.0000,  0.0001,  0.0000  ], # methyl ethyl ketone, other ketones
        'CH3OH':      [0.0000,  0.0022,  0.0000  ], # methanol
        'ORA2':       [0.0000,  0.0000,  0.0000  ]  # m-Xylene, ethylbenzen, trimethylbenzen
          },
    orient='index'
    )

# Emission speciation for particulate matter ----------------------------------
pm_spc_exh = {# This is an example, edit with so much care             
          "PM_10"   : (1 - frac_exh) * 0.50,         # remaining species for fraction coarse
          "SO4C"    : (1 - frac_exh) * 0.15,
          "NO3C"    : (1 - frac_exh) * 0.10,
          "ECC"     : (1 - frac_exh) * 0.20,
          "ORGC"    : (1 - frac_exh) * 0.05,
          "ORGI_A"  : 0.19    * frac_exh * 0.19,     # intermediate IVOCs from anthropogenic
          "ORGJ_A"  : 0.19    * frac_exh * 0.81,     # accumulation mode
          "ORGI_BB" : 0.05    * frac_exh * 0.19,     # organic mass from biomass burning
          "ORGJ_BB" : 0.05    * frac_exh * 0.81,     # ORGI = ORGI_A + ORGI_BB
          "ECI"     : 0.38    * frac_exh * 0.94,
          "ECJ"     : 0.38    * frac_exh * 0.06,
          "SO4I"    : 0.03    * frac_exh * 0.136,
          "SO4J"    : 0.03    * frac_exh * 0.864,
          "NO3I"    : 0.012   * frac_exh * 0.23,
          "NO3J"    : 0.012   * frac_exh * 0.77,
          "PM25I"   : 0.3     * frac_exh * 0.25,     # other fine fractions
          "PM25J"   : 0.3     * frac_exh * 0.75
          }

pm_spc_res = {# 
          "PM_10"   : (1 - frac_res) * 0.50,
          "SO4C"    : (1 - frac_res) * 0.15,
          "NO3C"    : (1 - frac_res) * 0.10,
          "ECC"     : (1 - frac_res) * 0.20,
          "ORGC"    : (1 - frac_res) * 0.05,
          "ORGI_A"  : 0.1440  * frac_res * 0.01,     # intermediate IVOCs from anthropogenic
          "ORGJ_A"  : 0.1440  * frac_res * 0.99,     # accumulation mode
          "ORGI_BB" : 0.0480  * frac_res * 0.01,     # organic mass from biomass burning
          "ORGJ_BB" : 0.0480  * frac_res * 0.99,     # ORGI = ORGI_A + ORGI_BB
          "ECI"     : 0.0520  * frac_res * 0.01,
          "ECJ"     : 0.0520  * frac_res * 0.99,
          "SO4I"    : 0.1000  * frac_res * 0.01,
          "SO4J"    : 0.1000  * frac_res * 0.99,
          "NO3I"    : 0.0150  * frac_res * 0.01,
          "NO3J"    : 0.0150  * frac_res * 0.99,
          "PM25I"   : 0.6410  * frac_res * 0.01,
          "PM25J"   : 0.6410  * frac_res * 0.99
          }

# =============================================================================
# Emission calculations (PointSources function)                    ok rev by AD  
# =============================================================================
# 1. LDV        -> Gasohol, Ethanol, Flex
# 2. Motorbikes -> Gasohol and Flex

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

gaso_vap = PointSources(name = "LDV_vap_gasohol",
                        point_emiss = vap_ldv_src * (gaso_frac+flex_frac*gaso_flex),
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_spc_vap.gaso.to_dict(),
                        pm_spc = pm_spc_exh)

etha_vap = PointSources(name = "LDV_vap_ethanol",
                        point_emiss = vap_ldv_src * (etha_frac+flex_frac*etha_flex),
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_spc_vap.etha.to_dict(),
                        pm_spc = pm_spc_exh)

gaso_liq = PointSources(name = "LDV_liq_gasohol",
                        point_emiss = liq_ldv_src * (gaso_frac+flex_frac*gaso_flex),
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_spc_liq.gaso.to_dict(),
                        pm_spc = pm_spc_exh)

etha_liq = PointSources(name = "LDV_liq_ethanol",
                        point_emiss = liq_ldv_src * (etha_frac+flex_frac*etha_flex),
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_spc_liq.etha.to_dict(),
                        pm_spc = pm_spc_exh)

ldv_res  = PointSources(name = "LDV_with_res",
                        point_emiss = res_ldv_src,
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_spc_exh.gaso.to_dict(),
                        pm_spc = pm_spc_res)

# 2. HDV        -> Diesel
hdv_exh = PointSources(name = "HDV with diesel",
                        point_emiss = exh_hdv_src,
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.hdv,
                        voc_spc = voc_spc_exh.diesel.to_dict(),
                        pm_spc = pm_spc_exh)

hdv_res  = PointSources(name = "HDV with res",
                        point_emiss = res_hdv_src,
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.hdv,
                        voc_spc = voc_spc_exh.diesel.to_dict(),
                        pm_spc = pm_spc_res)


# =============================================================================
# Merge sources using the GroupSources function
# ============================================================================= 
road_sources  = GroupSources(sources_list = [gaso_exh, etha_exh,           # ok rev AD
                                             gaso_vap, etha_vap,
                                             gaso_liq, etha_liq,
                                             ldv_res,
                                             hdv_exh,  hdv_res
                                             ])

ldv_sources   = GroupSources(sources_list = [gaso_exh, etha_exh,           # ok rev AD
                                             gaso_vap, etha_vap,
                                             gaso_liq, etha_liq,
                                             ldv_res
                                             ])

hdv_sources   = GroupSources(sources_list = [hdv_exh, hdv_res              # ok rev AD
                                             ])

ldv_emiss     = ldv_sources.to_wrfchemi(wrfinput = wrfinput,
                                        start_date = date_start,
                                        end_date   = date_end,
                                      # week_profile = week_profile.frac,
                                        write_netcdf = True,
                                        path = "../results/" +GridName+'_'+APPL + '_'+ scen + '_' + 'ldv'
                                        )

hdv_emiss     = hdv_sources.to_wrfchemi(wrfinput = wrfinput,
                                        start_date = date_start,
                                        end_date = date_end,
                                      # week_profile = week_profile.frac,
                                        write_netcdf = True,
                                        path = "../results/" +GridName+'_'+APPL + '_'+ scen + '_' + 'hdv'
                                        )
road_emiss    = road_sources.to_wrfchemi(wrfinput = wrfinput,
                                         start_date = date_start,
                                         end_date = date_end,
                                       # week_profile = week_profile.frac,
                                         write_netcdf = True,
                                         path = "../results/" +GridName+'_'+APPL + '_'+ scen + '_' + tipo
                                         )
