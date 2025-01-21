# siem: SImplied Emission Model

This is the SImplified Emission Model. 
It is a python package to create the emission 
file for [WRF-Chem](https://www2.acom.ucar.edu/wrf-chem) and [CMAQ](https://www.epa.gov/cmaq) air quality models.

It is inspired on the work of [Andrade et al. (2025)](http://journal.frontiersin.org/Article/10.3389/fenvs.2015.00009/abstract), 
[AAS4WRF](https://github.com/alvv1986/AAS4WRF), and [PyChEmiss](https://github.com/quishqa/PyChEmiss). 

`siem` main objective is to create the emission file for cities with scarce emission data.

## Installation

1. Clone this repository:

```
git clone git@github.com:quishqa/siem.git
```

2. Enter the main folder and create the `siem` environment by using:
```
conda env create -f environment.yml

```
3. Finally, install `siem` by using:
```
pip install -e .
```

## How to use.

`siem` has three classes: `EmissionSource`, `PointSource`, and `GroupSources`.

- `EmissionSource`: It is used to calculate and distribute emissions by using a spatial proxy.
- `PointSource`: It is used to distribute point emissions from a table.
- `GroupSources`: It is used to merge `EmissionSource` objects and `PointSource` objects into a single object. Useful to create the final emission file.

Each of these objects has the methos `to_wrfchem` and `to_cmaq` that allow us to create the emission file for WRF-Chem and CMAQ respectively.

### `EmissionSource`

`EmissionSource` is the principal class in `siem`. It foster the main variables of an emission source:
its name, its spatial and temporal distribution, its pollutants emission factors, and the speciation of PM and VOC.
We'll tackle how to define this variables in this section.

#### Spatial distribution

To create a EmisionSource object you first need to have a spatial proxy file.
This file has to have __the same number of points in your `wrfinput` file `west_east` and `south_north` coordinates__.

Let's imagine that you have this file called `spatial_proxy.csv`,
 where the first column is the id, the second column is the longitude,
 the third column is the latitude, and the fourth column is the weight of emission.

```
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

So, we read this file using the `read_spatial_proxy()` from the `spatial` module. Therefore:

```python
from siem.spatial import read_spatial_proxy


spatial_proxy = read_spatial_proxy(
    proxy_path="./spatial_proxy.csv",
    shape = (100, 100), # (ncol, nrow) of spatial_proxy.csv, (west_east points, south_north points)
    col_names=["id", "x", "y", "emiss_weight"],
    proxy="emiss_weight",
    lon_name="x",
    lat_name="y"
)
```

#### Temporal profile

The temporal profile is just a list with at least 24 elements. 
One element for each hour of the day. Remeber that it has to be define __in UTC__.

```python
gasoline_temp_prof = [
    0.020, 0.010, 0.010, 0.004, 0.003, 0.003,
    0.010, 0.020, 0.050, 0.080, 0.080, 0.064,
    0.060, 0.052, 0.050, 0.050, 0.050, 0.057,
    0.070, 0.090, 0.090, 0.060, 0.040, 0.034
    ]
```
#### Pollutant emission factors

The pollutant emission factors are defined using a `dict()`. 
The keys are the names of pollutants in the emission inventory,
and the values are a `tuple` with the emission factor (g day^-1) and the molecular weigth (g mol^-1).

```python
gasoline_ef = {
    "CO": (0.173, 28), "NO": (0.010, 30),
    "RCHO": (0.0005, 32), "VOC": (0.012, 100),
    "PM": (0.001, 1)
}
```

In this example, we define the emission factor of CO, NO, RCHO, VOC, and PM. 
Notice that it is required to have "VOC" and "PM" in the dictionary as these pollutants will next be speciated.
It there is no information about these pollutants you can just do `VOC: (0.0, 100)` or `PM: (0.0, 1)`.
#### VOC and PM speciation


#### Building the object

Finally, to define an emission source, like Gasoline Vehicles we used the `EmissionSource` class:

```
from siem.siem import EmissionSource

gasoline = EmissionSource(
    name="Gasoline vehicles",
    number=1_000_000,
    use_intensity= 13_495/365,
    pol_ef=gasoline_ef,
    temporal_profile=temp_prof,
    voc_spc=gasoline_voc_ef,
    pm_spc=gasoline_pm_spc
)
```

### `PointSource` 

### `GroupSources`

