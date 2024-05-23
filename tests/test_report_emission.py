import pandas as pd
from siem.siem import EmissionSource

def test_report_emission() -> None:
    emiss_source = EmissionSource("Test",
                                  1_000_000,
                                  1,
                                  {"NOX": (1., 30), 
                                   "CO": (2., 14 + 16)},
                                  [],
                                  [],
                                  {},
                                  {})
    total_nox_kTnYear = 1_000_000 * 365 / 10 ** 9
    total_co_kTnYear = 2_000_000 * 365 / 10 ** 9

    nox_total = emiss_source.total_emission("NOX", ktn_year=True)
    co_total = emiss_source.total_emission("CO", ktn_year=True)

    total_emiss = emiss_source.report_emissions()

    assert isinstance(total_emiss, pd.DataFrame)
    assert total_emiss.total_emiss.sum() -  (nox_total + co_total) < 1e-10
    



