#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
georef_maps.py
----------------
Georeferences an input .r4 map to the same reference as a given reference map.Both maps MUST have the same extent. 

Usage: georef_maps.py --map=<path> --dest=<path> --ref=<path> --name=<value>
georef_maps.py -h | --help

Options:
-h | --help             Show this screen
--map                   Path to map in .r4 format
--dest                  Path to destination directory
--ref                   Path to reference map
--name                  Naming of output file

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


########
# MAIN #
########

arguments = docopt.docopt(__doc__)

map_file = arguments['--map']
map_name = os.path.basename(map_file).split('.')[0]

dest_path = arguments['--dest']

ref_file = arguments['--ref']

name = arguments['--name']

# get all image parameter from ref file 
ds_ref = gdal.Open(ref_file)
ncol, nrow = ds_ref.RasterXSize, ds_ref.RasterYSize
proj = ds_ref.GetProjection()
geotransform = ds_ref.GetGeoTransform()

# read .r4 file
map_data = np.fromfile(map_file, dtype=np.float32)
map_data = map_data.reshape(nrow, ncol)

output_path = os.path.join(dest_path, '{}_{}.tif'.format(name, map_name))

save_to_file(map_data, output_path, ncol, nrow, proj, geotransform)




