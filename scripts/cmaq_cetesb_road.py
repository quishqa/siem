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

# Namelists ===================================================================
APPL          = "3km"               # Application name
dom           = "d02"               # Model domain
mech          = "cmaq_cb6ae7"       # Speciation mechanism name
GridName      = "RMSP"              # Should match with GRIDDESC to implement    
scen          = 'CETESB'            # Scenario of emission factors and fleet
frac_exh      = 0.7765              # PM2.5 fraction in exhaust (Pereira et al. 2023)
frac_res      = 0.2419              # PM2.5 fraction in resuspension (U.S. EPA, 2011) Paved roads 
fleet_domain  = 7_284_990           # Fleet circulation in the model domain
fleet_cetesb  = 7_284_990           # Fleet circulation according to CETESB
frac_ldv      = 0.936382            # LDV fraction in São Paulo State
frac_hdv      = 1- frac_ldv
gaso_frac     = 0.335738            # Fraction of gasohol from LDV                    
etha_frac     = 0.015567            # Fraction of ethanol from LDV            
flex_frac     = 0.648695            # Fraction of flex from LDV               
etha_flex     = 0.30                # Fraction of flex-fuel powered with hidrated ethanol
gaso_flex     = 1 - etha_flex       # Fraction of flex-fuel powered with gasoline blending with 25% ethanol

# Read Data ===================================================================
proj_path     = '/home/alejandro/projects/siem/tests/test_data/'
hdv_csv       = 'highways_hdv_'+dom+'.csv'
ldv_csv       = 'highways_ldv_'+dom+'.csv'
ldv_path      = proj_path + ldv_csv
hdv_path      = proj_path + hdv_csv
wrfinput      = xr.open_dataset(proj_path + "wrfinput_"+dom, engine= "scipy")
geogrid_path  = proj_path + 'geo_em.'+dom+'.nc'
geo           = xr.open_dataset(geogrid_path)
west_east     = len(geo.west_east)
south_north   = len(geo.south_north)
daily_profile = pd.read_csv(proj_path + "daily_profile_sum.csv")   # Sum  1 (columns ldv, hdv)
week_profile  = pd.read_csv(proj_path + "week_profile.csv")        # Mean 1 (frac) 

#> Molecular weight (g mol^-1)-------------------------------------------------                                                  
mol_w = {"CO"    : 12+16,                 # Carbon monoxide                     
         "NO"    : 14+12,                 # Nitrogen oxide    
         "NO2"   : 14+12*2,               # Nitrogen dioxide    
         "SO2"   : 32+16*2,               # Sulfur dioxide                      
        #"NH3"   : 14+3,                  # Ammonia                             
         "VOC"   : 100,                   # Volatile Organic Compounds          
         "VOC_INV":1,                     #                                     
         "PM"    : 1,                     # Particulate matter                  
        }

# =============================================================================
# Total emissions in kt/year in the modeling domain area
# =============================================================================
print(f"Processing emissions for ({scen}).")
# CETESB emissions reported for the Sao Paulo State (2018)
#> res[PM2.5] = exh[PM2.5] *  5/37     (CETESB, 2019; Grafico 4)
#> res[PM10 ] = exh[PM10 ] * 25/40     (CETESB, 2019; Grafico 4)
res_fact = 25/40

# 1. LDV exh, res, vap, liq
ldv_inv   = pd.DataFrame.from_dict(
            columns = [     'exh',    'res' ,    'vap',   'liq'],
            data    = {#---------| ---------|---------|--------|
            'CO'    : [  289.855 ,        0 ,       0 ,      0 ],
            'NO'    : [   23.7956,        0 ,       0 ,      0 ],
            'NO2'   : [    1.2524,        0 ,       0 ,      0 ],
            'SO2'   : [    0.314 ,        0 ,       0 ,      0 ],
            'VOC'   : [   33.233 ,        0 ,  16.149 , 12.376 ],
            'PM'    : [    0.282 ,   np.nan ,       0 ,      0 ],
            }, orient = 'index'
)

hdv_inv   = pd.DataFrame.from_dict(
            columns = [     'exh',      'res'],
            data    = {#---------| -----------
            'CO'    : [   24.992 ,          0],
            'NO'    : [  116.5004,          0],
            'NO2'   : [    6.1316,          0],
            'SO2'   : [    4.039 ,          0],
            'VOC'   : [    5.070 ,          0],
            'PM'    : [    3.608 ,   np.nan  ],
            }, orient = 'index'
)

ldv_inv.loc['PM','res'] = ldv_inv.loc['PM','exh'] * res_fact
hdv_inv.loc['PM','res'] = hdv_inv.loc['PM','exh'] * res_fact
ldv_inv.loc['VOC_INV']  = ldv_inv.loc['VOC', :]
hdv_inv.loc['VOC_INV']  = hdv_inv.loc['VOC', :]

