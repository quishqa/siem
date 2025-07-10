# ======================== Emissions for MASP ========================
# Created by Alejandro D. Peralta
# Last update Aug. 14 2024, Nov. 11 2024, 3 Dec 2024
# conda activate siem
# ====================================================================

import xarray as xr
import numpy as np
import pandas as pd
from siem.siem import EmissionSource
from siem.siem import GroupSources
from siem.spatial import read_spatial_proxy
import matplotlib.pyplot as plt
import importlib
import warnings
warnings.filterwarnings("ignore",
                        message="IOAPI_ISPH is assumed to be 6370000.; consistent with WRF")

###############################################################################
#
# This is an example to calculate emissions as input data to the CMAQ model
#
###############################################################################

# Namelists ===================================================================
#> This inventory applies to the Metropolitan Area of São Paulo

APPL         = "3km"           # Application name (model horizontal resolution)
dom          = "d02"           # Model domain
mech         = "cmaq_cb6ae7"   # Speciation mechanism name
GridName     = "RMSP"          # Should match with GRIDDESC to implement    
tipo         = "roads"         # Area-line emission sources
scen         = 'tunnel'        # Scenario of emission factors and fleet
ldv_use      = 41.00           # Use intensity (km day^-1) for light-duty vehicles
tru_use      = 110.00          # Use intensity (km day^-1) for trucks       
urb_use      = 165.00          # Use intensity (km day^-1) for urban buses  
int_use      = 165.00          # Use intensity (km day^-1) for coach buses 
motg_use     = 140.00          # Use intensity (km day^-1) for motorbikes
mote_use     = 140.00          # Use intensity (km day^-1) for motorbikes
frac_exh     = 0.7765          # Fraction of PM2.5 in exhaust emissions
frac_res     = 0.2419          # Fraction of PM2.5 in resuspension emissions 
fleet        = 7_284_990       # Fleet circulation
flex_fv      = 0.561566        # Vehicle fraction powered with flex     (v3 )             
trucks_fv    = 0.060919        # Truck fraction powered with diesel     (v4a)                 
gasobike_fv  = 0.107455        # Motorbikes powered with gasoline       (v6a)           
date_start   = "2018-05-01"
date_end     = "2018-05-02"

# Reading data ================================================================
proj_path     = '/your/path/project/data/'       # <----- EDIT HERE
hdv_csv       = 'highways_hdv_'+dom+'.csv'
ldv_csv       = 'highways_ldv_'+dom+'.csv'
geopath       = proj_path + 'geo_em.'+dom+'.nc'
geo           = xr.open_dataset(geopath)
west_east     = len(geo.west_east)
south_north   = len(geo.south_north)
proxy_ldv     = read_spatial_proxy(proj_path + ldv_csv, (west_east, south_north))
proxy_hdv     = read_spatial_proxy(proj_path + hdv_csv, (west_east, south_north))
wrfinput      = xr.open_dataset(proj_path + "wrfinput_"+dom, engine = 'scipy')
daily_profile = pd.read_csv(proj_path + "daily_profile_sum.csv")  # Sum  1 (columns ldv, hdv)
week_profile  = pd.read_csv(proj_path + "week_profile.csv")       # Mean 1 (frac) 

#> Molecular weight (g mol^-1)-------------------------------------------------                                                  
mol_w = {"CO"    : 12+16,                 # Carbon monoxide                     
         "NO"    : 14+12, "NO2":14+12*2,  # Nitrogen oxide, nitrogen dioxide    
         "SO2"   : 32+16*2,               # Sulfur dioxide                      
         "VOC"   : 100,                   # Volatile Organic Compounds          
         "VOC_INV":1,                     #                                     
         "PM"    : 1,                     # Particulate matter                  
        }

# =============================================================================
# Emission Factors (g km^-1) by fuel consumption, vehicle type, and resuspension
# =============================================================================
print(f"Processing emissions for {scen}.")
# Please edit your emission factors

