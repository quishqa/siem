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

## How to create WRF-Chem emission file

All `siem` objects have the method `.to_wrfchemi()` that is used to build the WRF-Chem emission file.
Let's create the emission file of the gasoline vehicles emissions in the tutorial example.

``` python
gasoline = EmissionSource(
  name="Gasoline vehicles",
  number=1_000_000,
  use_intensity=13_495/365,
  spatial_proxy=gasoline_spatial_proxy,
  temporal_profile=temp_prof,
  voc_spc=gasoline_voc_cbmz,
  pm_spc=gasoline_pm_mosaic
)
```

So, to create the emission file we can do:

```python

wrfinput_d01 = xr.open_dataset('./wrfinput_d01')

gasoline.to_wrfchemi(
  wrfinput=wrfinput_d01,
  start_date='2025-10-01',
  end_date='2025-10-01',
  week_profile=[1],
  pm_name='PM',
  voc_name='VOC',
  write_netcdf=True,
  nc_format='NETCDF3_64BIT',
  path='./'
)
```

This code chunk will produce the wrfchemi file in `io_style_emissions=1`.
That is a standard emission file split in 12 hours: `wrfchemi_00z_d01` and `wrfchemi_12z_d01`.

To create the wrfchemi file in `io_style_emissions=2`, we need to play with `start_date`, `end_date`, and `week_profile` arguments.
First if we want emission for a week, we can change the range of the start and end dates.

But if we want to add a week of the day variation, for example, lets say that on the weekends we have half the emissions of the weekday,
we can define this variations by a `list()` with seven elements going from Monday to Sunday.

```python hl_lines="2 7 8"

wrfinput_d01 = xr.open_dataset('./wrfinput_d01')
week_profile = [1, 1, 1, 1, 1, 0.5, 0.5]

gasoline.to_wrfchemi(
  wrfinput=wrfinput_d01,
  start_date='2025-10-01',
  end_date='2025-10-07',
  week_profile=week_profile,
  pm_name='PM',
  voc_name='VOC',
  write_netcdf=True,
  nc_format='NETCDF3_64BIT',
  path='./'
)
```

This code will produce the file `wrfchemi_d01_2025-10-01_00:00:00`,
and the weekends will have half the emissions of the week of the day.

!!! tip "Checking the times of wrfchemi files"

    You can use the command:
    ```
    ndump -v Times wrfchemi_d01_2025-10-01_00
    ```
    To check the number of times, and the start and end date of the emission files
    Also to check the day of the week variation, you can use `ncview`.

## How to create CMAQ file

Something similar is required to create the emission files for CMAQ.
The main difference is the need of extra inputs, the **`GRIDDESC``** file and the **`BTRIM`** value.
That is the output of MCIP outputs.

In this case we use the `.to_cmaq()` method. Following the same example:

```python hl_lines="6 7"

wrfinput_d01 = xr.open_dataset('./wrfinput_d01')
week_profile = [1, 1, 1, 1, 1, 0.5, 0.5]

gasoline.to_cmaq(
  wrfinput=wrfinput_d01,
  griddesc_path='./GRIDDESC',
  btrim=5,
  start_date='2025-10-01',
  end_date='2025-10-07',
  week_profile=week_profile,
  pm_name='PM',
  voc_name='VOC',
  write_netcdf=True,
  path='./'
)
```

This will create a daily emission file, one for each day of the range between start and end dates.

!!! warning Week profile

    `to_cmaq()` requires a `week_profile` of at least 7 elements.
    If there is no information available you can make a list full of ones.
