#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_correlation.py
----------------
Plots the histogramm and the standard deviation of a selected area of an image.

Usage: check_correlation.py --data=<path> --area=<values>
check_correlation.py -h | --help

Options:
-h | --help         Show this screen
--data              Path to input image
--area              Select a specific region xmin,xmax,ymin,ymax

"""

##########
# IMPORT #
##########

import os, sys
import numpy as np
from osgeo import gdal
import pandas as pd
from pathlib import Path
import docopt
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle

#############
# FUNCTIONS #
#############

def read_from_file(input_file):

    ds = gdal.OpenEx(input_file, allowed_drivers=['GTiff'])
    ds_band = ds.GetRasterBand(1)
    data = ds_band.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize)
    ncol, nrow = ds.RasterXSize, ds.RasterYSize
    return (data, ncol, nrow)

def crop_data(data, xmin, xmax, ymin, ymax):
    return data[ymin:ymax+1, xmin:xmax]

def get_crop_statistics(crop):

    print('Median of crop: {}'.format(np.nanmedian(crop)))
    print('Mean of crop: {}'.format(np.nanmean(crop)))
    print('Standard deviation of crop: {}'.format(np.nanstd(crop)))

def plot_crop(input_file, area_vals):

    data, ncol, nrow = read_from_file(input_file)
    area_vals = [int(v) for v in area_vals]
    xmin, xmax, ymin, ymax = area_vals
    
    crop = crop_data(data, xmin, xmax, ymin, ymax)
    get_crop_statistics(crop)

    fig = plt.figure(constrained_layout=True)
    axs = fig.subplot_mosaic([['Left', 'TopRight'],['Left', 'BottomRight']],
                          gridspec_kw={'width_ratios':[2, 1]})

    im = axs['Left'].imshow(data)
    axs['Left'].add_patch(Rectangle((xmin,ymin), xmax-xmin, ymax-ymin,edgecolor='r', fill=False))
    fig.colorbar(im)

    axs['Left'].set_title('Full Image')

    axs['TopRight'].imshow(crop)
    axs['TopRight'].set_title('Cropped Image')

    axs['BottomRight'].hist(crop, bins=20)
    axs['BottomRight'].set_title('Histogram')

    plt.show()


########
# MAIN #
########

arguments = docopt.docopt(__doc__)

input_file = arguments['--data']

area = arguments['--area']

# maybe add later option to not plot only an area
if(area):
    # xmin, xmax - columns
    # ymin. ymax - lines
    area_vals = arguments['--area'].split(',')
else:
    print('none')

plot_crop(input_file, area_vals)


