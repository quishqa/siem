"""
This is an example of creating the proxy .csv file
from the download data from OSM.
See `./download_proxy.py`
"""

from siem.proxy import (
    create_wrf_grid,
    load_osmx_to_gdfs,
    calculate_highway_grid,
)

if __name__ == "__main__":
    # Creating grid based on geo_em
    wrf_path = "../data/geo_em.d02.nc"
    hdv_path = "../data/partial/domain_hdv_d02.graphml"

    # Create .csv file from osm highways files.
    hdv = load_osmx_to_gdfs(hdv_path)
    wrf_grid = create_wrf_grid(wrf_path, save=False)
    hdv_in_grid = calculate_highway_grid(wrf_grid, hdv, file_name="hdv")
