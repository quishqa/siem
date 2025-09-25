# Explanation

`siem` packages helps you to create the emission files for WRF-Chem,
and CMAQ air quality models.

Building the emission file is an important part of air quality models.

It is mainly focused on vehicular emission

Why simplified? Because the spirit of the packages is to create emission with limited information,
many simplification were made. For example, it use a day profile and week profile, it does not account for vehicle age,
nor velocity curves. But the win is that the emission are created fast and it is easier to see what factor explain concentration variations.
