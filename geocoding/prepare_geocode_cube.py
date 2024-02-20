#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
prepare_geocode_cube.py
--------------
Converts images from cube file into format for geocoding and copies them to TO_GEOCODE.

Usage: prepare_geocode_cube.py --data=<path> [--dest=<path>] [--cube=<path>] [--masked]
prepare_geocode_cube.py -h | --help

Options:
-h | --help             Show this screen
--data                  Path to NSBAS processing directory, either H or V
--dest                  Path to destination directory [default: create TO_GEOCODE in EXPORT directory]
--cube                  Path to cube file to specify which cube file [default: will look for depl_cumule_flat]
--masked                If masked files are used [default: no]

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

def save_single_map(output_dir, filename, maps):
    fid = open(os.path.join(output_dir, filename), 'wb')
    maps[:,:,l].flatten().astype('float32').tofile(fid)
    fid.close()

def read_cube(cube_file, ncol, nlines, n_img):
    cubei = np.fromfile(cube_file,dtype=np.float32)
    cube = as_strided(cubei[:nlines*ncol*n_img])

    kk = np.flatnonzero(np.logical_or(cube==9990, cube==9999))
    cube[kk] = float('NaN')
    maps_temp = as_strided(cube.reshape((nlines,ncol,n_img)))
    maps = np.copy(maps_temp)
    
    return maps

########
# MAIN #
########

arguments = docopt.docopt(__doc__)

# path to NSBAS processing directory
data_path = arguments['--data']

# check if masked files are used - if yes, need to adjust path and output
masked = arguments['--masked']

# prepare output directory, save in WORK_DIR/EXPORT/TO_GEOCODE
if(masked):
    # need to go one directory deeper because of NSBAS_PROCESS/MASKED/H
    export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(data_path))), 'EXPORT')
else:
    export_dir = os.path.join(os.path.dirname(os.path.dirname(data_path)), 'EXPORT')
output_dir = os.path.join(export_dir, 'TO_GEOCODE')
Path(output_dir).mkdir(parents=True, exist_ok=True)

# get naming of dir to check if it is range or azimuth
direction = os.path.basename(os.path.normpath(data_path))
if(direction == 'H'):
    direction_name = 'range'
else:
    direction_name = 'azimuth'

# check if specific cube file was chosen (has to be in same directory) 
if(arguments['--cube'] is None):
    cube_file = os.path.join(data_path, 'depl_cumule_flat')
else:
    cube_file = arguments['--cube']

# get image dimensions and number of images - use lect_ts.in file
# to open depl_cumule_flat file - cp depl_cumule.hdr depl_cumule_flat.hdr
#ds = gdal.Open(cube_file)
if os.path.exists(os.path.join(data_path, 'lect_ts.in')):
    ncol, nlines, n_img = list(map(int, open(os.path.join(data_path, 'lect_ts.in')).readline().split(None, 2)[0:3]))
else:
    ds = gdal.Open(cube_file)
    ncol, nlines = ds.RasterXSize, ds.RasterYSize
    n_img = ds.RasterCount

# read list_dates to get all the dates as list
dates_df = pd.read_csv(os.path.join(data_path, 'list_dates'), sep=' ', header=None)
dates = list(dates_df.iloc[:,0])

# read cube file
maps = read_cube(cube_file, ncol, nlines, n_img)

# save individual map
for l in range(n_img):
    curr_date = dates[l]
    if(masked):
        filename = 'REGEOC.{}_{}_{}_{}.r4'.format(direction_name, os.path.basename(cube_file), curr_date, 'MASKED')
    else:
        filename = 'REGEOC.{}_{}_{}.r4'.format(direction_name, os.path.basename(cube_file), curr_date)
    print('saving: {}'.format(filename))

    save_single_map(output_dir, filename, maps) 



