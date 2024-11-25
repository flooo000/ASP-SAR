#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mask_cube_binary.py
--------------
Mask cube based on a binary mask map. Set 0 values of mask to NaN

Usage: mask_cube_binary.py --cube=<path> --mask=<path> --dest=<path> 
mask_cube_binary.py -h | --help

Options:
-h | --help             Show this screen
--cube                  Path to  cube
--mask                  Path to binary mask, 0 values are removed
--dest                  Path to destination directory

"""

##########
# IMPORT #
##########

import os, sys
import numpy as np
from numpy.lib.stride_tricks import as_strided
import pandas as pd
from osgeo import gdal
import shutil
import docopt
from matplotlib import pyplot as plt

#############
# FUCNTIONS #
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

def read_tif(input_file):

    ds = gdal.OpenEx(input_file, allowed_drivers=['GTiff'])
    ds_band = ds.GetRasterBand(1)
    values = ds_band.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize)
    
    return values

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
cube_name = os.path.basename(cube_file)

mask_file = arguments['--mask']

dest_path = arguments['--dest']

# read input cube
ds = gdal.Open(cube_file)
ncols, nlines = ds.RasterXSize, ds.RasterYSize
n_img = ds.RasterCount

img_data = (nlines, ncols, n_img)

maps = read_cube(cube_file, ncols, nlines, n_img)

# read mask file
mask = read_tif(mask_file)

# get final size cube
masked_cube = np.zeros((nlines, ncols, n_img))


for i in range(n_img):
    img_slice = maps[:,:,i].reshape((nlines,ncols))
    
    # set pixel to nan where mask = 0
    img_masked = np.where(mask == 0, np.nan, img_slice)
    masked_cube[:,:,i] = img_masked

outfile_name = '{}_masked'.format(cube_name)
save_cube(dest_path, outfile_name, masked_cube)
save_cube_metadata(dest_path, outfile_name, img_data)

