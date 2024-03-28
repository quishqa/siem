from siem.point import create_gpd_from
import os
import numpy as np
import pandas as pd
import geopandas as gpd


def test_create_gpd_from() -> None:
    lat: np.ndarray = np.arange(-13, -12.5, 0.05)
    lon: np.ndarray = np.arange(-43, -42.5, 0.05)
    so2: np.ndarray = np.random.random(len(lat)) * 100
    no2: np.ndarray = np.random.random(len(lat)) * 100

    sample = pd.DataFrame.from_dict({
            "lat": lat,
            "lon": lon,
            "so2": so2,
            "no2": no2})

    sample.to_csv("point_sample.csv", sep=",", index=False)

    point_sources = create_gpd_from("point_sample.csv", sep=",",
                                    lat_name="lat", lon_name="lon")

    os.remove("point_sample.csv")

    assert isinstance(point_sources, gpd.GeoDataFrame)
    assert "lat" not in point_sources.columns
    assert "lon" not in point_sources.columns