ef = pd.DataFrame.from_dict(### THIS IS AN EXAMPLE ###
    #                  LDV ---- HDV  --- Motorb--
    columns =        ['v1'   , 'v4a'  , 'v6a'   ],
    data={ #         -----------------------------
        'exa_co':     [6.5000,  4.9500,  10.4000],
        'exa_co2':    [206.00,  738.00, 206.0000],
        'exa_nox':    [0.5000,  9.8100,   0.1200],
        'exa_so2':    [0.0008,  0.0480,   0.0097],
        'exa_pm' :    [0.0612,  0.3665,   0.0612],
        'exa_voc':    [1.1700,  2.0500,   1.4100],
          },
    orient='index'
    )


#> LDV (Light-Duty Vehicle) ---------------------------------------------------
# v1 - LDV EF           (g km^-1                        , g mol^-1)
gasohol_ef = {"CO":     (ef.loc['exa_co'    , 'v1' ]    , mol_w["CO"]),   # Carbon monoxide
              "NO":     (ef.loc['exa_nox'   , 'v1' ]*.95, mol_w["NO"]),   # Nitrogen oxide
              "NO2":    (ef.loc['exa_nox'   , 'v1' ]*.05, mol_w["NO2"]),  # Nitrogen dioxide
              "SO2":    (ef.loc['exa_so2'   , 'v1' ]    , mol_w["SO2"]),  # Sulfur dioxide  
              "VOC":    (ef.loc['exa_voc'   , 'v1' ]    , mol_w["VOC"]),  # Volatile Organic Compounds (exhaust + vapor + liquid)
              "VOC_INV":(ef.loc['exa_voc'   , 'v1' ]    , mol_w["VOC_INV"]),  # Volatile Organic Compounds (exhaust + vapor + liquid)
              "PM":     (ef.loc['exa_pm'    , 'v1' ]    , mol_w["PM"]),   # Exhaust particulate matter
              }

#> High-Duty Vehicles -> Truck (Diesel), Bus (Diesel), Urban Bus (Diesel) -----
# v4a - HDV EF               (g km^-1                        , g mol^-1)
diesel_truck_ef = {"CO":     (ef.loc['exa_co'    , 'v4a']    , mol_w["CO"]),   # Carbon monoxide
                   "NO":     (ef.loc['exa_nox'   , 'v4a']*.95, mol_w["NO"]),   # Nitrogen oxide
                   "NO2":    (ef.loc['exa_nox'   , 'v4a']*.05, mol_w["NO2"]),  # Nitrogen dioxide
                   "SO2":    (ef.loc['exa_so2'   , 'v4a']    , mol_w["SO2"]),  # Sulfur dioxide
                   "VOC":    (ef.loc['voc'       , 'v4a']    , mol_w["VOC"]),  # Volatile Organic Compounds (exhaust + vapor + liquid)
                   "VOC_INV":(ef.loc['voc'       , 'v4a']    , mol_w["VOC_INV"]),  # Volatile Organic Compounds (exhaust + vapor + liquid)
                   "PM":     (ef.loc['exa_pm'    , 'v4a']    , mol_w["PM"]),   # Exhaust particulate matter
                  }

#> Motorbike Vehicles -> Gasoline, Ethanol ------------------------------------
#> Emission factors used in LAPAt model in ncl
# v6a - Motorbike EF          (g km^-1                        , g mol^-1)  
gasohol_mbike_ef = {"CO":     (ef.loc['exa_co'    , 'v6a']    , mol_w["CO"]),  # Carbon monoxide
                    "NO":     (ef.loc['exa_nox'   , 'v6a']*.95, mol_w["NO"]),  # Nitrogen oxide
                    "NO2":    (ef.loc['exa_nox'   , 'v6a']*.05, mol_w["NO2"]), # Nitrogen dioxide
                    "SO2":    (ef.loc['exa_so2'   , 'v6a']    , mol_w["SO2"]), # Sulfur dioxide
                    "VOC":    (ef.loc['voc'       , 'v6a']    , mol_w["VOC"]), # Volatile Organic Compounds (exhaust + vapor + liquid)
                    "VOC_INV":(ef.loc['voc'       , 'v6a']    , mol_w["VOC_INV"]), # Volatile Organic Compounds (exhaust + vapor + liquid)
                    "PM":     (ef.loc['exa_pm'    , 'v6a']    , mol_w["PM"]),  # Exhaust particulate matter
                   }

