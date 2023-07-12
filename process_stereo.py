#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
process_stereo.py
----------------------
Process all SAR data pairs with ASP parallel_stereo. It uses the current settings of asp_parameters.txt in the project directory. The list file containing the pairs has to be in the format of MasTer (see MasTer prepa_MSBAS.sh)

Usage: process_stereo.py [--f] --data=<path> --pairs=<path>
proces_stereo.py -h | --help

Options:
--data=<path>       Path to directory with linked and coregistered data (prepared in prepare_correl_dir.py); if directory is to be updated, this dir must be the working directory (indicated by a timestamp)
--pairs=<path>      Path to .txt-file with list of image pairs
--f                 Force complete recomputation
-h --help           Show this screen

"""

##########
# IMPORT #
##########

import os, sys
import numpy as np
from osgeo import gdal
import pandas as pd
from pathlib import Path
import datetime
import shutil
import docopt
import subprocess 

#############
# FUNCTIONS #
#############

def stereo_single_pair(data_dir, correl_dir, date1, date2):
    # need to pass update information to sh script
    # TODO:check if update is needed
    subprocess.call('run_stereo.sh {} {} {} {}'.format(data_dir, correl_dir, date1, date2), shell=True, stdout=sys.stdout, stderr=subprocess.STDOUT, env=os.environ)

def stereo_pair_list(data_dir, correl_dir, pair_list):
    pair_df = pd.read_csv(pair_list, sep='\s+')

    # copy file to dir instead of using link -> if original is changed, no impact in dir
    # check if table file is already existing, if yes - replace
    shutil.copy(pair_list, os.path.join(correl_dir, os.path.basename(pair_list)))

    for index, rows in pair_df.iterrows():
        date1, date2 = rows['Master'], rows['Slave']
        if(os.path.isdir(os.path.join(correl_dir, '{}_{}'.format(date1, date2)))):
            continue
        else:
            print('Start processing: {}_{}'.format(date1, date2))
            stereo_single_pair(data_dir, correl_dir, date1, date2)
            print('Finished processing: {}_{}'.format(date1, date2))

    
########
# MAIN #
########

arguments = docopt.docopt(__doc__)

# directory with all data stored, also contains now asp_parameters.txt
# data_dir/CORREL -> new "working dir"
data_dir = arguments['--data']

pair_list = arguments['--pairs']

# instead of update - only calculate new pairs from table (but already implemented in stereo_pair_list)
force = arguments['--f']

# if force - remove CORREL shutil.rmtree()


    # prepare directories
correl_dir = os.path.join(data_dir, 'CORREL')
geotiff_dir = os.path.join(data_dir, 'GEOTIFF')

if(force):
    # remove old CORREL dir with all contents and create new empty one
    print('FORCE RECOMPUTATION: REMOVE OLD CORREL')
    shutil.rmtree(correl_dir)
    Path(correl_dir).mkdir(parents=True, exist_ok=True)

    ## save information in info_log.txt

    # get TIMESTAMP for log file
now = datetime.datetime.now()
timestamp = now.strftime('%Y%m%d_%H%M%S')

if(os.path.isfile(os.path.join(data_dir, 'info_log.txt'))):
    with open(os.path.join(data_dir, 'info_log.txt'), 'a') as info_file:
        info_file.write('{}:{} {} {} {}\n'.format(timestamp, 'process_stereo.py', data_dir, pair_list, force))
else:
    # create short info.txt file
    with open(os.path.join(data_dir, 'info_log.txt'), 'w') as info_file:
            # should contain the information about SAT and REGION
        info_file.write('{}\n'.format(data_dir))
            # the second input of process: PATH TO PAIR_LIST
        info_file.write('{}\n'.format(pair_list))
        info_file.write('########################################\n')
        info_file.write('{}:{} {} {} {}\n'.format(timestamp, 'process_stereo.py', data_dir, pair_list, force))


# RUN PROCESSING #

stereo_pair_list(data_dir, correl_dir, pair_list)

