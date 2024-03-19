#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generate_lin_vector_file.py
--------------
Generates vector file with linear model between two dates.

Usage: generate_lin_vector_file.py --data=<path> --dest=<path> --dates=<value> --name=<value>
generate_lin_vector_file.py -h | --help

Options:
-h | --help             Show this screen
--data                  Path to list_dates file
--dest                  Path to destination directory
--dates                 Start and end date to model linear trend as date1,date2
--name                  Name extension for output file
"""
##########
# IMPORT #
##########

import os, sys
import numpy as np
from numpy.lib.stride_tricks import as_strided
from osgeo import gdal
import pandas as pd
from pathlib import Path
import shutil
from dateutil import parser
import docopt

#############
# FUNCTIONS #
#############

def lin_trend(dates, d1, d2):
    i1 = dates.index(d1)
    i2 = dates.index(d2)

    v = np.zeros((len(dates)))
    for i in range(i1 + 1, i2):
        v[i] = np.nan

    for i in range(i2, len(dates)):
        v[i] = 1.0
    
    return v


########
# MAIN #
########

arguments = docopt.docopt(__doc__)

# path to list_dates file
data_path = arguments['--data']

# path to save output file
dest_path = arguments['--dest']

# start and end date
in_dates = arguments['--dates']
start_date, end_date = in_dates.split(',')

# naming for output file
name = arguments['--name']

list_dates = pd.read_csv(data_path, sep=' ', header=None)
dates = [str(d) for d in list(list_dates[0])]
dates_dec = [float(d) for d in list(list_dates[1])]

# set values to NaN that will be interpolated, date1=0 and date2=1
vector_nan = lin_trend(dates, start_date, end_date)

# generate pd.Series to interpolate based on decimal date and replace nan values
vector_series = pd.Series(vector_nan, index=dates_dec)

vector = vector_series.interpolate(method='index')

with open(os.path.join(dest_path, 'vector_lin{}.txt'.format(name)), 'w') as f:
    for v in vector:
        f.write('{}\n'.format(str(v)))


