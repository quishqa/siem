from siem.cmaq import create_date_range


def test_creat_date_range() -> None:
    start_date = "2018-07-01"
    end_date = "2018-07-07"

    date_range = create_date_range(start_date, end_date)

    assert len(date_range) == 7
