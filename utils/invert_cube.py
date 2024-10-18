#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
invert_cube.py
----------------
Invert the values of cube to obtain displacement in -LOS. 

Usage: invert_cube.py --cube=<path> [--dest=<path>]
deconstruct_cube.py -h | --help

Options:
-h | --help             Show this screen
--cube                  Path to cube file
--dest                  Path to destination directory

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


def read_cube(cube_file, ncol, nlines, n_img):

    print('Start reading cube file')

    cubei = np.fromfile(cube_file,dtype=np.float32)
    cube = as_strided(cubei[:nlines*ncol*n_img])

    kk = np.flatnonzero(np.logical_or(cube==9990, cube==9999))
    cube[kk] = float('NaN')
    maps_temp = as_strided(cube.reshape((nlines,ncol,n_img)))
    maps = np.copy(maps_temp)

    print('Finished reading cube file')

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

cube_file = arguments['--cube']

cube_path = os.path.dirname(cube_file)
cube_name = os.path.basename(cube_file)

outfile_path = os.path.join(cube_path, '{}_inverted'.format(cube_name))
print(outfile_path)

ds = gdal.Open(cube_file)
ncols, nlines = ds.RasterXSize, ds.RasterYSize
n_img = ds.RasterCount

img_data = (nlines, ncols, n_img)

maps = read_cube(cube_file, ncols, nlines, n_img)

maps_inverted = np.zeros((nlines, ncols, n_img))
print(maps.shape)
print(maps_inverted.shape)

for l in range(n_img):
    maps_inverted[:,:,l] = -(maps[:,:,l].reshape((nlines, ncols)))


save_cube(cube_path, '{}_inverted'.format(cube_name), maps_inverted)
save_cube_metadata(cube_path, '{}_inverted'.format(cube_name), img_data)


