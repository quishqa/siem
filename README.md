# siem: SImplified Emission Model

This is the SImplified Emission Model.
It is a python package to create the emission
file for [WRF-Chem](https://www2.acom.ucar.edu/wrf-chem) and [CMAQ](https://www.epa.gov/cmaq) air quality models.

It is inspired on the work of [Andrade et al. (2015)](http://journal.frontiersin.org/Article/10.3389/fenvs.2015.00009/abstract),
[AAS4WRF](https://github.com/alvv1986/AAS4WRF), and [PyChEmiss](https://github.com/quishqa/PyChEmiss).

`siem` main objective is to create the emission file for cities with scarce emission data.

## Installation

You can install `siem` using pip:

```bash
pip install siem
```

Or you can install the developing version by doing:

```bash
pip install git+https://github.com/quishqa/siem.git
```

## How to use

`siem` has three classes: `EmissionSource`, `PointSource`, and `GroupSources`.

- `EmissionSource`: It is used to calculate and distribute emissions by using a spatial proxy.
- `PointSource`: It is used to distribute point emissions from a table.
- `GroupSources`: It is used to merge `EmissionSource` objects and `PointSource` objects into a single object. Useful to create the final emission file.

Each of these objects has the methods `to_wrfchem` and `to_cmaq` that allow us to create the emission file for WRF-Chem and CMAQ respectively.

You can check the documentation for further details:

- [Tutorials](https://quishqa.github.io/siem/tutorials/)
- [How to guide](https://quishqa.github.io/siem/how-to-guides/)
- Or you can check the `scripts` folder for examples.

## Acknoledgements

We thanks [IAG/USP](https://www.iag.usp.br/), [LAPAT](http://www.lapat.iag.usp.br/) and [MASTER](http://www.master.iag.usp.br/) labs!
