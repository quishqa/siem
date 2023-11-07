from siem.siem import EmissionSource


def test_total_emission_default() -> None:
    emiss_source = EmissionSource("Test",
                                  1_000_000,
                                  1,
                                  {"NOX": (1., 30)},
                                  [],
                                  [],
                                  {},
                                  {})
    assert emiss_source.total_emission("NOX") == 1_000_000


def test_total_emission_kTn_year() -> None:
    emiss_source = EmissionSource("Test",
                                  1_000_000,
                                  1,
                                  {"NOX": (1., 30)},
                                  [],
                                  [],
                                  {},
                                  {})
    total_kTnYear = 1_000_000 * 365 / 10 ** 9
    assert emiss_source.total_emission("NOX", ktn_year=True) == total_kTnYear



