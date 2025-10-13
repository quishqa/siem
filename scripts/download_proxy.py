"""
This is an example to download highways data from OSM
to build the proxy file.

"""

from siem.proxy import download_highways


if __name__ == "__main__":
    wrf_path = "../data/geo_em.d02.nc"
    highways_hdv = ["primary", "trunk", "motorway"]
    highways_ldv = highways_hdv + ["secondary", "tertiary", "residential"]

    from datetime import datetime

    print(f"Starting at: {datetime.now()}")

    SP = download_highways(
        wrf_path,
        highways_hdv,
        add_links=False,
        save=True,
        file_name="hdv_d02",
        save_path="../data/partial/",
    )

    print(f"Ending at: {datetime.now()}")
    print(type(SP))
