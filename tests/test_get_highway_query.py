from siem.proxy import get_highway_query

def test_get_highway_query() -> None:
    highway_types = ["primary", "motorway"]
    my_query = get_highway_query(highway_types)
    assert my_query == '["highway"~"primary|motorway"]'


def test_get_highway_query_link() -> None:
    highway_types = ["primary", "motorway"]
    my_query = get_highway_query(highway_types, add_links=True)
    assert my_query == '["highway"~"primary|motorway|primary_link|motorway_link"]'




