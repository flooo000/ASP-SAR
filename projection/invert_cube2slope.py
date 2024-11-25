#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
invert_cube2slope.py
--------------
Project each map of LOS cube in line of steepest slope and saves it in cube. Possible to crop the result to a given extent

Usage:
    invert_cube2slope.py --range_cube=<path> --azimuth_cube=<path> --inc=<path> --aspect=<path> --heading=<value> --dest=<path> --ext=<value> [--crop=<value>]
    invert_cube2slope.py --test
    invert_cube2slope.py -h | --help

Options:
-h | --help             Show this screen
--range_cube            Path to geocoded slant range cube
--azimuth_cube          Path to geocoded azimuth cube
--inc                   Path to geocoded incidence map
--aspect                Path to aspect map (or optical displacement angles) referenced from the North, positive clockwise
--heading               Value of heading angle
--dest                  Path to destination 
--ext                   Naming extension of output file 
--crop                  Crop dimensions ymin,ymax,xmin,xmax
--test                  Run synthetic test

"""

##########
# IMPORT #
##########

import os, sys
import numpy as np
from numpy.lib.stride_tricks import as_strided
from osgeo import gdal
import pandas as pd
from pathlib import Path
import shutil
from dateutil import parser
import docopt
from matplotlib import pyplot as plt

#############
# FUNCTIONS #
#############

## TEST FUNCTIONS ##

def run_synt_test(u_rg_map, u_az_map, phi, heading_rad, theta, omega):

    print('RUN SYNTHETIC TEST')

    print('Azimuth displacements')
    print(u_az_map)

    print('Slant Range displacements')
    print(u_rg_map)

    invert_results = invert_single_map(u_rg_map, u_az_map, phi, heading_rad, theta, omega)
    u_slope_map, u_z_map = invert_results
    print('Inverted u_slope parameter')
    print(u_slope_map)
    print('Inverted u_z parameter')
    print(u_z_map)

    u_rg_inv = np.zeros((u_slope_map.shape[0], u_slope_map.shape[1]))
    u_az_inv = np.zeros((u_slope_map.shape[0], u_slope_map.shape[1]))

    for i in range(u_slope_map.shape[0]):
        for j in range(u_slope_map.shape[1]):
            d = np.array([u_slope_map[i][j], u_z_map[i][j]])
            G = construct_G(i, j, phi, heading_rad, theta, omega)

            # m = [u_az, u_rg]
            m = G.dot(d)

            u_az_inv[i][j] = m[0]
            u_rg_inv[i][j] = m[1]

    print('Azimuth displacements from inversion results')
    print(u_az_inv)
    print('Slant Range displacements from inversion results')
    print(u_rg_inv)

def plot_aspect_sensitivity(aspect_360, heading_rad, incidence, omega_360):
    
    print('PLOT ASPECT SENSITIVITY')
    
    u_slope_1 = np.full(aspect_360.shape, 1)
    #print(u_slope_1)
    u_z_0 = np.full(aspect_360.shape, 0)
    #print(u_z_0)

    theta_360 = np.full(aspect_360.shape, np.radians(90 - incidence))

    u_rg_inv = np.zeros((u_slope_1.shape[0], u_slope_1.shape[1]))
    u_az_inv = np.zeros((u_slope_1.shape[0], u_slope_1.shape[1]))

    print(u_slope_1.shape)
    for i in range(u_slope_1.shape[0]):
        for j in range(u_slope_1.shape[1]):
            d = np.array([u_slope_1[i][j], u_z_0[i][j]])
            G = construct_G(i, j, phi, heading_rad, theta_360, omega_360)

            # m = [u_az, u_rg]
            m = G.dot(d)

            u_az_inv[i][j] = m[0]
            u_rg_inv[i][j] = m[1]

    # run test with different input - set u_rg and u_az 
    u_rg_10 = np.full(aspect_360.shape, 2)
    u_az_10 = np.full(aspect_360.shape, 2)

    invert_results_360_10 = invert_single_map(u_rg_10, u_az_10, phi, heading_rad, theta_360, omega_360)
    u_slope_10, u_z_10 = invert_results_360_10

    # add random noise to the obtained u_rg and u_az before calculating the u_slope and u_z
    invert_results_360 = invert_single_map(u_rg_inv + np.random.uniform(-0.2, 0.2, u_rg_inv.shape), u_az_inv + np.random.uniform(-0.2, 0.2, u_az_inv.shape), phi, heading_rad, theta_360, omega_360)
    u_slope_360, u_z_360 = invert_results_360

    fig, (ax_cartesian, ax_polar) = plt.subplots(1, 2, figsize=(12, 6))

    #ax_cartesian.plot(aspect_360, np.where(u_az_inv > 200, np.nan, u_az_inv), label='u_azimuth', color='b')
    #ax_cartesian.plot(aspect_360, np.where(u_rg_inv > 200, np.nan, u_rg_inv), label='u_range', color='r')

    ax_cartesian.plot(aspect_360, np.where(np.abs(u_slope_360) > 200, np.nan, u_slope_360), label='u_slope', color='b')
    ax_cartesian.plot(aspect_360, np.where(np.abs(u_z_360) > 200, np.nan, u_z_360), label='u_z', color='r')

    ax_cartesian.plot(aspect_360, np.where(np.abs(u_slope_10) > 50, np.nan, u_slope_10), label='u_slope_10', color='orange')
    ax_cartesian.plot(aspect_360, np.where(np.abs(u_z_10) > 50, np.nan, u_z_10), label='u_z_10', color='green')

    # plot Heading, LOS, -LOS in cartesian plot
    #ax_cartesian.axvline(np.degrees((1/2)*np.pi-heading_rad), color='black', label='heading')
    ax_cartesian.axvline(np.degrees(np.pi-heading_rad), color='orange', label='LOS')
    ax_cartesian.axvline(np.degrees(2*np.pi-heading_rad), color='orange', label='-LOS', linestyle='--')

    los_center = np.degrees(np.pi - heading_rad)
    los_neg_center = np.degrees(2 * np.pi - heading_rad)
    box_width = 10  # Box width in degrees

# Add shaded boxes around LOS and -LOS
    ax_cartesian.axvspan(los_center - box_width, los_center + box_width, color='grey', alpha=0.3, label='LOS ±10°')
    ax_cartesian.axvspan(los_neg_center - box_width, los_neg_center + box_width, color='grey', alpha=0.3, label='-LOS ±10°')


    ax_cartesian.set_xlabel('Aspect [°]')
    ax_cartesian.set_ylabel('Parameter')

    ax_cartesian.set_xlim(0, 360)

    ax_polar = fig.add_subplot(122, polar=True)
    #ax_polar.plot(np.radians(aspect_360), u_az_inv, label='u_azimuth', color='b')
    #ax_polar.plot(np.radians(aspect_360), u_rg_inv, label='u_range', color='r')
    #ax_polar.plot(np.radians(aspect_360), np.zeros(aspect_360.shape), color='grey')

    ax_polar.plot(np.radians(aspect_360), u_slope_360, label='u_slope', color='b')
    ax_polar.plot(np.radians(aspect_360), u_z_360, label='u_z', color='r')

    r_values = [-10, 10]
    ax_polar.set_ylim(r_values)
    
    ax_polar.set_theta_zero_location('N')
    ax_polar.set_theta_direction(-1)

    # set size of line for LOS and Heading
    #r_values = [-2, 2]

    ax_polar.plot([np.pi-heading_rad, np.pi-heading_rad], r_values, color='orange', label='LOS')
    ax_polar.plot([2*np.pi-heading_rad, 2*np.pi-heading_rad], r_values, color='orange', label='-LOS', linestyle='--')

    ax_polar.plot([(1/2)*np.pi-heading_rad, (1/2)*np.pi-heading_rad], r_values, color='black', label='Heading')
    #ax_polar.plot([rad_angle2, rad_angle2], r_values, color='orange', label='Line at 150°', linestyle='--')


    ax_cartesian.legend()
    ax_polar.legend()

    plt.tight_layout()
    plt.show()

def plot_aspect_theta(aspect_360, theta_90, omega_360, incidence):

    print('PLOT ASPECT + THETA INVERSION')

    u_slope_360_90 = np.full((aspect_360.shape[0], alpha_90.shape[0]), 1)
    u_z_360_90 = np.full((aspect_360.shape[0], alpha_90.shape[0]), 0)

    u_rg_inv = np.zeros(u_slope_360_90.shape)
    u_az_inv = np.zeros(u_slope_360_90.shape)

    theta_360_90 = np.tile(theta_90, (360, 90))
    plt.imshow(theta_360_90)
    plt.show()
    omega_360_90 = np.tile(omega_360, (1, 90))

    for i in range(aspect_360.shape[0]):
        for j in range(theta_90.shape[0]):
            d = np.array([u_slope_360_90[i][j], u_z_360_90[i][j]])
            G = construct_G(i, j, phi, heading_rad, theta_360_90, omega_360_90)
            m = G.dot(d)

            u_az_inv[i][j] = m[0]
            u_rg_inv[i][j] = m[1]

    fig, axes = plt.subplots(2, 1, figsize=(8, 10))

# Plot the azimuth map
    img1 = axes[0].imshow(u_az_inv.T, cmap='Spectral', aspect='auto')
    #img1 = axes[0].imshow(u_az_inv, cmap='nipy_spectral', extent=[aspect_360.min(), aspect_360.max(), np.degrees(alpha_90).min(), np.degrees(alpha_90).max()], aspect='auto')
    axes[0].set_title('u_az')
    axes[0].set_xlabel('Aspect (degrees)')
    axes[0].set_ylabel('Slope (degrees)')
    fig.colorbar(img1, ax=axes[0], orientation='vertical')

    img2 = axes[1].imshow(u_rg_inv.T, cmap='Spectral', aspect='auto')
    axes[1].set_title('u_range')
    axes[1].set_xlabel('Aspect (degrees)')
    axes[1].set_ylabel('Slope (degrees)')
    fig.colorbar(img2, ax=axes[1], orientation='vertical')

    plt.tight_layout(pad=3.0)
    plt.show()


def plot_aspect_slope(aspect_360, alpha_90, omega_360, incidence):
    
    print('PLOT ASPECT + SLOPE INVERSION')

    slope_para_map = np.zeros((aspect_360.shape[0], alpha_90.shape[0]))
    u_slope_360_90 = np.full(slope_para_map.shape, 1)
    u_z_360_90 = np.zeros((aspect_360.shape[0], alpha_90.shape[0]))

    # prepare slope_para_map
    for i in range(aspect_360.shape[0]):
        for j in range(alpha_90.shape[0]):
            slope_para_map[i][j] = u_slope_360_90[i][j] * np.cos(alpha_90[j])

    theta_360_90 = np.full(slope_para_map.shape, np.radians(90 - incidence))

    u_rg_inv = np.zeros((slope_para_map.shape[0], slope_para_map.shape[1]))
    u_az_inv = np.zeros((slope_para_map.shape[0], slope_para_map.shape[1]))

    omega_360_90 = np.tile(omega_360, (1, 90))

    for i in range(slope_para_map.shape[0]):
        for j in range(slope_para_map.shape[1]):
            d = np.array([slope_para_map[i][j], u_z_360_90[i][j]])
            G = construct_G(i, j, phi, heading_rad, theta_360_90, omega_360_90)

            # m = [u_az, u_rg]
            m = G.dot(d)

            u_az_inv[i][j] = m[0]
            u_rg_inv[i][j] = m[1]

    fig, axes = plt.subplots(2, 1, figsize=(8, 10))

# Plot the azimuth map
    img1 = axes[0].imshow(u_az_inv.T, cmap='Spectral', aspect='auto')
    #img1 = axes[0].imshow(u_az_inv, cmap='nipy_spectral', extent=[aspect_360.min(), aspect_360.max(), np.degrees(alpha_90).min(), np.degrees(alpha_90).max()], aspect='auto')
    axes[0].set_title('u_az')
    axes[0].set_xlabel('Aspect (degrees)')
    axes[0].set_ylabel('Slope (degrees)')
    fig.colorbar(img1, ax=axes[0], orientation='vertical')  

    img2 = axes[1].imshow(u_rg_inv.T, cmap='Spectral', aspect='auto')
    axes[1].set_title('u_range')
    axes[1].set_xlabel('Aspect (degrees)')
    axes[1].set_ylabel('Slope (degrees)')
    fig.colorbar(img2, ax=axes[1], orientation='vertical')

    plt.tight_layout(pad=3.0)
    plt.show()

## MAIN FUNCTIONS ##

def get_cube_dimension(cube_file):
    ds = gdal.Open(cube_file)
    ncols, nlines = ds.RasterXSize, ds.RasterYSize
    n_img = ds.RasterCount

    img_data = (nlines, ncols, n_img)

    return img_data

def read_tif(input_file, crop):

    ds = gdal.OpenEx(input_file, allowed_drivers=['GTiff'])
    ds_band = ds.GetRasterBand(1)
    values = ds_band.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize)
    
    if(crop):
        return values[crop[0]:crop[1], crop[2]:crop[3]]
    else:
        return values

def read_file(input_file, nlines, ncols, crop):
    # read file and return content as output array
    
    print('Read {}'.format(os.path.basename(input_file)))

    m = np.fromfile(input_file, dtype=np.float32)
    map_i = m[:nlines*ncols].reshape((nlines,ncols))

    if(crop):
        return map_i[crop[0]:crop[1], crop[2]:crop[3]]
    else:
        return map_i

def read_cube(cube_file, ncol, nlines, n_img, crop):
    
    print('Start reading cube file')

    cubei = np.fromfile(cube_file,dtype=np.float32)
    cube = as_strided(cubei[:nlines*ncol*n_img])

    kk = np.flatnonzero(np.logical_or(cube==9990, cube==9999))
    cube[kk] = float('NaN')
    maps_temp = as_strided(cube.reshape((nlines,ncol,n_img)))
    maps = np.copy(maps_temp)

    print('Finished reading cube file')

    if(crop):
        return maps[crop[0]:crop[1], crop[2]:crop[3],:]
    else:
        return maps

def save_cube(dest_path, out_filename, maps):
    print('Writing cube')

    fid = open(os.path.join(dest_path, out_filename), 'wb')
    maps[:,:,:].flatten().astype('float32').tofile(fid)
    fid.close()

def save_cube_metadata(dest_path, out_filename, img_data):
    nrow, ncol, nimg = img_data[0], img_data[1], img_data[2]

    # be careful here with ncol, nrow (normal: lines=nrow; samples=ncol)
    with open(os.path.join(dest_path, '{}.hdr'.format(out_filename)), 'w') as hdr_file:
        hdr_file.write("ENVI\n")
        hdr_file.write("samples = {}\n".format(ncol))
        hdr_file.write("lines = {}\n".format(nrow))
        hdr_file.write("bands = {}\n".format(nimg))
        hdr_file.write("header offset = 0\n")
        hdr_file.write("file type = ENVI Standard\n")
        hdr_file.write("data type = 4\n")  # 4 represents float32, adjust if needed
        hdr_file.write("interleave = bip") # add this to display in QGIS and Insar-viz
   
    # save also .in file to plot pixel
    with open(os.path.join(dest_path, 'lect_{}.in'.format(out_filename)), 'w') as lect_file:
        lect_file.write('\t{}\t{}\t{}'.format(ncol, nrow, nimg))

def construct_G(i, j, phi, heading_rad, theta, omega):
    
    PROJ = np.array([
        [np.cos(heading_rad),    np.sin(heading_rad),       0],
        [np.cos(phi)*np.cos(theta[i][j]), np.sin(phi)*np.cos(theta[i][j]), np.sin(theta[i][j])]
        ])

    R_aspect = np.array([
        [ np.cos(omega[i][j]),  np.sin(omega[i][j]), 0],
        [-np.sin(omega[i][j]),  np.cos(omega[i][j]), 0],
        [ 0,              0,             1]
    ])
    
    G_full = np.dot(PROJ, R_aspect)
    
    G = np.array([
        [G_full[0, 0], G_full[0, 2]],  
        [G_full[1, 0], G_full[1, 2]]
        ])
    
    return G

def invert_single_map(range_map, azimuth_map, phi, heading_rad, theta, omega):
    
    # print(range_map.shape)
    uslope = np.zeros((range_map.shape[0], range_map.shape[1]))
    uz = np.zeros((range_map.shape[0], range_map.shape[1]))

    for i in range(range_map.shape[0]):
        if (i + 1) % 100 == 0:
            print('Process line {} from {}'.format(i, range_map.shape[0]))
        for j in range(range_map.shape[1]):
            
            d = np.array([azimuth_map[i][j], range_map[i][j]])
            G = construct_G(i, j, phi, heading_rad, theta, omega)

            m = np.linalg.inv(G).dot(d)

            uslope[i][j] = m[0]
            uz[i][j] = m[1]

    return (uslope, uz)

########
# MAIN #
########

arguments = docopt.docopt(__doc__)

### SYNTHETIC TEST

if(arguments['--test']):
    
    u_az_map = np.array([
        [5, 7, 2, 9, 7],
        [3, 4, 7, 9, 7]
        ])
    u_rg_map = np.array([
        [-3, -8, -6, -7, -5],
        [-5, -8, -5, -6, -3]
        ])

    # PAZ Desc
    #heading = 260
    # PAZ ASC
    heading = 100

    heading_rad = np.radians(heading)
    phi = np.radians(-360 + float(heading) + 90)
    
    # PAZ Desc
    #incidence = 42
    # PAZ ASC
    incidence = 32

    theta = np.full(u_az_map.shape, np.radians(90 - incidence))
    theta_90 = np.radians(np.arange(90).reshape(90, 1))

    aspect = 200
    conv_aspect = np.mod(aspect - 90, 360)
    omega = np.full(u_az_map.shape, np.radians(conv_aspect))

    # SYNTHETIC TEST WITH SMALL INPUT MAP
    #run_synt_test(u_rg_map, u_az_map, phi, heading_rad, theta, omega)

    aspect_360 = np.arange(360).reshape(360, 1)
    conv_aspect_360 = np.mod(aspect_360 - 90, 360)
    omega_360 = np.radians(conv_aspect_360)

    # slope angle
    alpha_90 = np.radians(np.arange(90).reshape(90, 1))
    
    # PLOT ASPECT - u_range, u_azimuth
    plot_aspect_sensitivity(aspect_360, heading_rad, incidence, omega_360)
   
    # PLOT ASPECT + SLOPE 
    # instead of only u_slope - calculate u_para = u_slope * cos(alpha)
    #plot_aspect_slope(aspect_360, alpha_90, omega_360, incidence)

    #plot_aspect_theta(aspect_360, theta_90, omega_360, incidence)

    exit()

### 0: Set input data

##  Get input parameter
range_cube_file = arguments['--range_cube']
azimuth_cube_file = arguments['--azimuth_cube']
incidence_file = arguments['--inc']
aspect_file = arguments['--aspect']
# maybe change later to read AMSTer txt and extract heading
heading = arguments['--heading']
dest_path = arguments['--dest']
ext = arguments['--ext']

## Read and prepare all input data

# get cube dimensions from one of the cubes 
# full extent to initially read the cube, keep this if no crop option
img_data = get_cube_dimension(range_cube_file)
nlines, ncols, n_img = img_data[0], img_data[1], img_data[2]

# set crop parameters if crop is input
if(arguments['--crop']):
    # (xmin, xmax, ymin, ymax)
    crop = tuple(map(int, arguments['--crop'].split(',')))
    
    nlines_crop = crop[1] - crop[0]
    ncols_crop = crop[3] - crop[2]

    print('Crop option is set. New cube dimensions are ({},{},{})'.format(nlines_crop, ncols_crop, n_img))
else:
    crop = None
    print('No crop option is set. Process the full extent of cube')

range_maps = read_cube(range_cube_file, ncols, nlines, n_img, crop)
azimuth_maps = read_cube(azimuth_cube_file, ncols, nlines, n_img, crop)

# read other files
aspect = read_tif(aspect_file, crop)

plt.imshow(aspect)
plt.show()

incidence = read_file(incidence_file, nlines, ncols, crop)

# define angles for projection and convert in radians

phi = np.radians(-360 + float(heading) + 90)
print('Phi = {} rad ({} Grad)'.format(phi, -360 + float(heading) + 90))

heading_rad = np.radians(float(heading))
print('H = {} rad ({} Grad)'.format(heading_rad, heading))

theta = np.radians(90 - incidence)
# print test pixel for reference, get the pixel in the middle
test_x, test_y = int(aspect.shape[0]/2), int(aspect.shape[1]/2)
print(aspect.shape, test_x, test_y)
print('Theta = {} rad ({} Grad) of pixel {},{}'.format(theta[test_x][test_y], 90 - incidence[test_x][test_y], test_x, test_y))

conv_aspect = np.mod(aspect - 90, 360)
omega = np.radians(conv_aspect)
print('Omega = {} rad ({} Grad) of pixel {},{}'.format(omega[test_x][1], conv_aspect[test_x][test_y], test_x, test_y))

# construct G matrix

# need to generate G for each pixel individually

#G = construct_G(i, j, phi, heading_rad, theta, omega)
print('G for pixel {},{}'.format(test_x, test_y))
G = construct_G(test_x, test_y, phi, heading_rad, theta, omega)
print(G)


## 1: Apply inversion to all images of cube

# get the final size of cube to avoid a lot of conditions
nlines_final = nlines_crop if crop else nlines
ncols_final = ncols_crop if crop else ncols
print(nlines_final, ncols_final)
img_data_final = (nlines_final, ncols_final, n_img)

uslope_cube = np.zeros((nlines_final, ncols_final, n_img))
uz_cube = np.zeros((nlines_final, ncols_final, n_img))

for l in range(n_img):
    print('Start inverting map {}/{}'.format(l, n_img-1))
    range_map = range_maps[:,:,l].reshape((nlines_final,ncols_final))
    azimuth_map = azimuth_maps[:,:,l].reshape((nlines_final,ncols_final))

    # return the map of uslope and uz als tuple
    invert_results = invert_single_map(range_map, azimuth_map, phi, heading_rad, theta, omega)
    
    uslope_map, uz_map = invert_results[0], invert_results[1]

    uslope_cube[:,:,l] = uslope_map
    uz_cube[:,:,l] = uz_map

## 2: Save the inverted cubes as file

# save projected maps to cube + hdr file
# for slope direction (u_slope) and vertical (u_z)

if(crop):
    uslope_filename = 'depl_cumule_uslope_{}_crop_{}_{}_{}_{}'.format(ext, crop[0], crop[1], crop[2], crop[3])
    uz_filename = 'depl_cumule_uz_{}_crop_{}_{}_{}_{}'.format(ext, crop[0], crop[1], crop[2], crop[3])
else:
    uslope_filename = 'depl_cumule_uslope_{}'.format(ext)
    uz_filename = 'depl_cumule_uz_{}'.format(ext)

save_cube(dest_path, uslope_filename, uslope_cube)
save_cube_metadata(dest_path, uslope_filename, img_data_final)

save_cube(dest_path, uz_filename, uz_cube)
save_cube_metadata(dest_path, uz_filename, img_data_final)

