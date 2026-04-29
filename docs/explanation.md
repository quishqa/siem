# Explanation

`siem` package helps you to create the emission files for WRF-Chem,
and CMAQ air quality models.
The strategy is to reproduce the model's netCDF emission files
(same coordinates, dimensions, units, and attributes).
As sometimes the original emission pre-processors require very detailed information,
`siem` allows the user to create the emissions with limited information,
and hence the _simplified_ in the name.
Because of that, `siem` could be used in different cities to run air quality models,
and, therefore, to improve air quality management.

`siem` is strongly based on the methodology of Andrade et al. (2015),
previously used in many air quality simulations over the Metropolitan Area of São Paulo.
But, `siem` offers other features:

- Adding a different number of emission sources.
- Point sources can be spatially and temporally distributed.
- It is a chemical mechanism agnostic. The chemical mechanisms are not hard-coded.
- Emission sources can vary by day of the week.
- Each emission source can have a different spatial distribution.
- Early created for WRF-Chem, but now compatible with CMAQ.
- As it is built in Python, subproducts can be easily modified (i.e., calculate total emissions, plot pollutant emissions, apply correction factors, etc).
