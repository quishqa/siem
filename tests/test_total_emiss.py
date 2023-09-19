from siem.siem import EmissionSource


def test_total_emiss_default() -> None:
    emiss_source = EmissionSource("Test",
                                  1_000_000,
                                  1,
                                  {"NOX": 1.},
                                  [],
                                  [])
    assert emiss_source.total_emiss("NOX") == 1_000_000


def test_total_emiss_kTn_year() -> None:
    emiss_source = EmissionSource("Test",
                                  1_000_000,
                                  1,
                                  {"NOX": 1.},
                                  [],
                                  [])
    assert emiss_source.total_emiss("NOX", ktn_year=True) == 1_000_000 * 365 / 10 **9 



