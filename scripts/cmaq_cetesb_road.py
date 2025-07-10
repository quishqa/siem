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
         "NH3"   : 14+3,                  # Ammonia                             
         "VOC"   : 100,                   # Volatile Organic Compounds          
         "VOC_INV":1,                     #                                     
         "PM"    : 1,                     # Particulate matter                  
        }

# =============================================================================
# Total emissions in kt/year in the modeling domain area
# =============================================================================
print(f"Processing emissions for {scen}.")

# 1. LDV exh, res, vap, liq (EDIT HERE)
# where exh, res, vap, liq are sources (exhaust, resuspension, vapor, liquid)
ldv_inv   = pd.DataFrame.from_dict(# Units are in Gg (gigagrams or kilotonnes)
            columns = [     'exh',    'res' ,    'vap',   'liq'],
            data    = {#---------| ---------|---------|--------|
            'CO'    : [   50.0000,        0 ,       0 ,      0 ],
            'NO'    : [   95.0000,        0 ,       0 ,      0 ],
            'NO2'   : [   10.0000,        0 ,       0 ,      0 ],
            'SO2'   : [    1.0000,        0 ,       0 ,      0 ],
            'VOC'   : [   50.0000,        0 ,  20.000 , 10.000 ],
            'PM'    : [    1.0000,    0.625 ,       0 ,      0 ],
            }, orient = 'index'
)

hdv_inv   = pd.DataFrame.from_dict(
            columns = [     'exh',      'res'],
            data    = {#---------| -----------
            'CO'    : [   25.000 ,          0],
            'NO'    : [  150.0000,          0],
            'NO2'   : [   15.0000,          0],
            'SO2'   : [    2.000 ,          0],
            'VOC'   : [   10.000 ,          0],
            'PM'    : [    3.000 ,    1.5000 ],
            }, orient = 'index'
)

ldv_inv.loc['VOC_INV']  = ldv_inv.loc['VOC', :]
hdv_inv.loc['VOC_INV']  = hdv_inv.loc['VOC', :]

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
        'ETHY':       [0.3416,  0.9489,  0.3189  ],
        'ETOH':       [0.6051,  0.0000,  0.0000  ],
        'FORM':       [0.0211,  0.0164,  0.0585  ],
        'ALD2':       [0.0196,  0.0318,  0.0399  ],
        'ISOP':       [0.0046,  0.0000,  0.0000  ],
        'TOL':        [0.1405,  0.0151,  0.2351  ],
        'XYLMN':      [0.1575,  0.0395,  0.0084  ],
        'KET':        [0.0001,  0.0168,  1.2E-5  ],
        'ACET':       [0.0001,  0.0168,  1.2E-5  ],
        'MEOH':       [0.0018,  0.0055,  3.0E-6  ],
        'ALDX':       [0.1291,  0.0000,  0.0000  ],
        'BENZ':       [0.0384,  0.0000,  0.0142  ],
        'IOLE':       [0.0196,  0.0000,  0.0196  ],
        'NAPH':       [0.0005,  0.0000,  0.0000  ],
        'NVOL':       [0.0000,  0.0000,  0.0002  ],
        'TERP':       [0.0000,  0.0000,  0.0000  ],
        'UNR' :       [0.0000,  0.0000,  0.0000  ]
          },
    orient='index'
    )

voc_spc_vap = pd.DataFrame.from_dict(# CB6 mechanism                                
    #                 ------ (mol/100 g VOC) --------                           
    #                 LDV                 HDV                                   
    #                 Gas-E25   Eth95     Diesel B10                            
    columns =        ['gaso' ,  'etha',  'diesel'],
    data={ #         ---------------------------------                          
        'ETHA':       [0.0250,  0.0000,  0.0000  ],
        'PRPA':       [0.2400,  0.0000,  0.0000  ],
        'PAR':        [1.1100,  0.0000,  0.0000  ],
        'OLE':        [0.0000,  0.0000,  0.0000  ],
        'ETH':        [0.0382,  0.0000,  0.0000  ],
        'ETHY':       [0.0382,  0.0000,  0.0000  ],
        'ETOH':       [0.3500,  2.1706,  0.0000  ],
        'FORM':       [0.0000,  0.0000,  0.0000  ],
        'ALD2':       [0.0000,  0.0000,  0.0000  ],
        'ISOP':       [0.0000,  0.0000,  0.0000  ],
        'TOL':        [0.0850,  0.0000,  0.0000  ],
        'XYLMN':      [0.0000,  0.0000,  0.0000  ],
        'KET':        [0.0000,  0.0001,  0.0000  ],
        'ACET':       [0.0000,  0.0001,  0.0000  ],
        'MEOH':       [0.0000,  0.0022,  0.0000  ],
        'ALDX':       [0.0000,  0.0000,  0.0000  ],
        'BENZ':       [0.0000,  0.0000,  0.0000  ],
        'IOLE':       [0.0000,  0.0000,  0.0000  ],
        'NAPH':       [0.0000,  0.0000,  0.0000  ],
        'NVOL':       [0.0000,  0.0000,  0.0000  ],
        'TERP':       [0.0000,  0.0000,  0.0000  ],
        'UNR' :       [0.0000,  0.0000,  0.0000  ]
          },
    orient='index'
    )

