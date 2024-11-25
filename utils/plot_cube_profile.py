#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
plot_cube_profile.py
--------------
Plot a profil line of a given cube.

Usage: plot_cube_profile.py --cube=<path> --lstart=<value> --lend=<value> --list_dates=<path> [--aspect=<path>] [--amplitude=<path>] [--cbarmarks=<values>] [--dem=<path>] [--window=<value>] [--ylim=<value>] [--crop=<values>]
plot_cube_profile.py --help

Options:
-h | --help             Show this screen
--cube                  Path to cube file
--lstart                Start coordinate of line (x,y)
--lend                  End coordiante of line (x,y)
--list_dates            Path to images_retenues file
--aspect                Path to aspect map
--amplitude             Path to displacement amplitude 
--cbarmarks             Dates to mark in colorbar given date1,date2,date3,... in YYYYMMDD [Default: None]
--dem                   Path to DEM file to plot profile 
--window                Window size to smooth the profile [Default: 1] 
--ylim                  Set ylim extent as min,max [Default: automatic]
--crop                  Define crop area for cumulative displacemet map as xmin,xmax,ymin,ymax [Default: full image]

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
import matplotlib.gridspec as gridspec
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

if(arguments['--dem']):
    dem = read_tif(arguments['--dem'])
else:
    dem = None

# plot the given dates in colorbar 
if(arguments['--cbarmarks']):
    mark_dates = arguments['--cbarmarks'].split(',')
    mark_dates_conv = pd.to_datetime(mark_dates, format='%Y%m%d').strftime('%d/%m/%Y')
else:
    mark_dates = None

cube_dim = get_cube_dimension(cube_file)
nlines, ncols, n_img = cube_dim

# read cube
maps = read_cube(cube_file, ncols, nlines, n_img)

# read dates to get date values

list_dates = np.loadtxt(list_dates_file)
dates = list_dates[:,1].astype(str)
dates_str = [d.split('.')[0] for d in dates]
dates_conv = pd.to_datetime(dates_str, format='%Y%m%d').strftime('%d/%m/%Y')

if(arguments['--dem']):
    fig = plt.figure(figsize=(12, 8))
    # define grid space to place ax3 below ax2
    gs = gridspec.GridSpec(2, 2, height_ratios=[1, 0.25])

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 1])

else:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

# set line for the getting the coordinates
num_steps = max(abs(lend[1] - lstart[1]), abs(lend[0] - lstart[0]))

rows = np.linspace(lstart[1], lend[1], num_steps).astype(int)
cols = np.linspace(lstart[0], lend[0], num_steps).astype(int)

# plot last map of cube for reference
# masked map based of values outside 1st-99th percentile
p1, p2 = np.nanpercentile(maps[:,:,n_img-1], 1), np.nanpercentile(maps[:,:,n_img-1], 99)
map_plot = np.ma.masked_outside(maps[:,:,n_img-1], p1, p2) 

# adjust to plot the profile according to the crop
if(arguments['--crop']):
    xmin,xmax,ymin,ymax = arguments['--crop'].split(',')
    map_crop = map_plot[int(ymin):int(ymax), int(xmin):int(xmax)]
    cax1 = ax1.imshow(map_crop, cmap='Spectral', vmin=-20, vmax=20)
else:
    cax1 = ax1.imshow(map_plot, cmap='Spectral', vmin=-20, vmax=20)

ax1.plot(cols, rows, color='black')  # Plot the line
ax1.set_title('Profile with cumulative displacement map')

# plot dots every n_dots pixel to have orientation
n_dots = int(num_steps/10)
print('Sampling for profile line dots: {} pixel'.format(n_dots))
for j in range(0, len(cols), n_dots):
    ax1.plot(cols[j], rows[j], marker='o', color='grey', markersize=3)

# plot start (pyramid) and end (cross) pixel for reference
ax1.plot(lstart[0], lstart[1], marker='^', color='black', markersize=5)  
ax1.plot(lend[0], lend[1], marker='x', color='black', markersize=5)


cbar1 = fig.colorbar(cax1, ax=ax1, orientation='horizontal', pad=0.15)
cbar1.set_label('Displacement [m]')

if(arguments['--aspect']):
    x_bounded, y_bounded, u, v = prepare_arrows(map_plot, lstart, lend, angles, amplitudes)
    ax1.quiver(x_bounded, y_bounded, u, v, angles='uv', scale_units='xy', scale=0.1, color='r')

