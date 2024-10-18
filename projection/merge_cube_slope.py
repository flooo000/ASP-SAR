#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
merge_cube_slope.py
--------------
Merge two cubes that are projected in the steepest slope direction


Usage: merge_cube_slope.py --cube1=<path> [--dates1=<path>] --cube2=<path> [--dates2=<path>] --dest=<value> --name=<value> --ext=<value> [--direction=<value>] 
merge_cube_slope.py -h | --help

Options:
-h | --help             Show this screen
--cube1                 Path to first projected cube
--dates1                Path to dates file of first projected slope cube
--cube2                 Path to second projected cube
--dates2                Path to dates file of second projected slope cube
--dest                  Path to destination directory
--name                  Naming of output file
--ext                   Extension for the naming [Default: slope]
--direction             Direction of displacement [azimuth||range]

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
from scipy.interpolate import interp1d

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

def get_img_dim(data_path):
    #ds = gdal.Open(os.path.join(data_path, 'depl_cumule_slope'))
    ds = gdal.Open(data_path)
    ncol, nlines = ds.RasterXSize, ds.RasterYSize
    n_img = ds.RasterCount
    
    return (ncol, nlines, n_img)

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

# cube1 must have the earliest date; cube1[start_date] < cube2[start_date]
# assuming list_dates is in same directory as depl_cumule_slope
# include optional path for list_dates or just remove
cube_file1 = arguments['--cube1']
data_path1 = os.path.dirname(cube_file1)
#dates_file1 = arguments['--dates1']

cube_file2 = arguments['--cube2']
data_path2 = os.path.dirname(cube_file2)
#dates_file2 = arguments['--dates2']

dest_path = arguments['--dest']
name = arguments['--name']

direction = arguments['--direction']

if(arguments['--dates1']):
    dates1_df = pd.read_csv(arguments['--dates1'], sep=' ', header=None)
    dates1 = list(dates1_df.iloc[:,1])
else:
    dates1_df = pd.read_csv(os.path.join(data_path1, 'list_dates'), sep=' ', header=None)
    dates1 = list(dates1_df.iloc[:,1])

if(arguments['--dates2']):
    dates2_df = pd.read_csv(arguments['--dates2'], sep=' ', header=None)
    dates2 = list(dates2_df.iloc[:,1])
else:
    dates2_df = pd.read_csv(os.path.join(data_path2, 'list_dates'), sep=' ', header=None)
    dates2 = list(dates2_df.iloc[:,1])


#img_dim1 = get_img_dim(data_path1)
img_dim1 = get_img_dim(cube_file1)
print(img_dim1)
ncol1, nlines1, n_img1 = img_dim1[0], img_dim1[1], img_dim1[2]

#img_dim2 = get_img_dim(data_path2)
img_dim2 = get_img_dim(cube_file2)
ncol2, nlines2, n_img2 = img_dim2[0], img_dim2[1], img_dim2[2]
print(img_dim2)


# find the index of first smaller and first higher value of start value of dates2 in dates1

start_dates2 = dates2[0]

first_smaller_index = None
first_higher_index = None

for i, num in enumerate(dates1):
    if num < start_dates2:
        first_smaller_index = i
    elif num > start_dates2 and first_higher_index is None:
        first_higher_index = i


# get offset maps from first time series 
# read_cube and then maps[:,:,first_smaller_index] and maps[:,:,first_higher_index]
# take them - interpolate - get offset map
# then take second time series and add offset map
# combine

cube1 = read_cube(cube_file1, img_dim1[0], img_dim1[1], img_dim1[2])
cube2 = read_cube(cube_file2, img_dim2[0], img_dim2[1], img_dim2[2])

# get maps to interpolate between to get offset value for second time series

cube1_smaller_map = cube1[:,:,first_smaller_index]
cube1_higher_map = cube1[:,:,first_higher_index]

interp_function = interp1d([dates1[first_smaller_index], dates1[first_higher_index]], [cube1_smaller_map, cube1_higher_map], axis=0, kind='linear', fill_value='extrapolate')

offset_map = interp_function(start_dates2)

# add offset to all dates2 maps

cube2_with_offset = np.zeros((nlines2, ncol2, n_img2))

# for sorting the combined array, set pixel [0,0] of each map to the corresponding date_dec
for l in range(n_img2):
    
    cube2_with_offset[:,:,l] = cube2[:,:,l] + offset_map
    cube2_with_offset[0,0,l] = float(dates2[l])

for k in range(n_img1):
    cube1[0,0,k] = float(dates1[k])


combined_cubes = np.concatenate((cube1, cube2_with_offset), axis=2)

# sort based on the first pixel - should work as well without the reference pixel (apply same sort to list_dates files with the same indices)
# can be changed, but keep it like that now until it is a problem
sort_values = combined_cubes[0,0,:]
sorted_indices = np.argsort(sort_values)
sorted_cubes = combined_cubes[:,:,sorted_indices]


# adjust at one point

if(arguments['--ext']):
    ext = arguments['--ext']
else:
    ext = 'slope'

if(arguments['--direction']):
    save_cube(dest_path, '{}_depl_cumule_{}_{}_PAZ_TSX'.format(name, direction, ext), sorted_cubes)

    save_cube_metadata(dest_path, '{}_depl_cumule_{}_{}_PAZ_TSX'.format(name, direction, ext), sorted_cubes.shape)
else:
    save_cube(dest_path, '{}_depl_cumule_{}_PAZ_TSX'.format(name, ext), sorted_cubes)

    save_cube_metadata(dest_path, '{}_depl_cumule_{}_PAZ_TSX'.format(name, ext), sorted_cubes.shape)


