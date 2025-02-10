# siem/point.py
"""
Functions for point sources emissions

This module allows to work with PointSource class.

It contains the following functions:
    - `create_gpd_from(point_src_path, sep, lat_name, lon_name)` - Returns point sources csv in gpd.GeoDataFrame.
    - `calculate_sum_points(point_src, wrf_grid)` - Returns wrf_grid with sums of point sources emissions.
    - `create_emiss_point(point_src, wrf_grid)` - Returns wrf_grid with sums of point sources emissions and cell with no emissions with 0.
    - `retrive_proj_from(geogrid_path)` - Returns wrf domain projections.
    - `calculate_centroids(emiss_point, geo_path)` - Returns total emissions of point sources in wrf grid cell centroids.
    - `point_emiss_to_xarray(emiss_point_proj)` - Returns emissions in centroids in xr.Dataset.
    - `read_point_sources(point_path, geo_path, sep, lat_name, lon_name)` - Returns spatial distributed point sources emissiosn to use PointSources class.

"""
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
from netCDF4 import Dataset
from siem.proxy import create_wrf_grid, configure_grid_spatial
from wrf import getvar, get_cartopy


def create_gpd_from(point_src_path: str, sep: str = "\t",
                    lat_name: str = "LAT", lon_name: str = "LON",
                    ) -> gpd.GeoDataFrame:
    """
    Read .csv file with latitude and longitude of point sources,
    each column is the total emissions in KTn/year.

    Parameters
    ----------
    point_src_path : str
        Location of point source .csv file.
    sep : str
        Column separator of point_src file.
    lat_name : str
        Latitude column name.
    lon_name : str
        Longitude column name.

    Returns
    -------
    gpd.GeoDataFrame
        Point sources and emissions in GeoDataFrame.

    """
    point_sources = pd.read_csv(point_src_path, sep=sep)
    point_sources = gpd.GeoDataFrame(
        point_sources,
        geometry=gpd.points_from_xy(point_sources[lon_name],
                                    point_sources[lat_name]),
        crs="EPSG:4326")
    if "Unnamed: 0" in point_sources.columns:
        return point_sources.drop(["Unnamed: 0", lat_name, lon_name], axis=1)
    return point_sources.drop([lat_name, lon_name], axis=1)


def calculate_sum_points(point_src: gpd.GeoDataFrame,
                         wrf_grid: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Calculate sum of emissions from each point sources in a wrf grid cell.

    Parameters
    ----------
    point_src : gpd.GeoDataFrame
        GeoDataFrame of point sources. 
    wrf_grid : gpd.GeoDataFrame
        WRF domain grid

    Returns
    -------
    pd.DataFrame
        Sum of emission in each grid.

    """
    point_in_grid = gpd.overlay(point_src, wrf_grid, how="intersection")
    points_in_grid = point_in_grid.dissolve("ID", aggfunc="sum")
    return points_in_grid.drop(["geometry"], axis=1)


def create_emiss_point(point_src: gpd.GeoDataFrame,
                       wrf_grid: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Complete wrf grid cell with no point sources emissions with 0.
    TODO: change name of this function.

    Parameters
    ----------
    point_src : gpd.GeoDataFrame
        GeoDataFrame of point sources.
    wrf_grid : gpd.GeoDataFrame
        WRF domain grid

    Returns
    -------
    gpd.GeoDataFrame
        Complete grid with total emission in wrf domain grid.

    """
    points_in_grid = calculate_sum_points(point_src, wrf_grid)
    return wrf_grid.join(points_in_grid).fillna(0)


def retrive_proj_from(geogrid_path: str):
    """
    Extract projection of geo_em.d0x.nc file.

    Parameters
    ----------
    geogrid_path : str
       Location of geo_em.d0x.nc file.

    Returns
    -------
        Projection of geo_em.d0x.nc
        
    """
    with Dataset(geogrid_path) as geo_dom:
        hgt = getvar(geo_dom, "HGT_M")
    return get_cartopy(hgt)


def calculate_centroid(emiss_point: gpd.GeoDataFrame,
                       geo_path: str) -> pd.DataFrame:
    """
    Calculate centroid of each WRF domain grid cell.

    Parameters
    ----------
    emiss_point : gpd.GeoDataFrame
        Total emissions in each wrf domain cell.    
    geo_path : str
        Location of geo_em.d0x.nc file.

    Returns
    -------
    pd.DataFrame
       A DataFrame with total emissions from point sources with cell centroid coordiantes. 

    """
    wrf_proj = retrive_proj_from(geo_path)
    emiss_point_proj = emiss_point.to_crs(wrf_proj)
    emiss_point_proj["centro"] = emiss_point_proj.centroid
    emiss_point_proj["centro"] = emiss_point_proj.centroid.to_crs("EPSG:4326")
    emiss_point_proj["x"] = emiss_point_proj.centro.x.round(4)
    emiss_point_proj["y"] = emiss_point_proj.centro.y.round(4)
    return emiss_point_proj.drop(["geometry", "centro", "ID"], axis=1)


def point_emiss_to_xarray(emiss_point_proj: pd.DataFrame) -> xr.Dataset:
    """
    Transform point sources dataframe into a xr.Dataset.

    Parameters
    ----------
    emiss_point_proj : pd.DataFrame
        Total emissions in cell grid with centroid.

    Returns
    -------
    xr.Dataset
        Total emission in xr.Dataset.

    """
    lon1d = emiss_point_proj.x.round(5).unique()
    lat1d = emiss_point_proj.y.round(5).unique()
    lon, lat = np.meshgrid(lon1d, lat1d)

    emiss_point_proj = emiss_point_proj.rename(
        columns={"y": "south_north", "x": "west_east"}
    )

    coords = {"XLONG": (("south_north", "west_east"), lon),
              "XLAT": (("south_north", "west_east"), lat)}
    emiss_point_proj.set_index(["south_north", "west_east"], inplace=True)
    emiss_point = emiss_point_proj.to_xarray()
    emiss_point = (
        emiss_point
        .assign_coords(coords)
        .drop_vars(["south_north", "west_east"])
    )
    return emiss_point


def read_point_sources(point_path: str, geo_path: str, sep: str = "\t",
                       lat_name: str = "LAT", lon_name: str = "LON"
                       ) -> xr.Dataset:
    """
    Read point sources .csv file to produces a xr.Dataset.

    Parameters
    ----------
    point_path : str
        Location of point sources .csv file.
    geo_path : str
        Location of geo_em.d0X.nc file.
    sep : str
        Column separtor of point sources .csv file.
    lat_name : str
        Latitude column name.
    lon_name : str
        Longitude column name.

    Returns
    -------
    xr.Dataset
        Total emissions of point sources in each WRF domain cell xr.Dataset.

    """
    point_sources = create_gpd_from(point_path, sep, lat_name, lon_name)
    wrf_grid = create_wrf_grid(geo_path, save=False)
    wrf_grid = configure_grid_spatial(wrf_grid, point_sources)
    # Ensure points inside domain
    point_sources = gpd.clip(point_sources, wrf_grid)

    emiss_in_grid = create_emiss_point(point_sources, wrf_grid)
    emiss_in_grid = calculate_centroid(emiss_in_grid, geo_path)
    return point_emiss_to_xarray(emiss_in_grid)
