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

```python
from siem.spatial import read_spatial_proxy

spatial_proxy = read_spatial_proxy(
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
