import osmnx as ox
import xarray as xr
import numpy as np
from shapely.geometry import Polygon
import geopandas as gpd


def get_domain_extension(wrf_path: str ="../data/geo_em.d02.nc") -> tuple:
    geo = xr.open_dataset(wrf_path)
    xlat_c = geo.XLAT_C.isel(Time=0)
    xlon_c = geo.XLONG_C.isel(Time=0)
    north = xlat_c.max().values
    south = xlat_c.min().values
    east = xlon_c.max().values
    west = xlon_c.min().values
    return (north, south, east, west)


def get_highway_query(highway_types: list[str],
                      add_links: bool = False) -> str:
    if add_links:
        highway_links = [f"{st}_link" for st in highway_types]
        highway_types += highway_links

    cf = ('[' + '"highway"' + "~" +
          '"' + "|".join(highway_types) +
          '"' + ']')
    print(f"The custom filter is:\n {cf}")
    return cf


def download_highways(wrf_path: str, highway_types: str,
                      add_links: bool = False,
                      save: bool = True,
                      save_path: str = "../data/partial",
                      file_name: str = "highway"):

    north, south, east, west = get_domain_extension(wrf_path)
    custom_filter = get_highway_query(highway_types, add_links)
    highways = ox.graph_from_bbox(north, south, east, west,
                                  network_type="drive",
                                  custom_filter=custom_filter)
    if save:
        ox.save_graphml(highways,
                        filepath=f"{save_path}/domain_{file_name}.graphml")
    return highways


def download_point_sources(wrf_path: str, tags: dict,
                           save: bool = True,
                           save_path: str = "../data/partial"):
    '''Download point sources like:
        fuel stations tags={"amenity": "fuel"}
        pizza restaurant tags={"cuisine": "pizza"}'''
    north, south, east, west = get_domain_extension(wrf_path)
    point_sources = ox.features_from_bbox(north, south, east, west,
                                          tags=tags)
    point_sources_shp = point_sources[["name", "geometry"]].centroid
    print(f"Point sources: {len(point_sources_shp)}")

    if save:
        source_type = list(tags.values())[0]
        point_sources_shp.to_file(
                f"{save_path}/point_source_{source_type}.shp"
                )
    return point_sources_shp


def create_grid(lat: np.ndarray, lon: np.ndarray) -> gpd.GeoDataFrame:
    poly = []
    for j in range(len(lat) - 1):
        for i in range(len(lon) - 1):
            poly.append(Polygon([
                (lon[i], lat[j + 1]),
                (lon[i + 1], lat[j + 1]),
                (lon[i + 1], lat[j]),
                (lon[i], lat[j])
            ]))
    grid_wrf = gpd.GeoDataFrame({"geometry": poly})
    return grid_wrf


def create_wrf_grid(wrf_path: str, save: bool = True,
                    save_path: str = "../data/partial") -> gpd.GeoDataFrame:
    with xr.open_dataset(wrf_path) as geo:
        xlat_c = (geo
                  .XLAT_C
                  .isel(Time=0, west_east_stag=0)
                  .values)
        xlon_c = (geo
                  .XLONG_C
                  .isel(Time=0, south_north_stag=0)
                  .values)
        grid_id = geo.grid_id
    wrf_grid = create_grid(xlat_c, xlon_c)
    if save:
        wrf_grid.to_file(f"{save_path}/wrf_grid_d{grid_id}.shp")
    return wrf_grid


def configure_grid_spatial(wrf_grid: gpd.GeoDataFrame,
                           proxy: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    wrf_grid = wrf_grid.set_crs(proxy.crs)
    wrf_grid["ID"] = range(0, len(wrf_grid))
    return wrf_grid


def calculate_points_grid(wrf_grid: gpd.GeoDataFrame,
                          proxy: gpd.GeoDataFrame,
                          to_pre: bool = True,
                          save_pre: str = "../data",
                          file_name: str = "my_src") -> gpd.GeoDataFrame:
    wrf_grid_ready = configure_grid_spatial(wrf_grid,
                                            proxy)
    proxy_in_grid = gpd.clip(proxy, wrf_grid_ready)
    # From:
    # https://stackoverflow.com/questions/69644523/count-points-in-polygon-and-write-result-to-geodataframe
    points_in_grid = (wrf_grid_ready
                      .sjoin(proxy_in_grid)
                      .groupby("ID")
                      .count()
                      .geometry
                      .rename("n_sources"))
    points_in_dom = wrf_grid.join(points_in_grid).fillna(0)
    if to_pre:
        points_in_dom["x"] = points_in_dom.centroid.geometry.x
        points_in_dom["y"] = points_in_dom.centroid.geometry.y
        points_in_dom[["x", "y", "n_sources"]].to_csv(
                f"{save_pre}/points_{file_name}.csv",
                sep=" ", header=False
                )
    return points_in_dom


def load_osmx_to_gdfs(osmx_path):
    sp = ox.load_graphml(osmx_path)
    return ox.graph_to_gdfs(sp, nodes=False, edges=True)


def calculate_highway_grid(wrf_grid: gpd.GeoDataFrame,
                           proxy: gpd.GeoDataFrame,
                           to_pre: bool = True,
                           save_pre: str = "../data/",
                           file_name: str = "my_src") -> gpd.GeoDataFrame:
    wrf_grid_ready = configure_grid_spatial(wrf_grid, proxy)

    highway = proxy[["highway", "length", "geometry"]]
    highway = gpd.clip(highway, wrf_grid_ready)
    highway_grid = gpd.overlay(highway, wrf_grid_ready,
                               how="intersection")
    highway_grid = highway_grid.dissolve("ID")
    highway_grid["longKm"] = (highway_grid
                              .geometry
                              .to_crs("EPSG:32733")
                              .length / 1000)

    highway_dom = wrf_grid.join(highway_grid[["longKm"]]).fillna(0)

    if to_pre:
        highway_dom["x"] = highway_dom.geometry.centroid.x
        highway_dom["y"] = highway_dom.geometry.centroid.y
        highway_dom[["x", "y", "longKm"]].to_csv(
                f"{save_pre}/highways_{file_name}.csv",
                sep=" ", header=False
                )
    return highway_dom