# Emissions to domain fleet circulation
ldv_inv *= fleet_domain / fleet_cetesb
hdv_inv *= fleet_domain / fleet_cetesb

ldv_spatial = read_spatial_proxy(ldv_path, (west_east, south_north))
ldv_spatial /= ldv_spatial.sum()

hdv_spatial = read_spatial_proxy(hdv_path, (west_east, south_north))
hdv_spatial /= hdv_spatial.sum()
# -----------------------------------------------------------------------------
# Point emissions require xr.Dataset(), so we calculate from each xr.DataArray()
# -----------------------------------------------------------------------------

exh_ldv_src = xr.Dataset({para:ldv_inv.loc[para,'exh'] * ldv_spatial for para in ldv_inv.index})
res_ldv_src = xr.Dataset({para:ldv_inv.loc[para,'res'] * ldv_spatial for para in ldv_inv.index})
vap_ldv_src = xr.Dataset({para:ldv_inv.loc[para,'vap'] * ldv_spatial for para in ldv_inv.index})
liq_ldv_src = xr.Dataset({para:ldv_inv.loc[para,'liq'] * ldv_spatial for para in ldv_inv.index})
exh_hdv_src = xr.Dataset({para:hdv_inv.loc[para,'exh'] * hdv_spatial for para in hdv_inv.index})
res_hdv_src = xr.Dataset({para:hdv_inv.loc[para,'res'] * hdv_spatial for para in hdv_inv.index})

# =============================================================================
print(f"Emission speciation for VOC and PM by fuel and vehicle for {scen}")
# =============================================================================
# Information comes from Andrade et al. (2015), VOC split.

# VOC exhaust speciation ------------------------------------------------------
voc_exh = pd.DataFrame.from_dict(# CB6 mechanism
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
        'FORM':       [0.0211,  0.0164,  0.0585  ], # Based on emission factors n tunnel experiments 
        'ALD2':       [0.0196,  0.0318,  0.0399  ], # idem 
        'ISOP':       [0.0046,  0.0000,  0.0000  ],
        'TOL':        [0.1405,  0.0151,  0.2351  ],
        'XYLMN':      [0.1575,  0.0395,  0.0084  ],
        'KET':        [0.0001,  0.0168,  1.2E-5  ],
        'ACET':       [0.0001,  0.0168,  1.2E-5  ],
        'MEOH':       [0.0018,  0.0055,  3.0E-6  ],
        'ALDX':       [0.1291,  0.0000,  0.0000  ], # Based on Dominutti et al. (2020)
        'BENZ':       [0.0384,  0.0000,  0.0142  ], # idem, C9 aromatics
        'IOLE':       [0.0196,  0.0000,  0.0196  ],
        'NAPH':       [0.0005,  0.0000,  0.0000  ],
        'NVOL':       [0.0000,  0.0000,  0.0002  ],
        'SOAALK':     [0.0911,  0.0000,  0.0418  ],
        'TERP':       [0.0000,  0.0000,  0.0000  ],
        'UNR' :       [0.0000,  0.0000,  0.0000  ]
          },
    orient='index'
    )

voc_vap = pd.DataFrame.from_dict(# CB6 mechanism                                
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
        'SOAALK':     [0.0000,  0.0000,  0.0000  ],
        'TERP':       [0.0000,  0.0000,  0.0000  ],
        'UNR' :       [0.0000,  0.0000,  0.0000  ]
          },
    orient='index'
    )

voc_liq = pd.DataFrame.from_dict(# CB6 mechanism
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
        'SOAALK':     [0.0000,  0.0000,  0.0000  ],
        'TERP':       [0.0000,  0.0000,  0.0000  ],
        'UNR' :       [0.0000,  0.0000,  0.0000  ]
          },
    orient='index'
    )

# Emission speciation for particulate matter ----------------------------------
pm_exh = {# From Pereira et al. (2023)                                     
          "PMC"   : 1 - frac_exh,
          "POC"   : 0.244   * frac_exh,
          "PEC"   : 0.377   * frac_exh,
          "PSO4"  : 0.033   * frac_exh,
          "PNO3"  : 0.012   * frac_exh,
          "PAL"   : 0.0023  * frac_exh,
          "PCA"   : 0.0108  * frac_exh,
          "PCL"   : 0.0035  * frac_exh,
          "PFE"   : 0.0196  * frac_exh,
          "PH2O"  : 0.0     * frac_exh,
          "PK"    : 0.0018  * frac_exh,
          "PMG"   : 0.0011  * frac_exh,
          "PMN"   : 0.0008  * frac_exh,
          "PMOTHR": 0.1247  * frac_exh,
          "PNA"   : 0.007   * frac_exh,
          "PNCOM" : 0.1464  * frac_exh,
          "PNH4"  : 0.009   * frac_exh,
          "PSI"   : 0.0067  * frac_exh,
          "PTI"   : 0.0002  * frac_exh
          }

