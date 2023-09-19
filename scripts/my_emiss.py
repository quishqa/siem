import xarray as xr
from siem.siem import EmissionSource

spatial = xr.DataArray()

gasoline_vehicles = EmissionSource("Gasoline Vehicle",
                                   1_000_000,
                                   5.0,
                                   {"NOX": 10},
                                   spatial,
                                   [])
print(gasoline_vehicles.total_emiss("NOX"))

