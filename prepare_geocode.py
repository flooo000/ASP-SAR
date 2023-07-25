"""
prepare_geocode.py
--------------
Generates TO_GEOCODE directory with all files linked in needed format.

Usage: prepare_geocode.py --data=<path> [--dest=<path>]
prepare_geocode.py -h | --help

Options:
-h | --help             Show this screen
--data                  Path to NSBAS directory
--dest                  Path to destination directory [default: create TO_GEOCODE in EXPORT directory]

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
        if(len(f.split('.')) == 2):
            # f is filename
            print('Link {}'.format(f))
            os.symlink(os.path.join(input_dir, f), os.path.join(dest_dir, 'REGEOC_{}'.format(f)))

def copy_all_data(input_dir, dest_dir):
    for f in os.listdir(input_dir):
        if(len(f.split('.')) == 2):
            # f is filename
            print('Copy {}'.format(f))
            shutil.copy(os.path.join(input_dir, f), os.path.join(dest_dir, 'REGEOC_{}'.format(f)))


########
# MAIN #
########

arguments = docopt.docopt(__doc__)

nsbas_dir = arguments['--data']

export_dir = os.path.dirname(nsbas_dir)

h_data_dir = os.path.join(nsbas_dir, 'H')
v_data_dir = os.path.join(nsbas_dir, 'V')

if(arguments['--dest']):
    output_dir = arguments['--dest']
    
    copy_all_data(h_data_dir, output_dir)
    copy_all_data(v_data_dir, output_dir)
else:
    output_dir = os.path.join(export_dir, 'TO_GEOCODE')
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    link_all_data(h_data_dir, output_dir)
    link_all_data(v_data_dir, output_dir)









