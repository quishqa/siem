from siem.proxy import download_highways, download_point_sources


if __name__ == "__main__":
    wrf_path = "../data/geo_em.d02.nc"
    highways_hdv = ["primary"]
    highways_ldv = highways_hdv + ["secondary", "tertiary", "residential"]

    from datetime import datetime

    print(f"Starting at: {datetime.now()}")

    SP = download_highways(wrf_path, highways_hdv, add_links=False,
                           save=True, file_name="prim",
                           save_path="../data/partial/")

    print(f"Ending at: {datetime.now()}")
    print(type(SP))

    fuel = download_point_sources(wrf_path, tags={"amenity": "fuel"})
