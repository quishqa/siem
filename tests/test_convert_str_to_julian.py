from siem.cmaq import convert_str_to_julian


def test_convert_str_to_julian() -> None:
    date = "2018-07-01"
    date_julian = convert_str_to_julian(date)

    assert isinstance(date_julian, int)
    assert date_julian == 2018182


def test_convert_str_to_julian_fmt() -> None:
    date = "20180701"
    date_julian = convert_str_to_julian(date, fmt="%Y%m%d")

    assert isinstance(date_julian, int)
    assert date_julian == 2018182

