# Tutorials

`siem` works with three classes to define our emissions:

- `EmissionSource`: Mainly built to calculate and distribute vehicular emissions using a spatial proxy.
- `PointSource`: Mainly built to distribute point emissions that are loaded in a table (i.e. `.csv` file).
- `GroupSources`: Built to merge all the `EmissionSource` and `PointSource` object in one single object.
Useful to create the final emission that goes to the air quality model.

Each of theses objects has the `.to_wrfchem` and `.to_cmaq` methods that allows to create the emission file for WRF-Chem and CMAQ respectively.

## Defining emissions attributes

Because emissions varies in space, in time, in species, these factors need to be defined in `EmissionSource` and `PointSource` attributes.
Let's start by explaining how to define them.

### Spatial proxy

The spatial proxy is a file that have the weights (ratios) to spatially distribute an **n** number of sources (i.e. vehicles) in the simulation domain.
For that reason it is required to have the same number of `west_east` and `south_north` points in the `wrfinput` file.

A spatial proxy file has the following format:

```bash
159 -46.60239219665527 -24.044368743896484 0.0
160 -46.59200668334961 -24.044368743896484 0.0
161 -46.581621170043945 -24.044368743896484 0.0
162 -46.57123374938965 -24.044368743896484 0.0
163 -46.560848236083984 -24.044368743896484 0.0
164 -46.55046272277832 -24.044368743896484 0.0
165 -46.54007530212402 -24.044368743896484 1.7393638309449484
166 -46.52968978881836 -24.044368743896484 4.358224109569712
167 -46.519304275512695 -24.044368743896484 2.098392445514633
168 -46.5089168548584 -24.044368743896484 0.0
169 -46.498531341552734 -24.044368743896484 0.0
```

The first column is the **id**, the second column is the **longitude**, the third column is the **latitude**,
and the fourth column is the weight of the emissions sources.

So, to prepare these file to be used in `EmissionSource`, we use the `read_spatial_proxy()` function from the `spatial` module.
Let's imagine that the proxy represents the gasoline vehicles.

```python
from siem.spatial import read_spatial_proxy

gasoline_spatial_proxy = read_spatial_proxy(
  proxy_path='./spatial_proxy.csv',
  shape=(100, 100),
  col_names=['id', 'x', 'y', 'emiss_weight'],
  proxy='emiss_weight',
  lon_name='x',
  lan_name='y'
)
```

### Temporal profile

The temporal is just a list with at least 24 elements (hourly weight), one for each hour of the day.
It has to be in **UTC**.

For example a temporal profile for gasoline vehicles can be defined as:

```python
gasoline_temp_prof = [
    0.020, 0.010, 0.010, 0.004, 0.003, 0.003,
    0.010, 0.020, 0.050, 0.080, 0.080, 0.064,
    0.060, 0.052, 0.050, 0.050, 0.050, 0.057,
    0.070, 0.090, 0.090, 0.060, 0.040, 0.034
    ]
```

The temporal profile can also be a column of a data frame.

### Pollutant emission factors

The pollutant emission factors are defined using a `dict()`.
The dictionary keys are the names of pollutants in the emission inventory.
The dictionary values are a `tuple` where the first element is the emission factors (g day^-1),
and the second element is the molecular weight (g mol^-1).

Following the gasoline vehicles, we can define its emission factors as:

```python
gasoline_ef = {
  "CO": (0.173, 28),
  "NO": (0.010, 30),
  "RCHO": (0.0005, 32),
  "VOC": (0.012, 100),
  "PM": (0.001,1)
}
```

In this example, we define the emission factor of CO (carbon monoxide),
NO (nitrogen monoxide), RCHO (aldehydes), VOC (Volatile Organic Compound),
and PM (Particulate Matter).

!!! warning "About VOC and PM emission factors"

    It is required to have "VOC" and "PM" keys on the dictionary,
    as they will be latter speciated. If there is no information, you can zero them by
    using `VOC: (0, 100)` or `PM: (0, 1)`. Also, **PM molecular weight is always 1**.

### VOC and PM speciation

Many chemical mechanisms and aerosol modules use different species for both VOC and PM.
`siem` speciation is based on **percentage of total emissions**.
The speciation is also saved in a `dict()`,
where the keys are the VOC or PM species of the selected chemical mechanism or module aerosol,
and the values are the percentage of the total VOC or PM emissions.

For example, for CBMZ and MOSAIC we can have:

```python
gasoline_voc_cbmz = {
    "ETH": 0.282625, "HC3": 0.435206, "HC5": 0.158620,
    "HC8": 0.076538, "OL2": 0.341600, "OLT": 0.143212,
    "OLI": 0.161406, "ISO": 0.004554, "TOL": 0.140506,
    "XYL": 0.157456, "KET": 0.000083, "CH3OH": 0.001841
}

gasoline_pm_mosaic = {
    "PM25I": 0.032,
    "PM25J": 0.096,
    "SO4I": 0.0024,
    "SO4J": 0.0156,
    ....
}
```

