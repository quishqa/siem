# Source:
# https://pseudonetcdf.readthedocs.io/en/latest/examples/cmaqemisfromcsv.html
with open('../data/GRIDDESC', 'w') as gf:
    gf.write(
       "' '\n'LamCon_40N_97W'\n 2 33.000 45.000 -97.000 -97.000 40.000\n" +
       "' '\n'12US1'\n'LamCon_40N_97W' " +
       "-2556000.0 -1728000.0 12000.0 12000.0 459 299 1\n' '"
    )
