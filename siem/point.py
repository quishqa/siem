# siem/point.py
"""Functions for point sources emissions.

This module allows to work with PointSource class.

It contains the following functions:
    - `create_gpd_from(point_src_path, sep, lat_name, lon_name)` - Returns: point sources csv in gpd.GeoDataFrame.
    - `calculate_sum_points(point_src, wrf_grid)` - Returns: wrf_grid with sums of point sources emissions.
    - `create_emiss_point(point_src, wrf_grid)` - Returns: wrf_grid with sums of point sources emissions and cell with no emissions with 0.
    - `retrive_proj_from(geogrid_path)` - Returns: wrf domain projections.
    - `calculate_centroids(emiss_point, geo_path)` - Returns: total emissions of point sources in wrf grid cell centroids.
    - `point_emiss_to_xarray(emiss_point_proj)` - Returns: emissions in centroids in xr.Dataset.
    - `read_point_sources(point_path, geo_path, sep, lat_name, lon_name)` - Returns: spatial distributed point sources emissions to use PointSources class.
"""

import pandas as pd
import geopandas as gpd
import xarray as xr
from netCDF4 import Dataset
from siem.proxy import create_wrf_grid, configure_grid_spatial
import pyproj


def create_gpd_from(
    point_src_path: str,
    sep: str = "\t",
    lat_name: str = "LAT",
    lon_name: str = "LON",
) -> gpd.GeoDataFrame:
    """Read point emiss csv.

    Read .csv file with latitude and longitude of point sources,
    each column is the total emissions in KTn/year.

    Args:
        point_src_path: Location of point source .csv file.
        sep: Column separator of point_src file.
        lat_name: Latitude column name.
        lon_name: Longitude column name.

    Returns:
        Point sources and emissions in GeoDataFrame.
    """
    point_sources = pd.read_csv(point_src_path, sep=sep)
    point_sources = gpd.GeoDataFrame(
        point_sources,
        geometry=gpd.points_from_xy(point_sources[lon_name], point_sources[lat_name]),
        crs="EPSG:4326",
    )
    if "Unnamed: 0" in point_sources.columns:
        return point_sources.drop(["Unnamed: 0", lat_name, lon_name], axis=1)
    return point_sources.drop([lat_name, lon_name], axis=1)


def calculate_sum_points(
    point_src: gpd.GeoDataFrame, wrf_grid: gpd.GeoDataFrame
) -> pd.DataFrame:
    """Calculate sum of emissions from each point sources in a wrf grid cell.

    Args:
        point_src: GeoDataFrame of point sources.
        wrf_grid: WRF domain grid

    Returns:
        Sum of emission in each grid.
    """
    point_in_grid = gpd.overlay(point_src, wrf_grid, how="intersection")
    points_in_grid = point_in_grid.dissolve("ID", aggfunc="sum")
    return points_in_grid.drop(["geometry"], axis=1)