Therefore, `siem` can be used for different chemical mechanism as the speciation is defined by the user and the available information.

## Creating an `EmissionSource` object

Once we have and prepare the emission information, we can now create the object.
In the following example,
We will create an `EmissionSource` object that save information of all the **gasoline vehicles** of a city.
Let's imagine that there are **1 000 000 of these vehicles**, and on average they run **13 495 km per year**.
So:

```python
from siem.siem import EmissionSource

gasoline = EmissionSource(
    name="Gasoline vehicles",
    number=1_000_000,
    use_intensity= 13_495/365,  # km day ^ -1
    pol_ef=gasoline_ef,
    spatial_proxy=gasoline_spatial_proxy,
    temporal_profile=temp_prof,
    voc_spc=gasoline_voc_cbmz,
    pm_spc=gasoline_pm_mosaic
)
```

We can create another object with the information of diesel vehicles.
Let us assume that there are **40 000** diesel vehicles that run the same as the gasoline vehicles.

```python
diesel = EmissionSource(
    name="Diesel vehicles",
    number=40_000,
    use_intensity= 13_495/365,  # km day ^ -1
    pol_ef=diesel_ef,
    spatial_proxy=diesel_spatial_proxy,
    temporal_profile=diesel_temp_prof,
    voc_spc=diesel_voc_cbmz,
    pm_spc=diesel_pm_mosaic
)
```

!!! note "About the diesel example"

    Notice that `diesel` is define using different attributes
    (i.e. different spatial proxy, temporal profile, speciation, etc).
    If you have the information each EmissionSource can have different 
    attributes, otherwise, you can repeat the attributes for other EmissionSource.

## Creating an `PointSource` object

Now, if you have an emission file in `.csv` with point information total emission (kT year^-1),
you can use `PointSource` to load the emissions,
but first you need to read the `.csv`

### Reading point source `.csv` file

We use the function `read_point_sources()` from `point` module to prepare our `.csv` file.
This function will sum each of the point sources located inside domain cells.

```python
import xarray as xr
from siem.point import read_point_sources

geogrid = xr.open_dataset('./geo_em.d01.nc')
_, nrow, ncol = geo.XLAT_M.shape

point_dom = read_point_sources(
  point_path='./city_industries.tsv',
  geo_path='./geo_em.d01.nc',
  ncol=ncol, 
  nrow=nrow,
  sep='\t', 
  lat_name='LAT',
  lon_name='LON'
)
```

### Defining emission molecular weight

Because the `.csv` file already have the total emissions calculate,
we do not need the emission factors,
`PointSource` only needs the molecular weight of the emissions.
We define it using a `dict()`.

```python
pol_mw = {
  'CO': 12 + 14,
  'SO2': 32 + 2 * 16,
  'NO2': 14 + 2 * 16,
  'VOC': 100, 
  'PM': 1
}
```

!!! warning "About VOC and PM molecular weight"

    As in the case of `EmissionSource`, it is required to have "VOC" and "PM" keys on the dictionary,
    as they will be latter speciated.

### Defining `PointSource`

Now we can create our `PointSource` as following:

```python
city_point_source = PointSources(
  name='City industries',
  point_emiss=point_dom,
  pol_emiss=pol_mw,
  temporal_profile=ind_temp_prof,
  voc_spc=ind_voc_cbmz,
  pm_spc=ind_pm_cbmz
)
```

`temporal_profile`, `voc_spc`, and `pm_spc` are defined the same as in `EmissionSource`.

## Creating a `GroupSources` object

Once you defined all the emissions sources in your domain,
you need to group all of them to built the anthropogenic emission file require to run the air quality models.
To that goal we used `GroupSources`.

Following what we build in this tutorial, we can do the following:

```python
from siem.siem import GroupSources

city_sources = [city_point_source, gasoline, diesel]
city_anthro_emiss = GroupSources(city_sources)
```

That's it!

Now if you want to create emission files for WRF-Chem, you can do:

```python
import xarray as xr
wrfinput_d01 = xr.open_dataset('./wrfinput_d01')

city_anthro_emiss.to_wrfchemi(
  wrfinput=wrfinput_d01,
  start_date='2025-10-01',
  end_date='2025-10-01',
  week_profile=week_profile,
  write_netcdf=True
)
```

And for CMAQ:

```python
import xarray as xr
wrfinput_d01 = xr.open_dataset('./wrfinput_d01')


city_anthro_emiss.to_wrfchemi(
  wrfinput=wrfinput_d01,
  griddesc_path='./GRIDDESC',
  btrim=5,
  start_date='2025-10-01',
  end_date='2025-10-01',
  week_profile= week_profile,
  write_netcdf=True
)
```
