"""
compute_disp_ampli.py
----------------
Generated DISP_AMPLI directory with amplitude and angles of displacements.

Usage: compute_disp_ampli.py --data=<path>
compute_disp_ampli.py -h | --help

Options:
-h | --help             Show this screen
--data                  Path to CORREL directory

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

def save_to_file(data, output_path, ncol, nrow):
    drv = gdal.GetDriverByName('GTiff')
    dst_ds = drv.Create(output_path, ncol, nrow, 1, gdal.GDT_Float32)
    dst_band = dst_ds.GetRasterBand(1)
    dst_band.WriteArray(data)

# dont confuse naming:
# azimuth - horizontal; range - vertical
def compute_ampli_angle_displ(az_data, rg_data):
    
    # get size from one result
    ncol, nrow = az_data[1], az_data[2]
    
    ampli, angle = np.zeros((nrow, ncol)), np.zeros((nrow, ncol))
    
    ampli = np.sqrt(az_data[0]**2 + rg_data[0]**2)
    # check this
    angle = np.rad2deg(np.arctan(az_data[0]/rg_data[0]))

    return ampli, angle


def group_by_date(data_list):
    groups = {}
    for f in data_list:
        date = f.split('-')[0]
        groups.setdefault(date, []).append(f)
    return groups



########
# MAIN #
########

arguments = docopt.docopt(__doc__)

correl_path = arguments['--data']

adj_data_path = os.path.join(correl_path, 'EXPORT', 'ADJUSTED')
dest_path = os.path.join(correl_path, 'EXPORT', 'AMPLI_DISP')
Path(dest_path).mkdir(parents=True, exist_ok=True)

# filter data -> get only .tif files
data_list = [f for f in os.listdir(adj_data_path) if os.path.isfile(os.path.join(adj_data_path, f)) and os.path.splitext(f)[1] == '.tif']

# important to sort -> to have in result ...H and ...V
data_list_sorted = data_list.sort()
grouped_data = group_by_date(data_list)

for date, f in grouped_data.items():
    # because of sort - f[0] - horizontal/range; f[1] - vertical/azimuth
    rg_data = read_from_file(os.path.join(adj_data_path, f[0]))
    az_data = read_from_file(os.path.join(adj_data_path, f[1]))

    print('Start processing: {}'.format(date))
    ampli, angle = compute_ampli_angle_displ(az_data, rg_data)
    
    # image size is stored in az_data and rg_data - use only one
    #save_to_file(ampli, os.path.join(dest_path, '{}_AMPLI_DISP.tif'.format(date)), az_data[1], az_data[2])
    save_to_file(angle, os.path.join(dest_path, '{}_ANGLE_DISP.tif'.format(date)), az_data[1], az_data[2])
    print('Finished processing: {}'.format(date))
    