# =============================================================================
# Chemical Speciation 
# =============================================================================

# VOC speciation 
voc_spc = pd.DataFrame.from_dict(# CB6 mechanism                                
    #                 ---------- (mol/100 g VOC) -----------                               
    #                 Gasoline  Alcohol  Flex     Diesel (only exhaust)                    
    columns =         ['gaso',  'etha',  'flex',  'diesel'],
    data={ #         ---------------------------------------                                   
        'ETHA':       [0.1310,  0.0000,  0.0601,  0.0000  ],
        'PRPA':       [0.3204,  0.0000,  0.1468,  0.0490  ],
        'PAR':        [0.8438,  0.3018,  0.5502,  0.4431  ],
        'OLE':        [0.0315,  0.0000,  0.0144,  0.2966  ],
        'ETH':        [0.1631,  0.2534,  0.2120,  0.3189  ],
        'TOL':        [0.1078,  0.0040,  0.0516,  0.2351  ],
        'XYLMN':      [0.0648,  0.0105,  0.0354,  0.0084  ],
        'ALDX':       [0.1291,  0.1291,  0.1291,  0.1291  ],
        'BENZ':       [0.0128,  0.0128,  0.0128,  0.0142  ],
        'IOLE':       [0.0196,  0.0196,  0.0196,  0.0000  ],
          },
    orient='index'
    )

# Particulate matter speciation
pm_spc_exh  = {# This is an example                                                      
               "PMC"   : 1 - frac_exh,
               "POC"   : 0.24    * frac_exh,
               "PEC"   : 0.38    * frac_exh
               "PSO4"  : 0.03    * frac_exh,
               "PNO3"  : 0.012   * frac_exh,
               "PMOTHR": 0.338   * frac_exh,
              }

# =============================================================================
# Emission calculations (EmissionSource function)
# =============================================================================
# 1. LDV 
# 2. HDV 
# 3. Motorbikes

#> LDV ------------------------------------------------------------------------
gasohol_ldv = EmissionSource(name="LDV with gasohol",
                             number= fleet * gasohol_fv,
                             use_intensity = ldv_use,
                             pol_ef = gasohol_ef,
                             spatial_proxy = proxy_ldv,
                             temporal_prof = daily_profile.ldv,
                             voc_spc = voc_spc.gaso.to_dict(),
                             pm_spc = pm_spc_exh )


#> HDV ------------------------------------------------------------------------
trucks      = EmissionSource(name="Trucks with diesel",
                             number= fleet * trucks_fv,
                             use_intensity = tru_use,
                             pol_ef = diesel_truck_ef,
                             spatial_proxy = proxy_hdv,
                             temporal_prof = daily_profile.hdv,
                             voc_spc = voc_spc.diesel.to_dict(),
                             pm_spc = pm_spc_exh )


#> Motorbikes -----------------------------------------------------------------

gasohol_bike = EmissionSource(name="Motorbikes with gasohol",
                              number= fleet * gasobike_fv,
                              use_intensity = motg_use,
                              pol_ef = gasohol_mbike_ef,
                              spatial_proxy = proxy_ldv,
                              temporal_prof = daily_profile.ldv,
                              voc_spc = voc_spc.gaso.to_dict(),
                              pm_spc = pm_spc_exh )


# =============================================================================
# Merge sources using the GroupSources function
# =============================================================================

road_sources   = GroupSources(sources_list = [gasohol_ldv, trucks,
                                              gasohol_bike])


road_emiss     = road_sources.to_cmaq(wrfinput = wrfinput,
                                      griddesc_path = proj_path + "GRIDDESC_"+GridName,  # from mcip running
                                      btrim=  0,
                                      start_date= date_start,
                                      end_date= date_end,
                                      week_profile = week_profile.frac,
                                      write_netcdf = True,
                                      path = "../results/"+GridName+'_'+APPL+'_' + scen + '_' + tipo
                                     )

