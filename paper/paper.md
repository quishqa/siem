---
title: 'SIEM: Simplified emission model'
tags:
  - Python
  - emission
  - air pollution
  - WRF-Chem
  - CMAQ
authors:
  - name: Mario Eduardo Gavidia-Calderón
    orcid: 0000-0002-7371-1116
    corresponding: true # (This is how to denote the corresponding author)
    affiliation: 1 # (Multiple affiliations must be quoted)
  - name: Alejandro Delgado-Peralta
    orcid: 0000-0002-4413-3732
    affiliation: 1
  - name: Maria de Fatima Andrade
    orcid: 0000-0001-5351-8311
    affiliation: 1
  - name: Edmilson Dias de Freitas
    orcid: 0000-0001-8783-2747
    affiliation: 1
affiliations:
 - name: Instituto de Astronomia, Geofísica e Ciências Atmosféricas, Universidade de São Paulo, Brazil
   index: 1
date: 15 April 2026
bibliography: paper.bib

---

# Summary

Emissions are the quantity of a pollutant put on the atmosphere.
They are frequently report in an emission inventory.
Emission information is one of the most important input in air quality models.
Usually, the emission information is spatially and temporal distributed in the simulation domain.
Furthermore, it requires to be speciated based on the chemical mechanism and aerosol model selected in the air quality model.
Air quality models comes with pre-processors to do this task.
But, these pre-processors usually required detailed information that is not frequently available in cities on the Global South.
`siem` is an emission pre-processors that used simplified information to create the emission file for WRF-Chem and CMAQ air quality models.
It design allows to be used in cities with scarce to emission information,
therefore, `siem` will allows to improve air quality management by facilitating the implementation of air quality models.

# Statement of need

`siem` is a python package that allows you to create the emission file required to run WRF-Chem [@Grell2005] and CMAQ [@Binkowski2003] air quality models.
Despite this models come with their emissions pre-processors.
They required a lot information that many cities, specially in the global south, do not have.
WRF-Chem and CMAQ are both of the most used air quality models in South American cities [@Gavidia-Calderón],
therefore we provide a tool that allow to create emission files to perform model intercomparison.
It allow to create the emission files with a minimum of information.
It also allows to inspect the emissions during the construction of the files.

# State of the field

As far as we know, this is the first emission model that create emission files for WRF-Chem and CMAQ models.

# Software design

`siem` is based in the methodology for creating WRF-Chem emisison file described in @Andrade2015.
It was mainly developed to distribute vehicular emissions but it also works for other types of emission that need spatial and temporal distribution.

# Research impact statement

# AI usage disclosure

No generative AI tools were used in the development of this software, the writing
of this manuscript, or the preparation of supporting materials.

# Acknowledgements

We acknowledge contributions from Angel Vara-Vela.

# References
