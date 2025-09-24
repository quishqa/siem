# How-to guides

## How to create the spatial proxy

`siem` comes with functions to create a spatial proxy for vehicular emissions using the [OpenStreetMap](https://www.openstreetmap.org/about) data.
It follows the methodology to spatially distributes emissions described in [Andrade et al. (2015)](https://www.frontiersin.org/journals/environmental-science/articles/10.3389/fenvs.2015.00009/full).

To create the spatial proxy we need to:

- Download the highways data from OpenStreetMap.
- Calculate proxy.

### Download highways data

For this example we will download the `primary`, `motorway`, and `trunk` highways,
to distributes our vehicular emissions.

!!! note "List of highways types to download"

    You can see a list of highways to download from this site:
    [key:highways](https://wiki.openstreetmap.org/wiki/Key:highway).
    See what is the best highway to distribute the vehicular emissions.

To this goal we use `download_highways()` function from `proxy` module.

```python
from siem.proxy import download_highways

geogrid_path = './geo_em.d01.nc'
highways_list = ['primary', 'motorway', 'trunk']

city_highways = download_highways(
  geo_em_path=geogrid_path,
  highway_type=highways_list,
  add_links=False,
  save=True,
  save_path='./highway_data/partial',
  file_name='highways_d01'
)
```

Depending on the domain size and the number of highways types it could take some time.
It will save data in `./highway_data/partial/domain_highways_d01.graphml`

!!! tip "The download could take a lot of time"

    You can leave the process running in the background by saving it 
    in a python script and running by:
    ```bash
    nohup python download_proxy.py &
    ```

### Calculate proxy

Now that you have the highways data, we need to calculate the proxy.
That is, we need to calculate the weight in each domain cell.
`siem` assume that the **number of vehicles** inside a domain cell is proportional to the **sum of highways lengths** inside that cell.

To do this calculation, and create the proxy file ready to use in `EmissionSorce`,
we use the `create_wrf_grid()`, `load_osmx_to_gdfs()`, and `calculate_highway_grid()` functions from `proxy` module.

```python
from siem.proxy import (create_wrf_grid, load_osmx_to_gdfs, calculate_highway_grid)

geogrid_path = "./geo_em.d01.nc"
highways_path = "./highways_data/partial/domain_highways_d01.graphml"

highways = load_osmx_to_gdfs(highways_path)
wrf_grid = create_wrf_grid(geogrid_path)
highways_in_grid = calculate_highway_grid(
  wrf_grid=wrf_grid,
  proxy=highways,
  to_pre=True,
  save_pre="./highways_data/",
  file_name="d01"
)

```

This script will create the `.csv` (`./highways_data/highways_d01.csv`) to be used in `EmissionSorce`.

## How to create WRF-Chem `io_style_emissions = 1` file

## How to create WRF-Chem `io_style_emissions = 2` file

## How to create CMAQ file
