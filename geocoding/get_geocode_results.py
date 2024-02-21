#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
get_geocode_results.py
--------------
Generates GEOCODED directory and links all the files from the GeoProjection directory.

Usage: get_geocode_results.py --data=<path> --dest=<path> --name=<value>
get_geocode_results.py -h | --help

Options:
-h | --help             Show this screen
--data                  Path to GeoProjection dir in MasTer directory
--dest                  Path to working directory, where results should be linked
--name                  Name of output directory for EXPORT/GEOCODED/name

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

def link_all_data(input_dir, dest_dir):

    for f in os.listdir(input_dir):
        ext = os.path.splitext(f)[1]
        if(ext == '.bil' or ext == '.hdr'):
            # f is filename
            print('Link {}'.format(f))
            if(os.path.exists(os.path.join(dest_dir, f))):
                continue
            else:
                os.symlink(os.path.join(input_dir, f), os.path.join(dest_dir, f))


########
# MAIN #
########

arguments = docopt.docopt(__doc__)

# directory within ../i12/GeoProjection
geo_master_dir = arguments['--data']

work_dir = arguments['--dest']

name = arguments['--name']
# 
output_dir = os.path.join(work_dir, 'EXPORT', 'GEOCODED', name)
Path(output_dir).mkdir(parents=True, exist_ok=True)

link_all_data(geo_master_dir, output_dir)




