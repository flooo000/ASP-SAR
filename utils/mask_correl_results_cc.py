#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mask_result_export_cc.py
-------------
Mask the adjusted correlation results in EXPORT/ADJUSTED based on their corresponding correlation coefficient map in EXPORT/CC and save them in MASKED/CC

Usage: prepare_result_export.py [--f] --data=<path>
prepare_result_export.py -h | --help

Options:
-h | --help         Show this screen
--data              Path to EXPORT directory
--f                 Force recomputation of EXPORT directory

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

#############
# FUNCTIONS #
#############

def read_from_file(input_file, n_band):

    ds = gdal.OpenEx(input_file, allowed_drivers=['GTiff'])
    ds_band = ds.GetRasterBand(n_band)
    raw_disparity = ds_band.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize)
    ncol, nrow = ds.RasterXSize, ds.RasterYSize
    # return (raw_disparity, ncol, nrow) XSize=col YSize=row
    return (raw_disparity, ncol, nrow)

def save_to_file(data, output_path, ncol, nrow):
    drv = gdal.GetDriverByName('GTiff')
    dst_ds = drv.Create(output_path, ncol, nrow, 1, gdal.GDT_Float32)
    dst_band = dst_ds.GetRasterBand(1)
    dst_band.WriteArray(data)

# path to current pair cc file, adjusted input file, destination dir (EXPORT/MASKED),
def mask_origin_with_cc(cc_curr_pair, origin_file, destination_dir):
    cc_data = read_from_file(cc_curr_pair, 1)
    cc, ncol, nrow = cc_data[0], cc_data[1], cc_data[2]

    origin_data = read_from_file(origin_file, 1)
    origin = origin_data[0]

    # prepare array to mask, keep values == 1
    mask_array = np.where(cc == 1, True, False)
    
    # check if mask is true, if true - keep origin value, else set to NaN
    origin_masked = np.where(mask_array, origin, np.nan)

    output_path = os.path.join(destination_dir, '{}_MASK.tif'.format(os.path.basename(origin_file).split('.')[0]))
    
    save_to_file(origin_masked, output_path, ncol, nrow)

########
# MAIN #
########

arguments = docopt.docopt(__doc__)

# work_dir is data_dir from before, because everything is in one directory
export_dir = arguments['--data']

adj_dir = os.path.join(export_dir, 'ADJUSTED')
cc_dir = os.path.join(export_dir, 'CC')

masked_dir = os.path.join(export_dir, 'MASKED')
Path(masked_dir).mkdir(parents=True, exist_ok=True)


for f in os.listdir(cc_dir):
    curr_pair = '{}_{}'.format(f.split('_')[0], f.split('_')[1])
    print('Start masking pair: {}'.format(curr_pair))

    h_origin = os.path.join(adj_dir, '{}-F-H_wm.tif'.format(curr_pair))
    v_origin = os.path.join(adj_dir, '{}-F-V_wm.tif'.format(curr_pair))
    cc_curr_pair = os.path.join(cc_dir, f)
    
    
    mask_origin_with_cc(cc_curr_pair, h_origin, masked_dir)
    mask_origin_with_cc(cc_curr_pair, v_origin, masked_dir)
    







