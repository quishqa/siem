from siem.point import retrive_proj_from
import pyproj

def test_retrieve_proj_from() -> None:
    geo_path = "./tests/test_data/geo_em.d01.siem_test.nc"

    wrf_proj = retrive_proj_from(geo_path)

    assert isinstance(wrf_proj, pyproj.crs.crs.CRS)
