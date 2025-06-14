from siem.siem import EmissionSource
from siem.spatial import read_spatial_proxy
import xarray as xr


def test_wrfchemi_pm_sum() -> None:
    wrfinput = xr.open_dataset("./tests/test_data/wrfinput_d01_siem_test")
    _, ncol, nrow = wrfinput.XLAT.values.shape

    spatial_proxy = read_spatial_proxy(
        "./tests/test_data/highways_hdv.csv",
        (nrow, ncol), ["id", "x", "y", "longkm"],
        proxy="longkm")

    temporal_profile = [1 / 24 for n in range(24)]
    week_profile = [1 for n in range(7)]

    gasoline_ef = {"CO": (0.173, 28),
                   "NO2": (0.010, 64),
                   "VOC": (0.012, 100),
                   "PM": (0.001, 1)}
    pm_spc = {"PM2_5": 0.8, "PMC": 0.2}
    voc_spc = {"ETH": 0.8, "HC8": 0.2}

    gaso_emiss = EmissionSource(
        name="Gasoline",
        number=1_000_000,
        use_intensity=41,
        pol_ef=gasoline_ef,
        spatial_proxy=spatial_proxy,
        temporal_prof=temporal_profile,
        voc_spc=voc_spc,
        pm_spc=pm_spc
    )

    pm_total = 1_000_000 * gasoline_ef["PM"][0] * 41 * 365    # g year^-1
    pm_siem = gaso_emiss.total_emission("PM") * 365           # g year^-1

    gaso_wrf = gaso_emiss.to_wrfchemi(
        wrfinput=wrfinput,
        start_date="2024-01-01",
        end_date="2024-01-01",
        week_profile=week_profile
    )

    btrim = 0
    gaso_cmaq = gaso_emiss.to_cmaq(
            wrfinput=wrfinput,
            griddesc_path="./tests/test_data/GRIDDESC",
            btrim=btrim,
            start_date="2024-01-01",
            end_date="2024-01-01",
            week_profile=week_profile
            )
    

    # g/year     =  ug/m2/s       * s/hr *  g/ug      *   m2         * day/hr * year/day
    wrf_total_pm = (gaso_wrf.E_PM * 3600 * (10 ** -6) * wrfinput.DX**2).sum() * 365

    wrf_pm_spc = ((gaso_wrf.E_PM2_5 * 3600 * (10 ** -6) * (9 * 10 ** 6)).sum() * 365 +
                  (gaso_wrf.E_PMC * 3600 * (10 ** -6) * (9 * 10 ** 6)).sum() * 365)

    wrf_btrim = gaso_wrf.isel(
            south_north=slice(1, 13),
            west_east=slice(1, 23)
                              )
    wrf_btrim_pm = (wrf_btrim.E_PM * 3600 * 9).sum() * 365

    # g/s
    cmaq_total_pm = (
        (gaso_cmaq["2024-01-01"].sel(TSTEP=slice(0,24)).PM2_5 * 3600 ) +
        (gaso_cmaq["2024-01-01"].sel(TSTEP=slice(0,24)).PMC * 3600 )
            ).sum() * 365

    print(f"total pm: {pm_total:_}")
    print(f"wrf_pm_total: {wrf_total_pm:_}")
    print(f"wrf_pm_spc_total: {wrf_pm_spc:_}")
    print(f"cmaq_total: {cmaq_total_pm:_}")

    print(f"wrf_btrim: {wrf_btrim_pm:_}")

    assert isinstance(spatial_proxy, xr.DataArray)
    assert len(temporal_profile) == 24
    assert len(week_profile) == 7
    assert isinstance(gaso_emiss, EmissionSource)
    assert pm_total - pm_siem <= 1e10-9
    assert "E_PM" in gaso_wrf.data_vars
    assert len(gaso_wrf.Time) == 24
    assert pm_total - wrf_total_pm <= 1.0
    assert wrf_btrim_pm - cmaq_total_pm <= 1.0

    assert "PM" not in gaso_cmaq["2024-01-01"].data_vars