def create_emiss_point(
    point_src: gpd.GeoDataFrame, wrf_grid: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """Create emiss point.

    Complete wrf grid cell with no point sources emissions with 0.
    TODO: change name of this function.

    Args:
        point_src: GeoDataFrame of point sources.
        wrf_grid: WRF domain grid

    Returns:
        Complete grid with total emission in wrf domain grid.
    """
    points_in_grid = calculate_sum_points(point_src, wrf_grid)
    return wrf_grid.join(points_in_grid).fillna(0)


def retrive_proj_from(geogrid_path: str):
    """Extract projection of geo_em.d0x.nc file.

    Args:
        geogrid_path: Location of geo_em.d0x.nc file.

    Returns:
        Projection of geo_em.d0x.nc
    """
    geo_ds = xr.open_dataset(geogrid_path)
    a = 6370000.0
    b = 6370000.0

    lcc = pyproj.Proj(proj='lcc', lat_1=geo_ds.TRUELAT1, lat_2=geo_ds.TRUELAT2, 
                      lat_0=geo_ds.MOAD_CEN_LAT, lon_0=geo_ds.STAND_LON, 
                      a=a, b=b)
    merc = pyproj.Proj(proj='merc', lon_0=geo_ds.STAND_LON, lat_ts=geo_ds.TRUELAT1,
                       a=a, b=b)
    stere = pyproj.Proj(proj='stere', lat_0=geo_ds.TRUELAT1, lon_0=geo_ds.STAND_LON,
                        lat_ts=geo_ds.TRUELAT1, a=a, b=b)
    latlon = pyproj.Proj(proj='longlat', lon_0=geo_ds.STAND_LON, a=a, b=b)

    proj_codes = {
        1: lcc, # lambert
        2: stere, # polar
        3: merc, # merc 
        6: latlon # latlon
    }
    
    wrf_proj = proj_codes[geo_ds.MAP_PROJ]
    wrf_crs = pyproj.CRS.from_proj4(str(wrf_proj))
    return wrf_crs


def calculate_centroid(emiss_point: gpd.GeoDataFrame, geo_path: str) -> pd.DataFrame:
    """Calculate centroid of each WRF domain grid cell.

    Args:
        emiss_point: Total emissions in each wrf domain cell.
        geo_path : Location of geo_em.d0x.nc file.

    Returns:
       A DataFrame with total emissions from point sources with cell centroid coordinates.
    """
    wrf_proj = retrive_proj_from(geo_path)
    emiss_point_proj = emiss_point.to_crs(wrf_proj)
    emiss_point_proj["centro"] = emiss_point_proj.centroid
    emiss_point_proj["centro"] = emiss_point_proj.centroid.to_crs("EPSG:4326")
    emiss_point_proj["x"] = emiss_point_proj.centro.x.round(4)
    emiss_point_proj["y"] = emiss_point_proj.centro.y.round(4)
    return emiss_point_proj.drop(["geometry", "centro", "ID"], axis=1)


def pol_column_to_xarray(
    emiss_point_proj: pd.DataFrame, pol_col: str, ncol: int, nrow: int
) -> xr.DataArray:
    """Transform pollutant column to xr.DataArray

    Args:
        emiss_point_proj: Total emissions in cell grid with centroid.
        pol_col: Pollutant column name.
        ncol: Number of columns of wrfinput.
        nrow: Number of rows of wrfinput.

    Returns:
        Total emission of a pollutant in xr.DataArray.
    """
    lat = emiss_point_proj["y"].values.reshape(nrow, ncol)
    lon = emiss_point_proj["x"].values.reshape(nrow, ncol)
    pol = emiss_point_proj[pol_col].values.reshape(nrow, ncol)

    pol_xa = xr.DataArray(
        pol,
        dims=("south_north", "west_east"),
        coords={
            "XLAT": (("south_north", "west_east"), lat),
            "XLONG": (("south_north", "west_east"), lon),
        },
    )
    pol_xa.name = pol_col
    return pol_xa


def point_emiss_to_xarray(
    emiss_point_proj: pd.DataFrame, ncol: int, nrow: int
) -> xr.Dataset:
    """Transform point sources dataframe into a xr.Dataset.

    Args:
        emiss_point_proj: Total emissions in cell grid with centroid.
        ncol: Number of columns of wrfinput.
        nrow: Number of rows of wrfinput.

    Returns: Total emission in xr.Dataset.
    """
    pol_names = emiss_point_proj.columns.to_list()
    pol_names = [pol for pol in pol_names if pol not in ["x", "y"]]
    emiss_point = [
        pol_column_to_xarray(emiss_point_proj, pol, ncol, nrow) for pol in pol_names
    ]
    return xr.merge(emiss_point)


def read_point_sources(
    point_path: str,
    geo_path: str,
    ncol: int,
    nrow: int,
    sep: str = "\t",
    lat_name: str = "LAT",
    lon_name: str = "LON",
) -> xr.Dataset:
    """
    Read point sources .csv file to produces a xr.Dataset.

    Args:
        point_path: Location of point sources .csv file.
        geo_path: Location of geo_em.d0X.nc file.
        sep: Column separator of point sources .csv file.
        lat_name: Latitude column name.
        lon_name: Longitude column name.

    Returns:
        Total emissions of point sources in each WRF domain cell xr.Dataset.
    """
    point_sources = create_gpd_from(point_path, sep, lat_name, lon_name)
    wrf_grid = create_wrf_grid(geo_path, save=False)
    wrf_grid = configure_grid_spatial(wrf_grid, point_sources)
    # Ensure points inside domain
    point_sources = gpd.clip(point_sources, wrf_grid)

    emiss_in_grid = create_emiss_point(point_sources, wrf_grid)
    emiss_in_grid = calculate_centroid(emiss_in_grid, geo_path)
    return point_emiss_to_xarray(emiss_in_grid, ncol, nrow)
