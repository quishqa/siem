import geopandas as gpd
from siem.proxy import (create_wrf_grid, load_osmx_to_gdfs,
                        calculate_points_grid, calculate_highway_grid)

if __name__ == "__main__":
    # Creating grid based on geo_em
    wrf_path = "../data/geo_em.d02.nc"
    hdv_path = "../data/partial/domain_hdv.graphml"
    wrf_grid = create_wrf_grid(wrf_path, save=False)

    hdv = load_osmx_to_gdfs(hdv_path)
    point_src = gpd.read_file("../data/partial/point_source_fuel.shp")

    hdv_in_grid = calculate_highway_grid(wrf_grid, hdv, file_name="hdv")
    points_in_grid = calculate_points_grid(wrf_grid, point_src,
                                           file_name="fuel")
