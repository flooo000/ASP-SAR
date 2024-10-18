#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
diff_cube.py
--------------
Generates difference map of selected pairs of cube file. Similar to depl_cumule_diff.py but this takes the cube directly as input.

Usage: diff_cube.py --cube=<path> --list_images=<path> --diff=<path> --dest=<path> --ref=<path> [--ext=<value>]
diff_cube.py -h | --help

Options:
-h | --help             Show this screen
--cube                  Path to cube file
--list_images           Path to images_retenues file to use
--diff                  File with pairs to calculate difference [table with 2 cols: date1,date2]
--dest                  Path to destination directory
--ref                   Path to reference file for the (geo)-projection of output

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

if(arguments['--ext']):
    ext = arguments['--ext']
    cube_name = '{}_{}'.format(os.path.basename(cube_file), ext)
else:
    cube_name = os.path.basename(cube_file)

list_images_file = arguments['--list_images']

diff_file = arguments['--diff']

dest_path = arguments['--dest']


ds = gdal.Open(cube_file)
ncols, nlines = ds.RasterXSize, ds.RasterYSize
n_img = ds.RasterCount

# maybe need ref file for the projection
ref_file = arguments['--ref']
ds_ref = gdal.Open(ref_file)
proj = ds_ref.GetProjection()
geotransform = ds_ref.GetGeoTransform()

maps = read_cube(cube_file, ncols, nlines, n_img)

list_images = pd.read_csv(list_images_file, sep='\s+', header=None)

with open(diff_file) as file:
    for row in file:
        date1, date2 = row.rstrip().split(',')
        print('Calculate difference between {} - {}'.format(date1, date2))

        date1_index = list_images.index[list_images[1] == int(date1)].tolist()
        date2_index = list_images.index[list_images[1] == int(date2)].tolist()
        # squeeze to remove the single dimension (nlines,ncols,1) to (nlines,ncols) 
        diff_map = np.squeeze(maps[:,:,date2_index] - maps[:,:,date1_index])
        
        diff_file = os.path.join(dest_path, '{}_{}-{}.tif'.format(cube_name, date1, date2))
        print(diff_map.shape) 
        save_to_file(diff_map, diff_file, ncols, nlines, proj, geotransform)



