#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_geocoded_cube.py
--------------
Converts geocoded images to cube file in destination directory.

Usage: build_geocoded_cube.py --data=<path> --dest=<path> [--masked]
build_geocoded_cube.py -h | --help

Options:
-h | --help             Show this screen
--data                  Path to EXPORT/GEOCODED directory
--dest                  Path to destination directory (where original cube file is stored
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
from matplotlib import pyplot as plt


#############
# FUNCTIONS #
#############

def get_image_dimension(data_path, bil_files):
    ds = gdal.Open(os.path.join(data_path, bil_files[0]))
    ncol, nrow = ds.RasterXSize, ds.RasterYSize
    
    nimg = len(bil_files)

    return (nrow, ncol, nimg)

def build_cube(data_path, bil_files, maps, img_data):
    nrow, ncol, nimg = img_data[0], img_data[1], img_data[2]

    for i in range(nimg):
        curr_name = bil_files[i].split('.')[1]
        print('Read {}'.format(curr_name))

    # read image
        m = np.fromfile(os.path.join(data_path, bil_files[i]),dtype=np.float32)
        map_i = m[:nrow*ncol].reshape((nrow,ncol))

        maps[:,:,i] = map_i[:,:]

        del map_i

    return maps

def save_cube(dest_path, out_filename, maps):
    print('Writing cube')

    fid = open(os.path.join(dest_path, out_filename), 'wb')
    maps[:,:,:].flatten().astype('float32').tofile(fid)
    fid.close()

def save_cube_metadata(dest_path, out_filename, img_data):
    nrow, ncol, nimg = img_data[0], img_data[1], img_data[2]

    # be careful here with ncol, nrow (normal: lines=nrow; samples=ncol)
    with open(os.path.join(dest_path, '{}.hdr'.format(out_filename)), 'w') as hdr_file:
        hdr_file.write("ENVI\n")
        hdr_file.write("samples = {}\n".format(ncol))
        hdr_file.write("lines = {}\n".format(nrow))
        hdr_file.write("bands = {}\n".format(nimg))
        hdr_file.write("header offset = 0\n")
        hdr_file.write("file type = ENVI Standard\n")
        hdr_file.write("data type = 4\n")  # 4 represents float32, adjust if needed
   
    # save also .in file to plot pixel
    with open(os.path.join(dest_path, 'lect_{}.in'.format(out_filename)), 'w') as lect_file:
        lect_file.write('\t{}\t{}\t{}'.format(ncol, nrow, nimg))

########
# MAIN #
########

arguments = docopt.docopt(__doc__)

# path to EXPORT/GEOCODED directory
data_path = arguments['--data']

# path to save cube file (directory with original cube)
dest_path = arguments['--dest']

# check if masked data is used - change filename 
masked = arguments['--masked']

if(masked):
    out_filename = 'depl_cumule_geocoded_masked'
else:
    out_filename = 'depl_cumule_geocoded'


# important to sort data, otherwise no coherent time series (check later if more than one cube data or other files are in data dir -> maybe work with subdirectories)
bil_files = sorted([f for f in os.listdir(data_path) if os.path.splitext(f)[1] == '.bil'])

# get information for building cube -> ncol, nrow, nimg
img_data = get_image_dimension(data_path, bil_files)

# init cube structure
#maps = np.zeros((nrow, ncol, nimg))
maps = np.zeros(img_data)

# get data from files and save in maps
maps = build_cube(data_path, bil_files, maps, img_data)

# save cube and additional files (.hdr, lect_geocoded.in)
save_cube(dest_path, out_filename, maps)
save_cube_metadata(dest_path, out_filename, img_data)
