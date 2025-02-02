import os
import numpy as np
import pandas as pd
import xarray as xr
from siem.point import read_point_sources
from siem.emiss import ktn_year_to_ug_seg, ktn_year_to_mol_hr


def test_calculate_centroid() -> None:
    geo_path = "./tests/test_data/geo_em.d01.siem_test.nc"
    geo = xr.open_dataset(geo_path)
    lat = np.arange(geo.XLAT_M.min(), geo.XLAT_M.max(), 0.05)
    lon = np.linspace(geo.XLONG_M.min(), geo.XLONG_M.max(), len(lat))
    so2 = np.random.random(len(lat)) * 10
    no2 = np.random.random(len(lat)) * 100
    pm = np.random.random(len(lat)) * 100

    sample = pd.DataFrame.from_dict({
        "LAT": lat,
        "LON": lon,
        "so2": so2,
        "no2": no2,
        "PM": pm})

    sample.to_csv("sample_geo.csv", sep="\t", index=False)

    emiss_ready = read_point_sources("sample_geo.csv", geo_path,
                                     "\t", "LAT", "LON")
    os.remove("sample_geo.csv")

    so2 = emiss_ready["so2"]
    so2_mw = 32 + 2 * 16
    convert_factor = 1000 * 1000 / (365 * 24 * so2_mw)
    so2_mol_hr = ktn_year_to_mol_hr(so2, so2_mw)

    pm_emi = emiss_ready["PM"]
    pm_factor = 1000 * 1000 * 10 ** 6 / (365 * 24 * 3600)
    pm_ug_s = ktn_year_to_ug_seg(pm_emi)

    assert isinstance(so2_mol_hr, xr.DataArray)
    assert isinstance(pm_ug_s, xr.DataArray)
    assert (so2 * convert_factor).sum() - so2_mol_hr.sum() <= 1e-10
    assert (pm_emi * pm_factor).sum() - pm_ug_s.sum() <= 1e-10