# define colormap for profile lines
cmap = cm.Spectral 
norm = mcolors.Normalize(vmin=0, vmax=n_img - 1)

last_map_profile = maps[rows,cols,n_img-1]
mask_indices = np.where((last_map_profile > p2) | (last_map_profile < p1))[0]

# take mean values of given window around each pixel of the profile
if(arguments['--window']):
    window_size = int(arguments['--window'])
    half_window = window_size // 2
    print('Window size to smooth the profile: {} pixel'.format(window_size))
else:
    window_size = 1
    half_window = 0
    print('No smoothing of profile')


# plot profile lines
for i in range(n_img):
    img_slice = maps[:,:,i]
    # get pixel along the line
    profile = img_slice[rows,cols]

    profile_mean = []

    # smooth based on a given window if wanted
    for r, c in zip(rows, cols):
        # Extract window around the current point
        row_start = max(0, r - half_window)
        row_end = min(img_slice.shape[0], r + half_window + 1)
        col_start = max(0, c - half_window)
        col_end = min(img_slice.shape[1], c + half_window + 1)

        window = img_slice[row_start:row_end, col_start:col_end]
        # results look better with median than mean
        mean_value = np.nanmedian(window)
        profile_mean.append(mean_value)
    
    # filter maybe also based on the percentile (like for plot on left)
    #profile = np.where((profile > p2) | (profile < p1), np.nan, profile)

    # pixel that are outside the p1:p2 range
    mask_indices = np.where((profile_mean > p2) | (profile_mean < p1))[0]

    # mask pixel where absolute differences 
    abs_diff_indices = np.where(np.abs(np.diff(profile)) > 5)[0]

    # Create a mask for the entire profile array
    mask = np.full(profile.shape, False)

    # Apply a window around each out-of-range index
    #for idx in mask_indices:
    #    start_idx = max(0, idx - 2)  # Ensure no negative indices
    #    end_idx = min(len(profile), idx + 3)  # Include idx + 5 and ensure within bounds
    #    mask[start_idx:end_idx] = True

    #for idx in abs_diff_indices:
    #    start_idx = max(0, idx - 2)
    #    end_idx = min(len(profile), idx + 3)
    #    mask[start_idx:end_idx] = True

    # Mask the profile with NaNs in the specified range
    profile_masked = np.where(mask, np.nan, profile_mean)

    #ax2.scatter(range(len(profile_mean)), profile_masked, color=cmap(norm(i)), label=f'Slice {i+1}', s=0.2)
    ax2.plot(profile_masked, color=cmap(norm(i)), label=f'Slice {i+1}', linewidth=1)
    #ax2.plot(profile_mean, color=cmap(norm(i)), label=f'Slice {i+1}', linewidth=1)


# necessary for colorbar
sm = cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])


cbar = fig.colorbar(sm, ax=ax2, orientation='horizontal', pad=0.15)
cbar.set_label('Dates')


num_ticks = 5
tick_indices = np.linspace(0, len(dates) - 1, num_ticks).astype(int)
cbar.set_ticks(tick_indices)
cbar.set_ticklabels(dates_conv[tick_indices])

# plot vertical line for dates of displacement periods
if(mark_dates):
    for date_str in mark_dates_conv:
        if date_str in dates_conv:
            index = list(dates_conv).index(date_str)
            cbar.ax.axvline(index, color='red', linestyle='--', linewidth=1.5)

ax2.set_xlim(0, len(profile))

if(arguments['--ylim']):
    ylim = arguments['--ylim'].split(',')
    ax2.set_ylim(int(ylim[0]), int(ylim[1]))

ax2.set_title('Profile lines of cube')
ax2.set_xlabel('Profile Point Index')
ax2.set_ylabel('Displacement [m]')

# use n_dots to fit with the markers on line
ax2.set_xticks(np.arange(0, num_steps, n_dots))  # x-axis ticks every n pixels
ax2.grid(which='both', color='gray', linestyle='--', linewidth=0.5)


if(arguments['--dem']):
    dem_profile = dem[rows,cols]

    ax3.plot(dem_profile, color='black', linewidth=1)
    
    ax3.set_xlim(0, len(dem_profile))

    ax3.set_title('DEM profile')
    ax3.set_ylabel('Elevation [m]')

    ax3.set_xticks(np.arange(0, num_steps, n_dots))  # x-axis ticks every n pixel
    ax3.grid(which='both', color='gray', linestyle='--', linewidth=0.5)



plt.tight_layout()
plt.show()

