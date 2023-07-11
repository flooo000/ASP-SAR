#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
process_stereo.py
----------------------
Process all SAR data pairs with ASP parallel_stereo. It uses the current settings of asp_parameters.txt in the project directory. The list file containing the pairs has to be in the format of MasTer (see MasTer prepa_MSBAS.sh)

Usage: process_stereo.py [--u] --data=<path> --pairs=<path>
proces_stereo.py -h | --help

Options:
--data=<path>       Path to directory with linked and coregistered data (prepared in prepare_correl_dir.py); if directory is to be updated, this dir must be the working directory (indicated by a timestamp)
--pairs=<path>      Path to .txt-file with list of image pairs
--u                 Update working directory with new data pairs (30.6.23: TO BE IMPLEMENTED)
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

def stereo_single_pair(data_dir, working_dir, date1, date2, update):
    # need to pass update information to sh script
    subprocess.call('run_stereo.sh {} {} {} {} {}'.format(data_dir, working_dir, date1, date2, update), shell=True, stdout=sys.stdout, stderr=subprocess.STDOUT, env=os.environ)

def stereo_pair_list(data_dir, working_dir, pair_list, update):
    pair_df = pd.read_csv(pair_list, sep='\s+')

    # copy file to dir instead of using link -> if original is changed, no impact in dir
    shutil.copy(pair_list, os.path.join(working_dir, os.path.basename(pair_list)))

    for index, rows in pair_df.iterrows():
        date1, date2 = rows['Master'], rows['Slave']
        if(os.path.isdir(os.path.join(working_dir, '{}_{}'.format(date1, date2)))):
            continue
        else:
            print('Start processing: {}_{}'.format(date1, date2))
            stereo_single_pair(data_dir, working_dir, date1, date2, update)
            print('Finished processing: {}_{}'.format(date1, date2))

    
########
# MAIN #
########

arguments = docopt.docopt(__doc__)

update = arguments['--u']

if(update):
    working_dir = arguments['--data']
    pair_list = arguments['--pairs']
    print('UPDATE', work_dir, pair_list)
else:
    data_dir = arguments['--data']
    pair_list = arguments['--pairs']
    print('NEW', data_dir, pair_list)


# check if working dir is updated with new data or created from scratch
# depending on update information, processing inputs slightly change
if(update):
    # if update: input for the function is the WORKING DIRECTORY that will be updated
    # need parent of parent dir bc working_dir = DATA_DIR/CORREL/TIMESTAMP/..
    data_dir = Path(Path(working_dir).parent.absolute()).parent.absolute()
    print(data_dir)
    
    # get TIMESTAMP for log file
    now = datetime.datetime.now()
    timestamp = now.strftime('%Y%m%d_%H%M%S')

    # update info_log file, check if exists - yes -> just append command, else create like below
    if(os.path.isfile(os.path.join(working_dir, 'info_log.txt'))):
        with open(os.path.join(working_dir, 'info_log.txt'), 'a') as info_file:
            info_file.write('{}:{} {} {} {}\n'.format(timestamp, 'process_stereo.py', working_dir, pair_list, update))
    else:
        with open(os.path.join(working_dir, 'info_log.txt'), 'w') as info_file:
        # should contain the information about SAT and REGION
            info_file.write('{}\n'.format(working_dir))
        # the second input of process: PATH TO PAIR_LIST
            info_file.write('{}\n'.format(pair_list))
            info_file.write('########################################\n')
            info_file.write('{}:{} {} {} {}\n'.format(timestamp, 'process_stereo.py', working_dir, pair_list, update))

else:
    # prepare directories
    correl_dir = os.path.join(data_dir, 'CORREL')
    geotiff_dir = os.path.join(data_dir, 'GEOTIFF')

    # get TIMESTAMP for current processing dir
    now = datetime.datetime.now()
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    # WORKING DIRECTORY is DATA_DIR/CORREL/TIMESTAMP
    working_dir = os.path.join(correl_dir, timestamp)

    # create working directory for current run
    Path(working_dir).mkdir(parents=True, exist_ok=True)
    # Copy used asp_parameters to working directory
    shutil.copy(os.path.join(correl_dir, 'asp_parameters.txt'), os.path.join(working_dir, 'asp_parameters.txt'))
    
    # create short info.txt file
    with open(os.path.join(working_dir, 'info_log.txt'), 'w') as info_file:
        # should contain the information about SAT and REGION
        info_file.write('{}\n'.format(working_dir))
        # the second input of process: PATH TO PAIR_LIST
        info_file.write('{}\n'.format(pair_list))
        info_file.write('########################################\n')
        info_file.write('{}:{} {} {} {}\n'.format(timestamp, 'process_stereo.py', working_dir, pair_list, update))


# RUN PROCESSING #

stereo_pair_list(data_dir, working_dir, pair_list, update)

