#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_correlation.py
----------------
Plots the histogramm and the standard deviation of a selected area of an image.
By default it reads .tif files, but other file formats are supported (.r4/.bil) as long is .hdr file exists

Usage: check_correlation.py --data=<path> --area=<values> [--nsbas] [--xp=<values>] [--yp=<values>]
check_correlation.py -h | --help

Options:
-h | --help         Show this screen
--data              Path to input image
--area              Select a specific region xmin,xmax,ymin,ymax
--nsbas             Input file format .r4/.bil (result of NSBAS processing) [Default: .tif]
--xp                Pixel coordinates x
--yp                Pixel coordinates y
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

def read_from_nsbas_file(input_file):
    input_path = os.path.dirname(input_file)
    filename = os.path.splitext(os.path.basename(input_file))[0]

    if(os.path.isfile(os.path.join(input_path, '{}.hdr'.format(filename)))):
        hdr_file = input_file
    else:
        # take depl_cumule to get image dimension
        hdr_file = os.path.join(input_path, 'depl_cumule')
    print('Get image dimension using: {}'.format(hdr_file))
    
    ds = gdal.Open(hdr_file)
    ncol, nrow = ds.RasterXSize, ds.RasterYSize

    data = np.fromfile(input_file, dtype=np.float32)
    data = data.reshape(nrow, ncol)

    return (data, ncol, nrow)


def crop_data(data, xmin, xmax, ymin, ymax):
    return data[ymin:ymax+1, xmin:xmax]

def get_crop_statistics(crop):

    print('Median of crop: {:.4f}'.format(np.nanmedian(crop)))
    print('Mean of crop: {:.4f}'.format(np.nanmean(crop)))
    print('Standard deviation of crop: {:.4f}'.format(np.nanstd(crop)))

def plot_crop(input_file, area_vals, nsbas, xpix, ypix):

    if(nsbas):
        data, ncol, nrow = read_from_nsbas_file(input_file)
    else:
        data, ncol, nrow = read_from_file(input_file)
    area_vals = [int(v) for v in area_vals]
    xmin, xmax, ymin, ymax = area_vals
    
    crop = crop_data(data, xmin, xmax, ymin, ymax)
    get_crop_statistics(crop)


    if(xpix and ypix):
        xlist = xpix.split(',')
        ylist = ypix.split(',')

        if(len(xlist) != len(ylist)):
            print('Dimensions of xpix and ypix are not the same')

        npix = len(xlist)

        for i in range(npix):
            x, y = int(xlist[i]), int(ylist[i])
            value = data[y][x]
            print('Value of coordinate ({},{}): {:.4f}'.format(x, y, value))

    fig = plt.figure(constrained_layout=True)
    axs = fig.subplot_mosaic([['Left', 'TopRight'],['Left', 'BottomRight']],
                          gridspec_kw={'width_ratios':[2, 1]})
   
   
    # can also be done as input parameter if needed
    vmax = np.nanpercentile(data, 98)
    vmin = np.nanpercentile(data, 2)

    im = axs['Left'].imshow(data, vmax=vmax,vmin=vmin)
    
    if(xpix and ypix):
        for i in range(npix):
            x, y = int(xlist[i]), int(ylist[i])
            axs['Left'].scatter(x, y, color='r', marker='x', s=10)
            axs['Left'].text(x, y, i, color='k', fontsize=10)

    axs['Left'].add_patch(Rectangle((xmin,ymin), xmax-xmin, ymax-ymin,edgecolor='r', fill=False))
    fig.colorbar(im)

    axs['Left'].set_title('Full Image')

    axs['TopRight'].imshow(crop)
    axs['TopRight'].set_title('Cropped Image')
    
    # Find a way to plot point in cropped area too - problem with changed image dimension 
    #if(xpix and ypix):
    #    for i in range(npix):
    #        x, y = int(xlist[i]), int(ylist[i])
    #        axs['TopRight'].scatter(x, y, color='r', marker='x')

    axs['BottomRight'].hist(crop, bins=20)
    axs['BottomRight'].set_title('Histogram')

    plt.show()


########
# MAIN #
########

arguments = docopt.docopt(__doc__)

input_file = arguments['--data']

area = arguments['--area']

# check if it is file from nsbas processing (.r4)
nsbas = arguments['--nsbas']

# get coordinates of pixel
xpix = arguments['--xp']
ypix = arguments['--yp']


# maybe add later option to not plot only an area
if(area):
    # xmin, xmax - columns
    # ymin. ymax - lines
    area_vals = arguments['--area'].split(',')
else:
    print('none')

plot_crop(input_file, area_vals, nsbas, xpix, ypix)

