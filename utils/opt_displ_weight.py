#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
opt_displ_weight.py 
----------------
Weight the backward, forward, nadir displacement maps to generate smoother map and inverts the final output if needed. The output is saved in the same directory as the input images

Usage: compute_disp_ampli.py --backward=<path> --nadir=<path> --forward=<path> --direction=<value> --name=<value> --dest=<path> [--invert]
compute_disp_ampli.py -h | --help

Options:
-h | --help             Show this screen
--backward              Path to backward map
--nadir                 Path to nadir map
--forward               Path to forward map
--direction             Direction of displacement [SN||WE]
--name                  Naming of output file
--dest                  Path to destination directory
--invert                Indicates if final maps needs to be inverted
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
from dateutil import parser
import docopt

#############
# FUNCTIONS #
#############

def read_tif(input_file):

    ds = gdal.OpenEx(input_file, allowed_drivers=['GTiff'])
    ds_band = ds.GetRasterBand(1)
    values = ds_band.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize)
    ncols, nlines = ds.RasterYSize, ds.RasterXSize

    proj = ds.GetProjection()
    geotransform = ds.GetGeoTransform()

    return (values, nlines, ncols, proj, geotransform)

def save_to_file(data, output_path, ncol, nrow, proj, geotransform):
    drv = gdal.GetDriverByName('GTiff')
    dst_ds = drv.Create(output_path, ncol, nrow, 1, gdal.GDT_Float32)
    dst_band = dst_ds.GetRasterBand(1)

    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(proj)

    dst_band.WriteArray(data)


########
# MAIN #
########

arguments = docopt.docopt(__doc__)

forward_file = arguments['--forward']
nadir_file = arguments['--nadir']
backward_file = arguments['--backward']

name = arguments['--name']
file_date = '_'.join(os.path.basename(nadir_file).split('_')[2:4])

direction = arguments['--direction']

dest_path = arguments['--dest']

outfile_path = os.path.join(dest_path, '{}_{}_{}_weighted.tif'.format(direction, name, file_date))

print(outfile_path)

for_data, for_ncols, for_nlines, for_proj, for_geo = read_tif(forward_file)
nad_data, nad_ncols, nad_nlines, nad_proj, nad_geo = read_tif(nadir_file)
back_data, back_ncols, back_nlines, back_proj, back_geo = read_tif(backward_file)

out_data = np.zeros((for_nlines, for_ncols))

# stack arrays on one axis
stacked = np.stack((for_data, nad_data, back_data), axis=0)

# count non-zero values along the new axis
non_zero_count = np.count_nonzero(stacked, axis=0)

# sum the arrays along the new axis
total_sum = np.sum(stacked, axis=0)

# compute the weighted average (avoid division by zero)
out_data = np.divide(total_sum, non_zero_count, where=non_zero_count!=0, out=np.zeros_like(total_sum))

# check if output needs to inverted (changing direction)
if(arguments['--invert']):
    print('Changing signs and save data')
    save_to_file(-out_data, outfile_path, for_ncols, for_nlines, for_proj, for_geo)
else:
    print('Save data')
    # take the image data from one of the input images
    save_to_file(out_data, outfile_path, for_ncols, for_nlines, for_proj, for_geo)




