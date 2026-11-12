# Cloud-mask scoring conventions

A clear-sky validation usually condenses into one false-clear number. That number
is not a property of the mask: it moves with the truth definition, the confidence
reduction, the pooling, the metric and the matching window. This repository
applies twelve conventions to one fixed matchup set so the size of each choice is
visible.

## What is here

    supp/S1_matchups.csv   the frozen matchup set (7,123 profiles, 53 granules,
                           April and July 2019)
    code/p8_recompute.py   QC filter, the twelve conventions, the bootstrap
    code/tabgen.py         tables from numbers.json (single source of truth)
    code/make_figures.py   figures from numbers.json
    code/area_test.py      area weighting and the cell-aspect check
    numbers.json           every number the paper quotes
    tables/, figures/      generated output

## Run it

    pip install numpy pandas scipy matplotlib
    python code/p8_recompute.py     # QC banner, then the twelve conventions
    python code/tabgen.py           # tables/tab1_conventions.tex, tab3_metric.tex
    python code/make_figures.py     # figures/

The QC banner is the gate: it must print

    7123 rows, 53 granules (July 4246/31, April 2877/22); m35_det unique=[1]

## The interval unit

Every interval in the paper is a percentile interval from one granule-block
bootstrap over the **31 July granules** (2,000 replicates, seed 20261110), with
every convention recomputed on the same resample. Seven of the twelve exclude
unity; five do not, and the paper reports that rather than the other way round.

## Licence and citation

Code MIT; the matchup table CC BY 4.0 (see DATA_LICENSE). The MODIS and CALIPSO
source granules are public archives and are not redistributed here.
