#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
convert_geotiff.py
------------
Converts the ALL2GIF results to GeoTIFF. It takes the log() of the input image.
An additional file is created (AMPLI_STACK_SIGMA_3.tif) with mean, 1/sigma and sigma as bands.

Usage: prepare_correl_dir.py --data=<path>
prepare_correl_dir.py -h | --help

Options:
-h | --help         Show this screen
--data              Path to directory with linked data

"""
##########
# IMPORT #
##########

import os, sys
import numpy as np
from osgeo import gdal
import pandas as pd
from pathlib import Path
from math import *
import docopt

#############
# FUNCTIONS #
#############

def save_to_file(data, output_path, ncol, nrow):
    drv = gdal.GetDriverByName('GTiff')
    dst_ds = drv.Create(output_path, ncol, nrow, 1, gdal.GDT_Float32)
    dst_band = dst_ds.GetRasterBand(1)
    dst_band.WriteArray(data)

def convert_single_file(input_file, img_dim):

    # AT ONE POINT: CHECK VARIABLES AND PATHS - NECESSARY?
    # filename is linked file
    filename = input_file # prepare for later if link/file is passed with path
    real_path = os.path.realpath(input_file)
    output_dir = os.path.dirname(os.path.abspath(input_file))
    geotiff_dir = os.path.join(output_dir, 'GEOTIFF')

    ncol, nrow = img_dim[0], img_dim[1]
## prepare conversion

    # read image
    m = np.fromfile(input_file,dtype=np.float32)
    amp = m[:nrow*ncol].reshape((nrow,ncol))

# get log of amplitude 

    output_path_log = os.path.join(geotiff_dir, '{}_log.tif'.format(os.path.basename(input_file)))    
    amp[amp>0] = np.log(amp[amp>0])

    save_to_file(amp, output_path_log, ncol, nrow)

    print('Done processing: {}'.format(filename))


# get the dimensions of the coregistered images
def get_img_dimensions(input_file):
    real_path = os.path.realpath(input_file)
    i12_path = os.path.dirname(os.path.dirname(real_path))
    insar_param_file = os.path.join(i12_path, 'TextFiles', 'InSARParameters.txt')
    
    #print('InSAR file: {}'.format(insar_param_file))
    with open(insar_param_file, 'r') as f:
        # read lines of file and remove whitespace and comments (comments after \t\t)
        lines = [''.join(l.strip().split('\t\t')[0]) for l in f.readlines()]
        #print(lines)
        jump_index = lines.index('/* -5- Interferometric products computation */')
        img_dim = lines[jump_index + 2: jump_index + 4]
        #print(img_dim)

    ncol, nrow = int(img_dim[0].strip()), int(img_dim[1].strip())
    #print(input_file, ncol, nrow)
    
    # return results as tupels with bool flag, True if dimensions != 0
    if(ncol == 0):
        return (ncol, nrow, False)
    else:
        return (ncol, nrow, True)


def get_mean_sigma_amplitude(geotiff_dir, img_dim, corrupt_file_df):

    ncol, nrow = img_dim[0], img_dim[1]
    stack, sigma, weight = np.zeros((nrow, ncol)), np.zeros((nrow, ncol)), np.zeros((nrow, ncol))
    stack_norm, sigma_norm = np.zeros((nrow, ncol)), np.zeros((nrow, ncol))

    for f in os.listdir(geotiff_dir):
        # just use DATE.VV.mod_log.tif images; important if AMPLI_STACK_SIGMA was already calculated
        if(f in corrupt_file_df['file'].values):
            print('Skip: {}'.format(f))    
        else:
            #if(len(f.split('.')[0]) == 8):
            if('.mod_log.tif' in f):
                print('Start: {}'.format(f))
        # change to read data with gdal
                ds = gdal.OpenEx(os.path.join(geotiff_dir, f), allowed_drivers=['GTiff'])
                ds_band = ds.GetRasterBand(1)
        
        # geotiff data contains log of amplitude
                amp = ds_band.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize)
        
                stack = stack + amp
                sigma = sigma + amp**2
            
                stack_norm = stack_norm + (amp / np.nanmean(amp))
                sigma_norm = sigma_norm + (amp / np.nanmean(amp))**2

        # weight == N
        # weight is a matrix -> have the N information for every pixel
                w = np.zeros((nrow, ncol))
                index = np.nonzero(amp)
        # if img is empty/NaN, will not be added to N(weight)
                w[index] = 1
                weight = weight + w
                print('Finished: {}'.format(f))

    # compute mean of amplitude stack and sigma
    # mean_stack = stack / N_img (weight)
    stack[weight > 0] = stack[weight > 0] / weight[weight > 0]
    sigma[weight > 0] = np.sqrt(sigma[weight > 0] / weight[weight > 0] - (stack[weight > 0])**2)
    da = np.zeros((nrow, ncol))
    da[sigma > 0] = 1./sigma[sigma > 0]
   
    #stack_norm[weight > 0] = stack[weight > 0] / np.nanmean(stack[weight > 0])
    stack_norm[weight > 0] = stack_norm[weight > 0] / weight[weight > 0]
    sigma_norm[weight > 0] = np.sqrt(sigma_norm[weight > 0] / weight[weight > 0] - stack_norm[weight > 0]**2)

    save_to_file(stack, os.path.join(geotiff_dir, 'AMPLI_MEAN.tif'), ncol, nrow)
    save_to_file(sigma, os.path.join(geotiff_dir, 'AMPLI_SIGMA.tif'), ncol, nrow)
    save_to_file(da, os.path.join(geotiff_dir, 'AMPLI_dSIMGA.tif'), ncol, nrow)

    save_to_file(stack_norm, os.path.join(geotiff_dir, 'AMPLI_MEAN_NORM.tif'), ncol, nrow)
    save_to_file(sigma_norm, os.path.join(geotiff_dir, 'AMPLI_SIGMA_NORM.tif'), ncol, nrow)

########
# MAIN #
########

arguments = docopt.docopt(__doc__)

input_path = arguments['--data']
all_file_df = pd.DataFrame(columns=['file', 'ncol', 'nrow'])

geotiff_dir = os.path.join(input_path, 'GEOTIFF')
Path(geotiff_dir).mkdir(parents=True, exist_ok=True)

for f in os.listdir(input_path):
    if(os.path.splitext(f)[1] == '.mod'):
        img_dims = get_img_dimensions(os.path.join(input_path, f))
        # if true, dimensions found and use them for processing, else continue
        # bc all images have same dimension after ALL2GIF processing
        new_row = pd.DataFrame([{'file': f, 'ncol': img_dims[0], 'nrow': img_dims[1]}])
        all_file_df = pd.concat([all_file_df, new_row], ignore_index=True)
        
# more stable way to get image dimension, get value with most occurences for ncol and nrow as final values
# after this - use values to find images with different dimensions
# especially for S1 
ncol_max = all_file_df['ncol'].value_counts().idxmax()
nrow_max = all_file_df['nrow'].value_counts().idxmax()

# set image dimensions for further processing
IMG_DIM = (int(ncol_max), int(nrow_max))

# only expect differences for nrow - S1
ncol_differences = all_file_df.index[all_file_df['ncol'] != ncol_max]
nrow_differences = all_file_df.index[all_file_df['nrow'] != nrow_max]

ind_differences = ncol_differences.append(nrow_differences)

# get files with different extents and save in file
corrupt_file_df = all_file_df.iloc[ind_differences]
corrupt_file_df.to_csv(os.path.join(geotiff_dir, 'corrupt_data.txt'), sep='\t')

print('############################')
print('START CONVERSION')
print('############################')

# only process non existing files 
for f in os.listdir(input_path):
    if(os.path.splitext(f)[1] == '.mod'):
        if(os.path.isfile(os.path.join(geotiff_dir, '{}_log.tif'.format(f)))):
            continue
        else:
            # if file has different extent - skip
            if(f in corrupt_file_df['file'].values):
                continue
            else:
                print('Start processing: {}'.format(f))
                convert_single_file(os.path.join(input_path, f), IMG_DIM)

print(corrupt_file_df)

# process AMPLI_STACK_SIGMA each time to always include all images
print('Start AMPLI_MEAN and SIGMA calculation')
get_mean_sigma_amplitude(os.path.join(input_path, 'GEOTIFF'), IMG_DIM, corrupt_file_df)    
