#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_all2gif.py
-----------
Check the ALL2GIF.sh results before processing with ASP

Usage: check_all2gif.py --check=<path>
check_all2gif.py -h | --help

Options:
-h --help       Show this screen
--check         Path to ALL2GIF.sh results


"""
##########
# IMPORT #
##########

import os, sys
import numpy as np
import docopt

#############
# FUNCTIONS #
#############


def check_for_empty_files(all2gif_dir):
    out = []
    for d in os.listdir(all2gif_dir):
        # need to filter bc of _AMPLI directory
        if(os.path.isdir(os.path.join(all2gif_dir, d)) and d[0] == '2'):
            insar_param_file = os.path.join(all2gif_dir, d, 'i12', 'TextFiles', 'InSARParameters.txt')
            with open(insar_param_file, 'r') as f:
            # read lines of file and remove whitespace and comments (comments after \t\t)
                lines = [''.join(l.strip().split('\t\t')[0]) for l in f.readlines()]
                jump_index = lines.index('/* -5- Interferometric products computation */')
                img_dim = lines[jump_index + 2: jump_index + 4]

                ncol, nrow = int(img_dim[0].strip()), int(img_dim[1].strip())
                if(ncol == 0):
                    out += [d]
                #print('{}\t{}\t{}'.format(d.split('_')[1], ncol, nrow))
    return out

########
# MAIN #
########

arguments = docopt.docopt(__doc__)

all2gif_dir = arguments["--check"]

empty_files = check_for_empty_files(all2gif_dir)

if(not empty_files):
    print('Everything should be fine, can continue with process_stereo')
else:
    print('Check following directories; adjust LLRGCO & LLAZCO and process ALL2GIF again')
    for d in empty_files:
        print(os.path.join(all2gif_dir, d))
        

