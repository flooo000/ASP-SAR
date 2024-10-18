#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
plot_cube_profile.py
--------------
Plot a profil line of a given cube.

Usage: plot_cube_profile.py --cube=<path> --lstart=<value> --lend=<value> --list_dates=<path> [--aspect=<path>] [--amplitude=<path>]
plot_cube_profile.py --help

Options:
-h | --help             Show this screen
--cube                  Path to cube file
--lstart                Start coordinate of line (x,y)
--lend                  End coordiante of line (x,y)
--list_dates            Path to images_retenues file
--aspect                Path to aspect map
--amplitude             Path to displacement amplitude 

"""

##########
# IMPORT #
##########

import os, sys
import numpy as np
from numpy.lib.stride_tricks import as_strided
from osgeo import gdal
from pathlib import Path
import docopt
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import pandas as pd

#############
# FUNCTIONS #
#############

def read_tif(input_file):
    ds = gdal.OpenEx(input_file, allowed_drivers=['GTiff'])
    ds_band = ds.GetRasterBand(1)
    values = ds_band.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize)

    return values

def get_cube_dimension(cube_file):
    ds = gdal.Open(cube_file)
    ncols, nlines = ds.RasterXSize, ds.RasterYSize
    n_img = ds.RasterCount
    
    img_data = (nlines, ncols, n_img)

    return img_data

def read_cube(cube_file, ncol, nlines, n_img):

    print('Start reading cube file')

    cubei = np.fromfile(cube_file,dtype=np.float32)
    cube = as_strided(cubei[:nlines*ncol*n_img])

    kk = np.flatnonzero(np.logical_or(cube==9990, cube==9999))
    cube[kk] = float('NaN')
    maps_temp = as_strided(cube.reshape((nlines,ncol,n_img)))
    maps = np.copy(maps_temp)

    print('Finished reading cube file')

    return maps

def prepare_arrows(plot_map, lstart, lend, angles, amplitudes):
    xmin = min(lstart[0], lend[0])
    xmax = max(lstart[0], lend[0])
    ymin = min(lstart[1], lend[1])
    ymax = max(lstart[1], lend[1])

    # define the size of the bounding box to extent over the given coordiantes
    expand_by = 50
    xmin = max(0, xmin - expand_by)  
    xmax = min(plot_map.shape[1], xmax + expand_by)  
    ymin = max(0, ymin - expand_by)  
    ymax = min(plot_map.shape[0], ymax + expand_by) 
    
    # convert the angles
    angles_rad = np.radians(90 - angles)

    x_full, y_full = np.meshgrid(np.arange(0, plot_map.shape[1]), np.arange(0, plot_map.shape[0]))

    # grid within bound box with 20 pixel spacing
    sampling = 10
    x_bounded = x_full[ymin:ymax:sampling, xmin:xmax:sampling]  
    y_bounded = y_full[ymin:ymax:sampling, xmin:xmax:sampling]
    
    if(amplitudes is not None):
        u = amplitudes[ymin:ymax:sampling, xmin:xmax:sampling] * np.cos(angles[ymin:ymax:sampling, xmin:xmax:sampling])
        v = amplitudes[ymin:ymax:sampling, xmin:xmax:sampling] * np.sin(angles[ymin:ymax:sampling, xmin:xmax:sampling])
    else:
        u = np.cos(angles[ymin:ymax:sampling, xmin:xmax:sampling])
        v = np.sin(angles[ymin:ymax:sampling, xmin:xmax:sampling])

    return (x_bounded, y_bounded, u, v)

########
# MAIN #
########

arguments = docopt.docopt(__doc__)

cube_file = arguments['--cube']

# images retenues file 
list_dates_file = arguments['--list_dates']

lstart = tuple(map(int, arguments['--lstart'].split(',')))
lend = tuple(map(int, arguments['--lend'].split(',')))

if(arguments['--amplitude']):
    amplitudes = read_tif(arguments['--amplitude'])
else:
    amplitudes = None

if(arguments['--aspect']):
    angles = read_tif(arguments['--aspect'])
else:
    angles = None


cube_dim = get_cube_dimension(cube_file)
nlines, ncols, n_img = cube_dim

# read cube
maps = read_cube(cube_file, ncols, nlines, n_img)

# read dates to get date values

list_dates = np.loadtxt(list_dates_file)
dates = list_dates[:,1].astype(str)
dates_str = [d.split('.')[0] for d in dates]
dates_conv = pd.to_datetime(dates_str, format='%Y%m%d').strftime('%d/%m/%Y')

# set line for the getting the coordinates
num_steps = max(abs(lend[1] - lstart[1]), abs(lend[0] - lstart[0]))

rows = np.linspace(lstart[1], lend[1], num_steps).astype(int)
cols = np.linspace(lstart[0], lend[0], num_steps).astype(int)

# plot last map of cube for reference
slice_to_plot = maps[:,:,n_img-1] 

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

# plot one map of the cube as orientation
cax1 = ax1.imshow(slice_to_plot, cmap='Spectral', vmin=-20, vmax=20)
ax1.plot(cols, rows, color='black')  # Plot the line
ax1.set_title('Profile with cumulative displacement map')

# plot dots every n_dots pixel to have orientation
n_dots = 20
for j in range(0, len(cols), n_dots):
    ax1.plot(cols[j], rows[j], marker='o', color='grey', markersize=3)

# plot start (pyramid) and end (cross) pixel for reference
ax1.plot(lstart[0], lstart[1], marker='^', color='black', markersize=5)  
ax1.plot(lend[0], lend[1], marker='x', color='black', markersize=5)

cbar1 = fig.colorbar(cax1, ax=ax1, orientation='horizontal', pad=0.15)
cbar1.set_label('Displacement [m]')

if(arguments['--aspect']):
    x_bounded, y_bounded, u, v = prepare_arrows(slice_to_plot, lstart, lend, angles, amplitudes)
    ax1.quiver(x_bounded, y_bounded, u, v, angles='uv', scale_units='xy', scale=0.1, color='r')

# define colormap for profile lines
cmap = cm.Spectral 
norm = mcolors.Normalize(vmin=0, vmax=n_img - 1)

# plot profile lines
for i in range(n_img):
    img_slice = maps[:,:,i]
    # get pixel along the line
    profile = img_slice[rows,cols] 
    
    # HARD CODED - change add one point
    # remove outliers values, maybe change at one point to variable from reading the metadata of image
    profile = np.where((profile > 50) | (profile < -50), np.nan, profile)

    ax2.plot(profile, color=cmap(norm(i)), label=f'Slice {i+1}', linewidth=1)

# necessary for colorbar
sm = cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])


cbar = fig.colorbar(sm, ax=ax2, orientation='horizontal', pad=0.15)
cbar.set_label('Dates')

num_ticks = 5 
tick_indices = np.linspace(0, len(dates) - 1, num_ticks).astype(int)
cbar.set_ticks(tick_indices)  
cbar.set_ticklabels(dates_conv[tick_indices]) 

ax2.set_xlim(0, len(profile))

ax2.set_title('Profile lines of cube')
ax2.set_xlabel('Profile Point Index')
ax2.set_ylabel('Displacement [m]')

# use n_dots to fit with the markers on line
ax2.set_xticks(np.arange(0, num_steps, n_dots))  # X-axis ticks every 20 pixels
ax2.grid(which='both', color='gray', linestyle='--', linewidth=0.5)

plt.tight_layout()
plt.show()

