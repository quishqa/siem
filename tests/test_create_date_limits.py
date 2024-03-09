from siem.cmaq import create_date_limits


def test_create_date_limits() -> None:
    date = "2018-07-01"
    start, end = create_date_limits(date)

    assert isinstance(start, int)
    assert isinstance(end, int)
    assert start == 2018182
    assert end == 2018183


def test_create_date_limits_new_year() -> None:
    date = "2018-12-31"
    start, end = create_date_limits(date)

    assert start == 2018365
    assert end == 2019001
