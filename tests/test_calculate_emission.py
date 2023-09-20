from siem.siem import calculate_emission


def test_calculate_emission() -> None:
    assert calculate_emission(10, 10, 10) == 10 ** 3
