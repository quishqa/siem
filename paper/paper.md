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

# Statement of need

`siem` is a python package that allows you to create the emission file required to run WRF-Chem [@Grell2005] and CMAQ [@Binkowski2003] air quality models.
Despite this models come with their emissions pre-processors.
They required a lot information that many cities, specially in the global south, do not have.

# State of the field

# Software design

`siem` is based in the methodology for creating WRF-Chem emisison file described in @Andrade2015.
It was mainly develope to distribute vehicular emissions but it also works for other types of emission that need spatial distribution.

# Research impact statement

# AI usage disclosure

No generative AI tools were used in the development of this software, the writing
of this manuscript, or the preparation of supporting materials.

# Acknowledgements

We acknowledge contributions from Angel Vara-Vela.

# References
