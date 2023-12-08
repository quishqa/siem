import geopandas as gpd
from siem.proxy import (create_wrf_grid, load_osmx_to_gdfs,
                        calculate_points_grid, calculate_highway_grid)

if __name__ == "__main__":
    # Creating grid based on geo_em
    wrf_path = "../data/geo_em.d02.nc"
    hdv_path = "../data/partial/domain_hdv.graphml"

    hdv = load_osmx_to_gdfs(hdv_path)
    wrf_grid = create_wrf_grid(wrf_path, save=False)
    hdv_in_grid = calculate_highway_grid(wrf_grid, hdv, file_name="hdv")

    fuel_path = "../data/partial/point_source_fuel.shp"
    fuel = gpd.read_file(fuel_path)
    fuel_in_grid = calculate_points_grid(wrf_grid, fuel, file_name="fuel")
