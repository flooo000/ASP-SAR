#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
process_MSWEP.py
-------------

Usage: process_MSWEP.py --data=<path> --coords=<value,value> --dest=<path> [--name=<value>] [--plot_all]
process_MSWEP.py -h | --help

Options:
-h | --help         Show this screen
--data              Path to MSWEP data directory 
--coords            Coordinates of point of interest [lat,lon]
--dest              Path to destination directory for txt files
--name              Set name of output file [Default: Takes coordinates]
--plot              Plot current file


"""
##########
# IMPORT #
##########

import os, sys
import numpy as np
from osgeo import gdal
import pandas as pd
from pathlib import Path
import shutil
import docopt
import xarray
from matplotlib import pyplot as plt
import datetime


#############
# FUNCTIONS #
#############

def plot_precipitation(data, year, name, dest_dir):
    #plt.rcParams["figure.figsize"] = (20,10)
    #plt.xlim([pd.to_datetime('{}-01-01'.format(year)), pd.to_datetime('{}-12-31'.format(year))])
    plt.ylim(0, 100)
    
    # if plot from txt file, need to convert string to datetime
    #dates = [datetime.datetime.fromisoformat(d) for d in data['date']]
    dates = data['date']
    plt.plot(dates, data['precipitation'], '-b')

    plt.ylabel('Precipitation in [mm]')
    plt.title('Precipitation for {} in {}'.format(name, year))

    plt.savefig(os.path.join(dest_dir, '{}_{}_precipitation.pdf'.format(year, name)))

    plt.show()

# split to include later just the plot for given txt files
def plot_single_dataframe(data_df, year, name, dest_dir):
    plot_precipitation(data_df, year, name, dest_dir)


def process_precipitation_year(data_list, coordinates, data_dir, dest_dir, year, name, plot):
    
    # save dates and precipitation data in list -> important that data_list is sorted!
    precip_dates_list = []
    precip_values_list = []

    coordinates = coordinates.split(',')
   
    for f in data_list:
        current_file = os.path.join(data_dir, f)
        rain_data = xarray.open_dataset(current_file)

        precip = rain_data['precipitation']

        poi_precip = precip.sel(lat=coordinates[0], lon=coordinates[1], method='nearest')

        poi_date = poi_precip['time'].values[0]
        poi_value = poi_precip.values[0]

        precip_dates_list.append(poi_date)
        precip_values_list.append(poi_value)

    out_df = pd.DataFrame({'date': precip_dates_list,
                           'precipitation': precip_values_list
                          })

    out_df.to_csv(os.path.join(dest_dir, '{}_{}_precipitation.txt'.format(year, name)), sep='\t', index=None)
    
    if(plot):
        plot_single_dataframe(out_df, year, name, dest_dir)
    



########
# MAIN #
########

arguments = docopt.docopt(__doc__)

data_dir = arguments['--data']

coordinates = arguments['--coords']

dest_dir = arguments['--dest']

if(arguments['--name']):
    name = arguments['--name']
else:
    name = arguments['--coords']

plot = arguments['--plot_all']

# save data in dictionary to allow processing based on year
# key = year; values = files for that year
data_dict = {}

for f in os.listdir(data_dir):
    year = f[0:4]
    
    if year in data_dict:
        data_dict[year].append(f)
    else:
        data_dict[year] = [f]


for y in data_dict.keys():
    # important to sort here to have dates in correct order 
    data_list = sorted(data_dict[y])
    
    print('Start: {}'.format(y))
    process_precipitation_year(data_list, coordinates, data_dir, dest_dir, y, name, plot)
    print('Finished: {}'.format(y))



