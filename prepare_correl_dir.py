#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
prepare_correl_dir.py
--------------
Prepare the directory structure for further processing. Link all ALL2GIF results in the given destination dir.

Usage: prepare_correl_dir.py --data=<path> --dest=<path> [--u] 
prepare_correl_dir.py -h | --help

Options:
-h | --help         Show this screen
--data              Path to ALL2GIF results
--dest              Path to destination directory. Will be the processing directory
--u                 Only update the links

"""
##########
# IMPORT #
##########

import os, sys
import numpy as np
from osgeo import gdal
from matplotlib import pyplot as plt
import pandas as pd
import re
from pathlib import Path
from init_asp_parameters import init_asp_parameters 
import docopt

#############
# FUNCTIONS #
#############

def filter_mod_files(input_file):
    real_path = os.path.realpath(input_file)
    i12_path = os.path.dirname(os.path.dirname(real_path))
    insar_param_file = os.path.join(i12_path, 'TextFiles', 'InSARParameters.txt')
    with open(insar_param_file, 'r') as f:
        # read lines of file and remove whitespace and comments (comments after \t\t)
        lines = [''.join(l.strip().split('\t\t')[0]) for l in f.readlines()]
        #print(lines)
        jump_index = lines.index('/* -5- Interferometric products computation */')
        img_dim = lines[jump_index + 2: jump_index + 4]
        #print(img_dim)

    ncol, nrow = int(img_dim[0].strip()), int(img_dim[1].strip())
    if(ncol == 0):
        return False
    else:
        return True

def prepare_dir_list(input_path):
   
    # for preparation with ALL2GIF.sh
    # maybe problem with region name if condition is coded like this
    # data_dirs_paths = [os.path.join(input_path, d, 'i12', 'InSARProducts') for d in os.listdir(input_path) if(len(d.split('_')) == 7 and os.path.isdir(os.path.join(input_path, d)))]
    # this solution should work with ALL2GIF and other MasTer Massprocessing results (to be checked) 
    data_dirs_paths = [os.path.join(input_path, d, 'i12', 'InSARProducts') for d in os.listdir(input_path) if(d[0] == '2' and os.path.isdir(os.path.join(input_path, d)))]


    for d in os.listdir(input_path):
        if(os.path.isdir(d)):
            print(print(len(d.split('_'))))

    #compare_list = []
    out_list = []
    
    # walk through all i12/InSARProducts directories and save paths to DATE.VV.mod files in list
    # need to filter te results to link the mod files where interferometric dimensions in i12/TextFiles/InSARParameters.txt != 0
    for d in data_dirs_paths:
        for f in os.listdir(d):
            if(os.path.splitext(f)[1] == '.mod'):
                # only add mod files to list, where dimensions are != 0
                #compare_list += [os.path.join(d, f)]
                if(filter_mod_files(os.path.join(d, f))):
                    out_list += [os.path.join(d, f)]
                else:
                    continue
    
    # return list with path to mod files f.e. 
    # input_path/20220717_20220919/i12/InSARProducts/[DATE].VV.mod
    return out_list

# create link to every file in dst directory
def link_files(data_path_list, dst_path):
    print('Start linking files')
    for p in data_path_list:
        if(os.path.isfile(os.path.join(dst_path, os.path.basename(p)))):
            continue
        else:
            os.symlink(p, os.path.join(dst_path, os.path.basename(p)))
    print('Finished linking files')

def get_az_range_sampling(data_path_list, correl_path):
    # only need one InSARParameters.txt file bc azimuth and slant range sampling are same for all
    # need parent of parent dir bc in data_path_list are paths to DATE.mod files
    result_dir = os.path.dirname(os.path.dirname(data_path_list[0]))
    insar_param_file = os.path.join(result_dir, 'TextFiles', 'InSARParameters.txt')
    print(insar_param_file)
    with open(insar_param_file, 'r') as f:
        # read lines of file and remove whitespace
        lines = [''.join(l.strip().split('\t\t')) for l in f.readlines()]
        for l in lines:
            if('Azimuth sampling' in l):
                azimuth_sampl = l.split('/')[0].strip()
            if('Slant range sampling' in l):
                range_sampl = l.split('/')[0].strip()
                break

    sampling = pd.DataFrame(data={'AZ':[azimuth_sampl], 'SR':[range_sampl]})
    sampling.to_csv(os.path.join(correl_path, 'sampling.txt'), sep='\t', index=None)


########
# MAIN #
########

arguments = docopt.docopt(__doc__)

# path to data processed with MasTer
input_path = arguments['--data']
# path to where data should be linked to; directory for further processing
dst_path = arguments['--dest']
# update flag
update = arguments['--u']

data_path_list = prepare_dir_list(input_path)

if(update):
    print('Update directory')
    link_files(data_path_list, dst_path)
else:
    print('Initiate directory')
    link_files(data_path_list, dst_path)

    Path(os.path.join(dst_path, 'GEOTIFF')).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(dst_path, 'CORREL')).mkdir(parents=True, exist_ok=True)
    correl_path = os.path.join(dst_path, 'CORREL')
   
    # save asp_parameters and sampling in destination directory instead of CORREL
    init_asp_parameters(dst_path)

    get_az_range_sampling(data_path_list, dst_path)



