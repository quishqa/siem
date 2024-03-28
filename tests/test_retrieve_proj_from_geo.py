from siem.point import retrive_proj_from
import cartopy.crs as ccrs

def test_retrieve_proj_from() -> None:
    geo_path = "data/geo_em.d02.nc"

    wrf_proj = retrive_proj_from(geo_path)

    assert isinstance(wrf_proj, ccrs.Projection)