voc_spc_liq = pd.DataFrame.from_dict(# CB6 mechanism
    #                 ------ (mol/100 g VOC) --------
    #                 LDV                 HDV
    #                 Gas-E25   Eth95     Diesel B10
    columns =        ['gaso' ,  'etha',  'diesel'],
    data={ #         ---------------------------------
        'ETHA':       [0.0000,  0.0000,  0.0000  ],
        'PRPA':       [0.2132,  0.0000,  0.0000  ],
        'PAR':        [0.4190,  0.0000,  0.0000  ],
        'OLE':        [0.1926,  0.0000,  0.0000  ],
        'ETH':        [0.0000,  0.0000,  0.0000  ],
        'ETHY':       [0.0000,  0.0000,  0.0000  ],
        'ETOH':       [0.6051,  2.1706,  0.0000  ],
        'FORM':       [0.0000,  0.0000,  0.0000  ],
        'ALD2':       [0.0595,  0.0000,  0.0000  ],
        'ISOP':       [0.0011,  0.0000,  0.0000  ],
        'TOL':        [0.0584,  0.0000,  0.0000  ],
        'XYLMN':      [0.1193,  0.0000,  0.0000  ],
        'KET':        [0.0000,  0.0001,  0.0000  ],
        'ACET':       [0.0000,  0.0001,  0.0000  ],
        'MEOH':       [0.0000,  0.0022,  0.0000  ],
        'ALDX':       [0.0595,  0.0000,  0.0000  ],
        'BENZ':       [0.0000,  0.0000,  0.0000  ],
        'IOLE':       [0.0000,  0.0000,  0.0000  ],
        'NAPH':       [0.0000,  0.0000,  0.0000  ],
        'NVOL':       [0.0000,  0.0000,  0.0000  ],
        'TERP':       [0.0000,  0.0000,  0.0000  ],
        'UNR' :       [0.0000,  0.0000,  0.0000  ]
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
          "PAL"   : 0.003   * frac_exh,
          "PCA"   : 0.0108  * frac_exh,
          "PCL"   : 0.004   * frac_exh,
          "PFE"   : 0.02    * frac_exh,
          "PH2O"  : 0.0     * frac_exh,
          "PK"    : 0.002   * frac_exh,
          "PMG"   : 0.001   * frac_exh,
          "PMN"   : 0.0008  * frac_exh,
          "PMOTHR": 0.1247  * frac_exh,
          "PNA"   : 0.007   * frac_exh,
          "PNCOM" : 0.15    * frac_exh,
          "PNH4"  : 0.009   * frac_exh,
          "PSI"   : 0.0067  * frac_exh,
          "PTI"   : 0.0002  * frac_exh
          }

pm_spc_res = {
          "PMC"   : 1 - frac_res,
          "PAL"   : 0.09    * frac_res,
          "PCA"   : 0.0281  * frac_res,
          "PCL"   : 0.0004  * frac_res,
          "PFE"   : 0.0515  * frac_res,
          "PH2O"  : 0.0     * frac_res,
          "PK"    : 0.0132  * frac_res,
          "PMG"   : 0.0138  * frac_res,
          "PMN"   : 0.0007  * frac_res,
          "PMOTHR": 0.5     * frac_res,
          "PNA"   : 0.0027  * frac_res,
          "PNCOM" : 0.01206 * frac_res,
          "PNH4"  : 0.1     * frac_res,
          "PNO3"  : 0.0     * frac_res,
          "PSI"   : 0.1     * frac_res,
          "PSO4"  : 0.0     * frac_res,
          "PTI"   : 0.0061  * frac_res,
          "POC"   : 0.02    * frac_res,
          "PEC"   : 0.01    * frac_res
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

ldv_emiss     =   ldv_sources.to_cmaq(wrfinput = wrfinput,
                                      griddesc_path = proj_path + f"GRIDDESC_{GridName}",
                                      btrim = -1,
                                      start_date = date_start,
                                      end_date   = date_end,
                                      week_profile = week_profile.frac,
                                      write_netcdf = True,
                                      path = "../results/" +GridName+'_'+APPL + '_'+ scen + '_' + 'ldv'
                                      )

hdv_emiss     =   hdv_sources.to_cmaq(wrfinput = wrfinput,
                                      griddesc_path = proj_path + f"GRIDDESC_{GridName}",
                                      btrim = -1,
                                      start_date = date_start,
                                      end_date = date_end,
                                      week_profile = week_profile.frac,
                                      write_netcdf = True,
                                      path = "../results/" +GridName+'_'+APPL + '_'+ scen + '_' + 'hdv'
                                      )
road_emiss    =  road_sources.to_cmaq(wrfinput = wrfinput,
                                      griddesc_path = proj_path + f"GRIDDESC_{GridName}",
                                      btrim = -1,
                                      start_date = date_start,
                                      end_date = date_end,
                                      week_profile = week_profile.frac,
                                      write_netcdf = True,
                                      path = "../results/" +GridName+'_'+APPL + '_'+ scen + '_' + tipo
                                      )
