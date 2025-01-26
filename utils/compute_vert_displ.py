#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
compute_vert_displ.py
--------------
Compute the vertical displacements given horizontal displacements and vertical variations.

Usage: compute_vert_displ.py --we=<path> --sn=<path> --vert=<path> --dsm=<<path> --dest=<path> --name=<value>  
compute_opt_displ_angles.py -h | --help

Options:
-h | --help             Show this screen
--we                    Path to WE-displacement map
--sn                    Path to SN-displacement map
--vert                  Path to vertical variation map
--dsm                   Path to DSM map
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
dsm_diff_file = arguments['--vert']
dsm_file = arguments['--dsm']

dest_path = arguments['--dest']
name = arguments['--name']

output_path = os.path.join(dest_path, 'uz_optical_{}.tif'.format(name))

# read data
we_displ = read_tif(we_displ_file)[0]
sn_displ = read_tif(sn_displ_file)[0]
dsm_diff = read_tif(dsm_diff_file)[0]
dsm, dsm_cols, dsm_lines, dsm_proj, dsm_geotransf = read_tif(dsm_file)

# x, y dimensions = dsm_geotransf[1], dsm_geotransf[5]

# compute slope normals
dsm_dx, dsm_dy = np.gradient(dsm, dsm_geotransf[1], dsm_geotransf[5])
dsm_dz = -1 # upward
amplitude = np.sqrt(dsm_dx**2 + dsm_dy**2 + dsm_dz**2)

nx = dsm_dx / amplitude
ny = dsm_dy / amplitude
nz = dsm_dz / amplitude

vert_displ = dsm_diff - (we_displ * nx + sn_displ * ny)

print(vert_displ.shape)
print(dsm_cols, dsm_lines)

# can use any of the input ref values, here from dsm as it is used before
save_to_file(vert_displ, output_path, dsm_cols, dsm_lines, dsm_proj, dsm_geotransf) 
