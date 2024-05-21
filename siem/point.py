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


def point_sources_to_dataset(point_path: str, geo_path: str, sep: str = "\t",
                             lat_name: str = "LAT", lon_name: str = "LON"
                             ) -> xr.Dataset:
    point_sources = create_gpd_from(point_path, sep, lat_name, lon_name)
    wrf_grid = create_wrf_grid(geo_path, save=False)
    wrf_grid = configure_grid_spatial(wrf_grid, point_sources)
    # Ensure points inside domain
    point_sources = gpd.clip(point_sources, wrf_grid)

    emiss_in_grid = create_emiss_point(point_sources, wrf_grid)
    emiss_in_grid = calculate_centroid(emiss_in_grid, geo_path)
    return point_emiss_to_xarray(emiss_in_grid)

