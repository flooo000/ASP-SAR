#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
compute_opt_displ_angles.py
--------------
Computes the optical displacement angles from optical EW/SN displacement maps. Adjusted to follow the convetion: North=0, East=90.., positive in clockwise direction. Also generates a map for the displacement amplitude

Usage: compute_opt_displ_angles.py --we=<path> --sn=<path> --dest=<path> --name=<value>  
compute_opt_displ_angles.py -h | --help

Options:
-h | --help             Show this screen
--we                    Path to WE-displacement map
--sn                    Path to SN-displacement map
--dest                  Path to destination directory
--name                  Name of output file

"""

##########
# IMPORT #
##########

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import os, sys
from osgeo import gdal
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

we_displ_file = arguments['--we']
sn_displ_file = arguments['--sn']

dest_path = arguments['--dest']
name = arguments['--name']

output_file_angles = os.path.join(dest_path, 'WE_SN_{}_displacement_angles_norm.tif'.format(name))
output_file_amplitude = os.path.join(dest_path, 'WE_SN_{}_displacement_amplitude.tif'.format(name))

# ncols, nlines, proj, geotransform are all the same
we_displ, we_ncols, we_nlines, we_proj, we_geotransform = read_tif(we_displ_file)
sn_displ, sn_ncols, sn_nlines, sn_proj, sn_geotransform = read_tif(sn_displ_file)

# compute the displacement angles
displ_angles = np.degrees(np.arctan2(-sn_displ, we_displ))
displ_angles_norm = np.where((displ_angles + 90) < 0, (displ_angles + 90) + 360, displ_angles + 90)

# save displacement angles
print('Save displacement angles')
save_to_file(displ_angles_norm, output_file_angles, we_ncols, we_nlines, we_proj, we_geotransform)

# compute displacement amplitude
displ_amplitude = np.sqrt(we_displ**2 + sn_displ**2)

# save displacement amplitude
print('Save displacement amplitudes')
save_to_file(displ_amplitude, output_file_amplitude, we_ncols, we_nlines, we_proj, we_geotransform)




