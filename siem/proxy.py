# siem/proxy.py
"""
Functions to download and create spatial proxy using OSM data.

This module helps you to download OSM data to be used to spatially distribute
emissions. It's mainly developed to distribute vehicular emissions.
It helps you to create the `spatial_proxy` to use in `EmissSource`.

It contains the following functions:
    - `get_domain_extension(geo_em_path)` - Returns wrf domain corners coordinates.
    - `get_highway_query(highway_types, add_links)` - Returns query for dowload highways.
    - `download_highways(geo_em_path, highway_types, add_links, save_path, file_name)` - Returns highways in domain in graphml.
    - `download_point_sources(geo_em_path, tags, save, save_path)` - Returns amenities shapefile.
    - `create_grid(geo_em)` - Return wrf grid shapfile.
    - `create_wrf_grid(geo_em_path, save, save_path)` - Returns wrf grid after read geo_em.d0X.
    - `configure_grid_spatial(wrf_grid, proxy)` - Returns wrf_grid with proxy CRS and cell ID column.
    - `calculate_points_grid(wrf_grid, proxy, to_pre, save_pre, file_name)` - Returns number of amenities in eac wrf grid.
    - `load_osmx_to_gdfs(osmx_path)` - Returns highways graphml into GeoDataFrame.
    - `calculate_highway_grid(wrf_grid, proxy, to_pre, save_pre, file_name)` - Returns sums of highways longitude inside each wrf grid cell.

"""

import osmnx as ox
import xarray as xr
import numpy as np
import shapely
from siem.user import check_create_savedir
import geopandas as gpd


def get_domain_extension(geo_em_path: str = "../data/geo_em.d02.nc") -> tuple:
    """
    Extract wrf domain corners latitude and longitude.

    Parameters
    ----------
    geo_em_path : str
        Location of geo_em.d0x.nc file

    Returns
    -------
    tuple
        max latitude, min latitude, max longitude, and min longitude.
    """
    geo = xr.open_dataset(geo_em_path)
    xlat_c = geo.XLAT_C.isel(Time=0)
    xlon_c = geo.XLONG_C.isel(Time=0)
    north = xlat_c.max().values
    south = xlat_c.min().values
    east = xlon_c.max().values
    west = xlon_c.min().values
    return (north, south, east, west)


def get_highway_query(highway_types: list[str],
                      add_links: bool = False) -> str:
    """List to OSMx query.

    Create the custiom query based on highways types to use in OSMx package.
    See <https://wiki.openstreetmap.org/wiki/Key:highway>.

    Parameters
    ----------
    highway_types: list[str]
        List with the types of highways to download.
    add_links: bool
        If highways type links need to be download.

    Returns
    -------
    str
        The custom query to use OSMx.
    """
    if add_links:
        highway_links = [f"{st}_link" for st in highway_types]
        highway_types += highway_links

    cf = ('[' + '"highway"' + "~" +
          '"' + "|".join(highway_types) +
          '"' + ']')
    print(f"The custom filter is:\n {cf}")
    return cf


def download_highways(geo_em_path: str, highway_types: str,
                      add_links: bool = False,
                      save: bool = True,
                      save_path: str = "../data/partial",
                      file_name: str = "highway"):
    """
    Download highways types contain in WRF domains.

    Parameters
    ----------
    wrf_path: str
        location of geo_em.d0x file.
    highway_type: str
        List with the types of highways to download.
    add_links: bool
        If highways type links need to be download.
    save: bool
        To save the file.
    save_bath: str
        Location to save downloaded highways.
    file_name:
        Identifier of save file.

    Returns
    -------
    Highways in domain in graph.ml format.
    """
    north, south, east, west = get_domain_extension(geo_em_path)
    custom_filter = get_highway_query(highway_types, add_links)
    highways = ox.graph_from_bbox(north, south, east, west,
                                  network_type="drive",
                                  custom_filter=custom_filter)
    if save:
        check_create_savedir(save_path)
        ox.save_graphml(highways,
                        filepath=f"{save_path}/domain_{file_name}.graphml")
    return highways


def download_point_sources(geo_em_path: str, tags: dict,
                           save: bool = True,
                           save_path: str = "../data/partial"):
    """Download OSM amenities.

    Download point sources like fuel staions or restaurants.
    It is based on OSM amenities. This function uses tags that can be found in
    <https://wiki.openstreetmap.org/wiki/Key:amenity>.

    Parameters
    ----------
    wrf_path: str
        location of geo_em.d0x file.
    tags: dict
        For example, fuel stations `tags={"amenity": "fuel"}` or
        for pizza restaurant `tags={"cuisine": "pizza"}`
    save: bool
        To save the file.
    save_bath: str
        Location to save downloaded amenities.

    Returns
    -------
        Point amenities in shapefile.
    """
    north, south, east, west = get_domain_extension(geo_em_path)
    point_sources = ox.features_from_bbox(north, south, east, west,
                                          tags=tags)
    point_sources_shp = point_sources[["name", "geometry"]].centroid
    print(f"Point sources: {len(point_sources_shp)}")

    if save:
        check_create_savedir(save_path)
        source_type = list(tags.values())[0]
        point_sources_shp.to_file(
            f"{save_path}/point_source_{source_type}.shp"
        )
    return point_sources_shp


