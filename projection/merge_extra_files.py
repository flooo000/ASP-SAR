#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.py
--------------
Merge additional files, that are needed to run invers_pixel.py

Usage: merge_extra_files.py --imgret1=<Path> --imgret2=<Path> --dest=<Path>   
merge_extra_files.py -h | --help

Options:
-h | --help             Show this screen
--imgret1               Path to first image_retenues
--imgret2               Path to second image_retunues
--dest                  Path to destination directory

"""

##########
# IMPORT #
##########

import os, sys
import numpy as np
import pandas as pd
from pathlib import Path
import docopt
from datetime import datetime

#############
# FUCNTIONS #
#############

def date_to_float(date):
    date_str = str(date)
    d = datetime.strptime(date_str, '%Y%m%d')
    
    return (d.year + (d.month-1)/12.0 + (d.day-1)/365.0)

def merge_img_ret_files(imgret1_file, imgret2_file):

    header1 = ['index', 'date', 'nimg', 'date_dec', 'Bt', 'Bperp1']
    header2 = ['index', 'date', 'nimg', 'date_dec', 'Bt', 'Bperp2']    
    
    imgret1 = pd.read_csv(imgret1_file, header=None, sep='\s+')
    imgret1.columns = header1
    imgret2 = pd.read_csv(imgret2_file, header=None, sep='\s+')
    imgret2.columns = header2

    # sort by date_dec
    combined_imgret = pd.concat([imgret1, imgret2], ignore_index=True)
    combined_imgret = combined_imgret.sort_values(by=['date_dec'])
    new_index = range(1, len(combined_imgret) + 1)

    # set value to 0 where data is not available
    combined_imgret['Bperp1'] = combined_imgret['Bperp1'].fillna(0)
    combined_imgret['Bperp2'] = combined_imgret['Bperp2'].fillna(0)

    combined_imgret['index'] = new_index
    # update Bt column to have everything relative to merged first date
    combined_imgret['Bt'] = (combined_imgret['date'].apply(date_to_float) - date_to_float(combined_imgret['date'][0])).apply(lambda x: f"{x:.6f}")
    
    print(combined_imgret)
    return combined_imgret




def merge_rms_date_files(rmsdate1_file, rmsdate2_file):

    header = ['index', 'date_str', 'rms']

    rmsdate1 = pd.read_csv(rmsdate1_file, header=None, sep='\s+')
    rmsdate2 = pd.read_csv(rmsdate2_file, header=None, sep='\s+')
   
    combined_rmsdate = pd.concat([rmsdate1, rmsdate2], ignore_index=True)
    combined_rmsdate.columns = header
    
    combined_rmsdate['date'] = pd.to_datetime(combined_rmsdate['date_str'], format='%Y%m%d')

    combined_rmsdate = combined_rmsdate.sort_values(by=['date'])

    new_index = range(1, len(combined_rmsdate) + 1)

    combined_rmsdate['index'] = new_index


    return combined_rmsdate


########
# MAIN #
########

arguments = docopt.docopt(__doc__)

imgret1_file = arguments['--imgret1']
imgret2_file = arguments['--imgret2']

rmsdate1_file = os.path.join(os.path.dirname(imgret1_file), 'RMSdate')
rmsdate2_file = os.path.join(os.path.dirname(imgret2_file), 'RMSdate')

dest_path = arguments['--dest']

combined_imgret = merge_img_ret_files(imgret1_file, imgret2_file)
print(combined_imgret)
combined_rmsdate = merge_rms_date_files(rmsdate1_file, rmsdate2_file)


# adjust at one point

out_file_img_ret = os.path.join(dest_path, 'images_retenues_merged')
combined_imgret.to_csv(out_file_img_ret, index=False, header=False, sep=' ')

out_file_rmsdate = os.path.join(dest_path, 'inaps_merged.txt')
combined_rmsdate['rms'].to_csv(out_file_rmsdate, index=False, header=False)

