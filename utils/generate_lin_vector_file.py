#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generate_lin_vector_file.py
--------------
Generates vector file with linear model between two dates.

Usage: generate_lin_vector_file.py --data=<path> --dest=<path> --dates=<value> --name=<value> [--adj]
generate_lin_vector_file.py -h | --help

Options:
-h | --help             Show this screen
--data                  Path to images_retenues file
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
from datetime import datetime


#############
# FUNCTIONS #
#############

def date_to_float(date):
    date_str = str(date)
    d = datetime.strptime(date_str, '%Y%m%d')

    return (d.year + (d.month-1)/12.0 + (d.day-1)/365.0)

def lin_trend_adj(dates, dates_dec, d1, d2):
    i1 = dates.index(d1)
    i2 = dates.index(d2)

    dmax = dates_dec[i2] - dates_dec[i1] 
    
    # m = 1 / (dates_dec[i2] - dates_dec[i1])
    m = 1

    v = np.zeros((len(dates)))
    for i in range(i1, i2 + 1):
        v[i] = m * (dates_dec[i] - dates_dec[i1])
    
    for i in range(i2 + 1, len(dates)):
        v[i] = dmax
    
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

# use interpolation method
adj = arguments['--adj']


list_dates = pd.read_csv(data_path, sep=' ', header=None)
dates = [str(d) for d in list(list_dates[1])]
dates_dec = [date_to_float(d) for d in dates]

vector = lin_trend_adj(dates, dates_dec, start_date, end_date)

with open(os.path.join(dest_path, 'vector_lin{}_adj.txt'.format(name)), 'w') as f:
    for v in vector:
        f.write('{}\n'.format(str(v)))