pm_res = {# Ivan Gregorio & Andrade (2016)                                 
          "PMC"   : 1 - frac_res,
          "PAL"   : 0.0861  * frac_res,
          "PCA"   : 0.0281  * frac_res,
          "PCL"   : 0.0004  * frac_res,
          "PFE"   : 0.0515  * frac_res,
          "PH2O"  : 0.0     * frac_res,
          "PK"    : 0.0132  * frac_res,
          "PMG"   : 0.0138  * frac_res,
          "PMN"   : 0.0007  * frac_res,
          "PMOTHR": 0.54653 * frac_res,
          "PNA"   : 0.0027  * frac_res,
          "PNCOM" : 0.01206 * frac_res,
          "PNH4"  : 0.1     * frac_res,
          "PNO3"  : 0.0     * frac_res,
          "PSI"   : 0.1037  * frac_res,
          "PSO4"  : 0.0     * frac_res,
          "PTI"   : 0.0061  * frac_res,
          "POC"   : 0.0201  * frac_res,
          "PEC"   : 0.0150  * frac_res
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
                        voc_spc = voc_exh.gaso.to_dict(),
                        pm_spc = pm_exh)

etha_exh = PointSources(name = "LDV_exh_ethanol",
                        point_emiss = exh_ldv_src * (etha_frac+flex_frac*etha_flex),
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_exh.etha.to_dict(),
                        pm_spc = pm_exh)

gaso_vap = PointSources(name = "LDV_vap_gasohol",
                        point_emiss = vap_ldv_src * (gaso_frac+flex_frac*gaso_flex),
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_vap.gaso.to_dict(),
                        pm_spc = pm_exh)

etha_vap = PointSources(name = "LDV_vap_ethanol",
                        point_emiss = vap_ldv_src * (etha_frac+flex_frac*etha_flex),
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_vap.etha.to_dict(),
                        pm_spc = pm_exh)

gaso_liq = PointSources(name = "LDV_liq_gasohol",
                        point_emiss = liq_ldv_src * (gaso_frac+flex_frac*gaso_flex),
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_liq.gaso.to_dict(),
                        pm_spc = pm_exh)

etha_liq = PointSources(name = "LDV_liq_ethanol",
                        point_emiss = liq_ldv_src * (etha_frac+flex_frac*etha_flex),
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_liq.etha.to_dict(),
                        pm_spc = pm_exh)

ldv_res  = PointSources(name = "LDV_with_res",
                        point_emiss = res_ldv_src,
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.ldv,
                        voc_spc = voc_exh.gaso.to_dict(),
                        pm_spc = pm_res)

# 2. HDV        -> Diesel
hdv_exh = PointSources(name = "HDV with diesel",
                        point_emiss = exh_hdv_src,
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.hdv,
                        voc_spc = voc_exh.diesel.to_dict(),
                        pm_spc = pm_exh)

hdv_res  = PointSources(name = "HDV with res",
                        point_emiss = res_hdv_src,
                        pol_emiss   = mol_w,
                        temporal_prof = daily_profile.hdv,
                        voc_spc = voc_exh.diesel.to_dict(),
                        pm_spc = pm_res)


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
                                      start_date = '2018-05-01',
                                      end_date = '2018-05-02',
                                      week_profile = week_profile.frac,
                                      write_netcdf = True,
                                      path = "../results/" +GridName+'_'+APPL + '_'+ scen + '/' + 'ldv'
                                      )

hdv_emiss     =   hdv_sources.to_cmaq(wrfinput = wrfinput,
                                      griddesc_path = proj_path + f"GRIDDESC_{GridName}",
                                      btrim = -1,
                                      start_date = '2018-05-01',
                                      end_date = '2018-05-02',
                                      week_profile = week_profile.frac,
                                      write_netcdf = True,
                                      path = "../results/" +GridName+'_'+APPL + '_'+ scen + '/' + 'hdv'
                                      )
road_emiss    =  road_sources.to_cmaq(wrfinput = wrfinput,
                                      griddesc_path = proj_path + f"GRIDDESC_{GridName}",
                                      btrim = -1,
                                      start_date = '2018-05-01',
                                      end_date = '2018-05-02',
                                      week_profile = week_profile.frac,
                                      write_netcdf = True,
                                      path = "../results/" +GridName+'_'+APPL + '_'+ scen + '/' + 'road_all'
                                      )