def create_grid(geo_em: xr.Dataset) -> gpd.GeoDataFrame:
    """Create grid from geo_em cell coordinates.

    Create grid based of geo_em.d0X.nc file. It is compatible with
    Mercator and Lambert projections.
    
    Based on:
        <https://gis.stackexchange.com/questions/414617/creating-polygon-grid-from-point-grid-using-geopandas>.

    Parameters
    ----------
    geo_em: xr.Dataset
        WRF geo_em.d0x.nc file

    Returns
    -------
    gpd.GeoDataFrame
        WRF domain grid in GeoDataFrame format.
    """
    clat = geo_em.XLAT_C.sel(Time=0).values
    clon = geo_em.XLONG_C.sel(Time=0).values

    nrow = geo_em.sizes["south_north"]
    ncol = geo_em.sizes["west_east"]

    n = nrow * ncol

    left = lower = slice(None, -1)
    upper = right = slice(1, None)
    corners = [
        [lower, left],
        [lower, right],
        [upper, right],
        [upper, left]
    ]

    xy = np.empty((n, 4, 2))

    for i, (rows, cols) in enumerate(corners):
        xy[:, i, 0] = clon[rows, cols].ravel()
        xy[:, i, 1] = clat[rows, cols].ravel()

    grid_geometry = shapely.creation.polygons(xy)
    grid_wrf = gpd.GeoDataFrame(geometry=grid_geometry)
    return grid_wrf


def create_wrf_grid(geo_em_path: str, save: bool = True,
                    save_path: str = "../data/partial") -> gpd.GeoDataFrame:
    """
    Create WRF domain grid.

    Parameters
    ----------
    geo_em_path: str
        Location of geo_em.d0X.nc file.
    save: bool
        If grid needs to be saved.
    save_path:
        Location to save wrf grid.
    """
    with xr.open_dataset(geo_em_path) as geo:
        wrf_grid = create_grid(geo)
        grid_id = geo.grid_id
    if save:
        check_create_savedir(save_path)
        wrf_grid.to_file(f"{save_path}/wrf_grid_d{grid_id}.shp")
    return wrf_grid


def configure_grid_spatial(wrf_grid: gpd.GeoDataFrame,
                           proxy: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Prepare wrf grid for spatial operations.

    Add CRS to WRF grid and added ID, preparing grid to be intecepted
    with highway shp.

    Parameters
    ----------
    wrf_grid: gpd.GeoDataFrame
        WRF domain grid.
    proxy: gpd.GeoDataFrame
        proxy shapefile (highways)

    Returns
    -------
    gpd.GeoDataFrame
        wrf_grid with same CRS as proxy and with column ID.
    """
    wrf_grid = wrf_grid.set_crs(proxy.crs)
    wrf_grid["ID"] = range(0, len(wrf_grid))
    return wrf_grid


def calculate_points_grid(wrf_grid: gpd.GeoDataFrame,
                          proxy: gpd.GeoDataFrame,
                          to_pre: bool = True,
                          save_pre: str = "../data",
                          file_name: str = "my_src") -> gpd.GeoDataFrame:
    """
    Calculate number of points (osm amenites) in each wrf grid cells.

    Parameters
    ----------
    wrf_grid : gpd.GeoDataFrame
        WRF domain grid.
    proxy : gpd.GeoDataFrame
        proxy shapefile (amenities)
    to_pre : bool
        If needed to prepare spatial proxy.
    save_pre : str
        Location to save file.
    file_name : str
        File identifier.

    Returns
    -------
    gpd.GeoDataFrame
       Number of points in each cell grid.
    """
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
        check_create_savedir(save_pre)
        points_in_dom["x"] = points_in_dom.centroid.geometry.x
        points_in_dom["y"] = points_in_dom.centroid.geometry.y
        points_in_dom[["x", "y", "n_sources"]].to_csv(
            f"{save_pre}/points_{file_name}.csv",
            sep=" ", header=False
        )
    return points_in_dom


def load_osmx_to_gdfs(osmx_path: str) -> gpd.GeoDataFrame:
    """
    Load osmx highways (graph.ml) to gpd.GeoDataFrame.

    Parameters
    ----------
    osmx_path : str
       Location of highways type data. 

    Returns
    -------
    gpd.GeoDataFrame
        Highways in GeoDataFrame.
    """
    sp = ox.load_graphml(osmx_path)
    return ox.graph_to_gdfs(sp, nodes=False, edges=True)


def calculate_highway_grid(wrf_grid: gpd.GeoDataFrame,
                           proxy: gpd.GeoDataFrame,
                           to_pre: bool = True,
                           save_pre: str = "../data/",
                           file_name: str = "my_src") -> gpd.GeoDataFrame:
    """Sum of highways lenght inside wrf grid cell.

    Calculate sum of highways longitude inside WRF grid cell.
    This will produce a proxy for spatially distribute vehicular emissions.

    Parameters
    ----------
    wrf_grid : gpd.GeoDataFrame
        WRF domain grid.    
    proxy : gpd.GeoDataFrame
        Highways shapefile.
    to_pre : bool
        If needed to prepare spatial proxy.
    save_pre : str
        Location to save file.
    file_name : str
        File identifier name.

    Returns
    -------
    gpd.GeoDataFrame
        Sum of longitudes of all highways type inside grid cell.

    """
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
        check_create_savedir(save_pre)
        highway_dom["x"] = highway_dom.geometry.centroid.x
        highway_dom["y"] = highway_dom.geometry.centroid.y
        highway_dom[["x", "y", "longKm"]].to_csv(
            f"{save_pre}/highways_{file_name}.csv",
            sep=" ", header=False
        )
    return highway_dom
