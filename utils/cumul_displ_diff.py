#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cumul_displ_diff.py
--------------
Calculates the difference of geocoded cumulative displacement maps given a table file that indicates the pair and the operation, set d for difference

Usage: cumul_displ_diff.py --data=<path> --diff=<path>
cumul_displ_diff.py -h | --help

Options:
-h | --help             Show this screen
--data                  Path to EXPORT/GEOCODED/name
--diff                  File with pairs and operation to do [table with 3 cols: date1,date2,operation]

"""

##########
# IMPORT #
##########

import os, sys
import numpy as np
from osgeo import gdal
import shutil
import docopt

#############
# FUNCTIONS #
#############

def get_image_dimension(data_path, bil_files):
    # need to take [0][0], bc saved as tuple
    ds = gdal.Open(os.path.join(data_path, bil_files[0][0]))
    ncol, nrow = ds.RasterXSize, ds.RasterYSize
    
    # need projection and geotransform for crs 
    prj = ds.GetProjection()
    transf = ds.GetGeoTransform()

    return (nrow, ncol, prj, transf)

def read_file(data_path, nrow, ncol):
    # possible to read both ways

    #data = np.zeros((nrow, ncol))
    #m = np.fromfile(data_path, dtype=np.float32)
    #data = m[:nrow*ncol].reshape((nrow,ncol))

    ds = gdal.OpenEx(data_path, allowed_drivers=['ENVI'])
    ds_band = ds.GetRasterBand(1)
    data = ds_band.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize)
    
    
    return data

def diff_dates(d1_data, d2_data):
    # difference - date2 - date1
    return d2_data - d1_data

def save_to_file(output_path, data, nrow, ncol, prj, transf):
    drv = gdal.GetDriverByName('GTiff')
    dst_ds = drv.Create(output_path, ncol, nrow, 1, gdal.GDT_Float32)
    dst_ds.SetProjection(prj)
    dst_ds.SetGeoTransform(transf)

    dst_band = dst_ds.GetRasterBand(1)
    dst_band.WriteArray(data)



########
# MAIN #
########

arguments = docopt.docopt(__doc__)

# path to geocoded/name dir (containing geocoded cube files)
data_path = arguments['--data']

# path to file containing diff information
diff_file = arguments['--diff']

# save filename and date as tuple to easily find pairs
bil_files = sorted([(f, f.split('.')[1].split('_')[3]) for f in os.listdir(data_path) if os.path.splitext(f)[1] == '.bil'])

# get direction for naming of file, take first file
direction = bil_files[0][0].split('.')[1].split('_')[0]


# get image dimensions
nrow, ncol, prj, transf = get_image_dimension(data_path, bil_files)

with open(diff_file) as file:
    for row in file:
        d1, d2, op = row.rstrip().split(' ')
        # get files where to do difference
        if(op == 'd'):
            i_date1 = [d[1] for d in bil_files].index(d1)
            i_date2 = [d[1] for d in bil_files].index(d2)
            
            # get filenames based on timestamp
            f_date1 = bil_files[i_date1][0]
            f_date2 = bil_files[i_date2][0]
            
            data_d1 = read_file(os.path.join(data_path, f_date1), nrow, ncol)
            data_d2 = read_file(os.path.join(data_path, f_date2), nrow, ncol)
    
            # diff of data date2 - date1
            diff_data = diff_dates(data_d1, data_d2)
            
            output_path = os.path.join(data_path, '{}_cumul_displ_{}-{}.tif'.format(direction, bil_files[i_date1][1], bil_files[i_date2][1]))
            save_to_file(output_path, diff_data, nrow, ncol, prj, transf)



