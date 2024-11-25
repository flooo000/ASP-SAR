#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
deconstruct_cube.py
----------------
Saves single map or all maps from the cube as tif file. 

Usage: deconstruct_cube.py --cube=<path> --dest=<path> [--nimg=<value>] [--ref=<path>]
deconstruct_cube.py -h | --help

Options:
-h | --help             Show this screen
--cube                  Path to cube file
--dest                  Path to destination directory
--nimg                  Number of map to save, if -1 - save last file of cube [Default: saves all files]
--ref                   Path to reference file for the (geo)-projection of output


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
# FUCNTIONS #
#############

def save_to_file(data, output_path, ncol, nrow, proj, geotransform):
    drv = gdal.GetDriverByName('GTiff')
    dst_ds = drv.Create(output_path, ncol, nrow, 1, gdal.GDT_Float32)
    dst_band = dst_ds.GetRasterBand(1)

    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(proj)

    dst_band.WriteArray(data)

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



########
# MAIN #
########

arguments = docopt.docopt(__doc__)

cube_file = arguments['--cube']
cube_name = os.path.basename(cube_file)

dest_path = arguments['--dest']

dest_img = int(arguments['--nimg'])

ds = gdal.Open(cube_file)
ncols, nlines = ds.RasterXSize, ds.RasterYSize
n_img = ds.RasterCount

if(dest_img == -1):
    dest_img = n_img

# if reference image is given, use it for projection
if(arguments['--ref']):
    ref_file = arguments['--ref']
    ds_ref = gdal.Open(ref_file)
    proj = ds_ref.GetProjection()
    geotransform = ds_ref.GetGeoTransform()
else:
    proj = ds.GetProjection()
    geotransform = ds.GetGeoTransform()

maps = read_cube(cube_file, ncols, nlines, n_img)

# add later option to save all files
for l in range(n_img):
    if(l == dest_img-1):
        curr_map = maps[:,:,l].reshape((nlines, ncols))


        print('Save image {} of {} total images in cube'.format(n_img, n_img))
        output_path = os.path.join(dest_path, '{}_map{}.tif'.format(cube_name, dest_img))
        print(output_path)

        save_to_file(curr_map, output_path, ncols, nlines, proj, geotransform)




