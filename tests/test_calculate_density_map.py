from siem.siem import calculate_emission
from siem.spatial import read_spatial_proxy
from siem.spatial import calculate_density_map
from siem.spatial import distribute_spatial_emission


def test_calculate_density_map() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                       ["id", "x", "y","main", "lon", "urban"])
    number_source = 1_000_000
    cell_area = 10
    density_map = calculate_density_map(spatial_proxy,
                                        1_000_000,
                                        10)
    assert density_map.sum() * cell_area == number_source


def test_distribute_spatial_emission() -> None:
    spatial_proxy = read_spatial_proxy("./data/ldv_s3.txt",
                                      ["id", "x", "y","main", "lon", "urban"])
    spatial_emission = distribute_spatial_emission(spatial_proxy,
                                                   number_sources=1_000_000,
                                                   cell_area=1,
                                                   use_intensity=1,
                                                   pol_ef=1,
                                                   pol_name="NOX")
    total_emission = calculate_emission(1_000_000, 1, 1)
    assert spatial_emission.sum() == total_emission

