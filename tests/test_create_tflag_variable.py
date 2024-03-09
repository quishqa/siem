from siem.cmaq import create_tflag_variable
import numpy as np
import xarray as xr


def test_create_tflag_variable() -> None:
    date = "2018-07-01"
    n_vars = 124
    tflag = create_tflag_variable(date, n_vars)

    assert isinstance(tflag, xr.DataArray)
    assert tflag.shape == (25, 124, 2)
    assert tflag.dims == ("TSTEP", "VAR", "DATE-TIME")
    assert tflag.dtype == np.dtype("int32")
