"""
crop_file.py
---------------
Crop input file to given extent.

Usage: crop_file.py --infile=<path> --extent=<values>
crop_file.py -h | --help

Options:
-h | --help             Show this screen
--infile                Input file
--extent                Crop extent as xmin,xmax,ymin,ymax

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

def read_from_file(input_file):

    ds = gdal.OpenEx(input_file, allowed_drivers=['GTiff'])
    ds_band = ds.GetRasterBand(1)
    data = ds_band.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize)
    ncol, nrow = ds.RasterXSize, ds.RasterYSize
    # return (data, ncol, nrow) XSize=col YSize=row
    return (data, ncol, nrow)

def save_to_file(data, out_file, ncol, nrow):
    fid = open(out_file, 'wb')
    data.flatten().astype('float32').tofile(fid)

    out_rsc = os.path.join(os.path.split(out_file)[0], '{}.rsc'.format(os.path.split(out_file)[1]))
    f = open(out_rsc, 'w')
    f = open(out_rsc, "w")
    f.write("""\
      WIDTH                 %d
      FILE_LENGTH           %d
      XMIN                  0
      XMAX                  %d
      YMIN                  0
      YMAX                  %d
      """ % (ncol, nrow, ncol-1, nrow-1))
    f.close()

def crop_data(data, xmin, xmax, ymin, ymax):
    return data[ymin:ymax+1, xmin:xmax+1]

def crop_single_file(input_file, extent_vals):
    
    data_dir, filename = os.path.split(input_file)
    dest_dir = os.path.join(data_dir, 'CROP_{}.r4'.format(filename.split('.')[0]))

    data = read_from_file(input_file)[0]
    xmin,xmax,ymin,ymax = [int(v) for v in extent_vals]
    
    crop = crop_data(data, xmin, xmax, ymin, ymax)
    
    nrows, ncol = crop.shape
    print(nrows, ncol)

    save_to_file(crop, dest_dir, ncol, nrows)
    



########
# MAIN #
########

# add functionality at one point - crop all files in given directory

arguments = docopt.docopt(__doc__)

input_file = arguments['--infile']

extent_vals = arguments['--extent'].split(',')


crop_single_file(input_file, extent_vals)





