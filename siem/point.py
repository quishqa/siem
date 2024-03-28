import pandas as pd
import geopandas as gpd
import xarray as xr
from netCDF4 import Dataset
from wrf import getvar, get_cartopy


def create_gpd_from(point_src_path: str, sep: str = "\t",
                    lat_name: str = "LAT", lon_name: str = "LON",
                    ) -> gpd.GeoDataFrame:
    point_sources = pd.read_csv(point_src_path, sep=sep)
    point_sources = gpd.GeoDataFrame(
            point_sources,
            geometry=gpd.points_from_xy(point_sources[lon_name],
                                        point_sources[lat_name]),
            crs="EPSG:4326")
    return point_sources.drop([lat_name, lon_name], axis=1)


def calculate_sum_points(point_src: gpd.GeoDataFrame,
                         wrf_grid: gpd.GeoDataFrame) -> pd.DataFrame:
    point_in_grid = gpd.overlay(point_src, wrf_grid, how="intersection")
    points_in_grid = point_in_grid.dissolve("ID", aggfunc="sum")
    return points_in_grid.drop(["geometry"], axis=1)


def create_emiss_point(point_src: gpd.GeoDataFrame,
                       wrf_grid: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    points_in_grid = calculate_sum_points(point_src, wrf_grid)
    return wrf_grid.join(points_in_grid).fillna(0)


def retrive_proj_from(geogrid_path: str):
    with Dataset(geogrid_path) as geo_dom:
        hgt = getvar(geo_dom, "HGT_M")
    return get_cartopy(hgt)


def calculate_centroid(emiss_point: gpd.GeoDataFrame,
                       geo_path: str) -> pd.DataFrame:
    wrf_proj = retrive_proj_from(geo_path)
    emiss_point_proj = emiss_point.to_crs(wrf_proj)
    emiss_point_proj["centro"] = emiss_point_proj.centroid
    emiss_point_proj["centro"] = emiss_point_proj.centroid.to_crs("EPSG:4326")
    emiss_point_proj["x"] = emiss_point_proj.centro.x.round(4)
    emiss_point_proj["y"] = emiss_point_proj.centro.y.round(4)
    return emiss_point_proj.drop(["geometry", "centro", "ID"], axis=1)


def point_emiss_to_xarray(emiss_point_proj: pd.DataFrame) -> xr.Dataset:
    emiss_point_proj.set_index(["y", "x"], inplace=True)
    return emiss_point_proj.to_xarray()
