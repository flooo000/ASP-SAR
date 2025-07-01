#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
compute_vert_displ.py
--------------
Compute the vertical displacements given horizontal displacements and vertical difference.

Usage: compute_vert_displ.py --we=<path> --sn=<path> --vert=<path> --dsm=<path> --dest=<path> --name=<value> [--filter_size=<value>] [--angle_threshold=<value>]
compute_vert_displ.py -h | --help

Options:
-h | --help             Show this screen
--we                    Path to WE-displacement map (positive towards east)
--sn                    Path to SN-displacement map (positive towards north)
--vert                  Path to vertical difference map
--dsm                   Path to DSM map
--dest                  Path to destination directory
--name                  Name of output file
--filter_size           Filter window size in meter for the DSM [default: 10]
--angle_threshold       Threshold angle to mask where the horizontal displacement vector deviates by more than this angle from the downslope direction [default: 30]
"""

##########
# IMPORT #
##########

import numpy as np
from numpy.lib.stride_tricks import as_strided
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import os
from osgeo import gdal
import docopt

#############
# FUNCTIONS #
#############

def read_tif(input_file):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File {input_file} not found")
    ds = gdal.OpenEx(input_file, allowed_drivers=['GTiff'])
    ds_band = ds.GetRasterBand(1)
    values = ds_band.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize)
    ncols, nlines = ds.RasterYSize, ds.RasterXSize
    proj = ds.GetProjection()
    geotransform = ds.GetGeoTransform()
    return (values, nlines, ncols, proj, geotransform)

def save_to_file(data, output_path, ncol, nrow, proj, geotransform):
    drv = gdal.GetDriverByName('GTiff')
    dst_ds = drv.Create(output_path, ncol, nrow, 1, gdal.GDT_Float32)
    dst_band = dst_ds.GetRasterBand(1)
    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(proj)
    dst_band.WriteArray(data)
    dst_ds.FlushCache()

########
# MAIN #
########

arguments = docopt.docopt(__doc__)

we_displ_file = arguments['--we']
ns_displ_file = arguments['--sn']
dsm_diff_file = arguments['--vert']
dsm_file = arguments['--dsm']
dest_path = arguments['--dest']
name = arguments['--name']

# Default values for optional arguments
filter_size = float(arguments['--filter_size']) if arguments['--filter_size'] else 10.0
angle_threshold = float(arguments['--angle_threshold']) if arguments['--angle_threshold'] else 30.0

# Read data
we_displ = read_tif(we_displ_file)[0]  # positive towards east
ns_displ = -read_tif(ns_displ_file)[0] # positive towards south 
dsm_diff = read_tif(dsm_diff_file)[0] # convention: negative when erosion
dsm, dsm_cols, dsm_lines, dsm_proj, dsm_geotransf = read_tif(dsm_file)

if not (we_displ.shape == ns_displ.shape == dsm_diff.shape == dsm.shape):
    raise ValueError("Dimensions between files do not match")

# Filter DSM before computing gradient
filter_sigma_x = filter_size / abs(dsm_geotransf[1])
filter_sigma_y = filter_size / abs(dsm_geotransf[5])
dsm_filtered = gaussian_filter(dsm, sigma=(filter_sigma_y, filter_sigma_x))

# Compute gradients n = (dx,dy)
dsm_dy, dsm_dx = np.gradient(dsm_filtered, dsm_geotransf[5], dsm_geotransf[1]) # dy is positive towards south, while dx is positive towards east

# Compute downslope unit vector (horizontal component of slope vector)
norm_ns = np.sqrt(dsm_dx**2 + dsm_dy**2)
ns_x = dsm_dx / norm_ns
ns_y = dsm_dy / norm_ns

# Compute horizontal displacement magnitude
u_H = np.sqrt(we_displ**2 + ns_displ**2)

# Project u_H onto downslope direction
u_proj = we_displ * ns_x + ns_displ * ns_y  # scalar projection 

# Compute slope magnitude
slope = np.sqrt(dsm_dx**2 + dsm_dy**2)  # tan(slope_angle)

# Compute vertical displacement
vert_displ = dsm_diff - slope * u_proj

# Mask all the pixels for which the horizontal displacements vector is orientated at more than for example 30° from the down-slope direction.
aspect = (np.rad2deg(np.arctan2(dsm_dy, -dsm_dx)) + 360 ) % 360   # clock-wise slope direction from 0 to 360 
omega = (np.rad2deg(np.arctan2(ns_displ,we_displ)) + 360) % 360 # clock-wise downslope direction 
mask = np.nonzero(abs(omega - aspect)  >= angle_threshold)  # Mask where angle <= threshold
masked_vert_displ = np.copy(vert_displ)
masked_vert_displ[mask] = np.nan

# Save result to file
output_path = os.path.join(dest_path, f'uz_optical_{name}.tif')
save_to_file(masked_vert_displ, output_path, dsm_cols, dsm_lines, dsm_proj, dsm_geotransf)
output_path = os.path.join(dest_path, f'omega.tif')
save_to_file(omega, output_path, dsm_cols, dsm_lines, dsm_proj, dsm_geotransf)
output_path = os.path.join(dest_path, f'aspect.tif')
save_to_file(aspect, output_path, dsm_cols, dsm_lines, dsm_proj, dsm_geotransf)

# Zoom sur la zone d'intérêt
crop_slice = (slice(450, 950), slice(500, 1000))
dsm_diff_crop = dsm_diff[crop_slice]
u_H_crop = u_H[crop_slice]
vert_displ_crop = vert_displ[crop_slice]
masked_vert_displ_crop = masked_vert_displ[crop_slice]
dsm_crop = dsm[crop_slice]
omega_crop = omega[crop_slice]
aspect_crop =  aspect[crop_slice]

print('Average downslope direction:', np.nanmean(omega_crop))
print('Average aspect:', np.nanmean(aspect_crop))

# Création de la figure
fig = plt.figure(figsize=(12, 14))
vmax = 10 # harcoding

# DSM difference
ax = fig.add_subplot(2, 3, 1)
#ax.imshow(aspect_crop, cmap='Greys_r')
cax = ax.imshow(dsm_diff_crop, cmap='coolwarm', origin='upper', vmax=vmax, vmin=-vmax, alpha=0.5)
ax.set_title("DSM Differences (dz)")
ax.set_xticks([])
ax.set_yticks([])
divider = make_axes_locatable(ax)
c = divider.append_axes("right", size="5%", pad=0.05)
plt.colorbar(cax, cax=c)

# Horizontal displacement magnitude
ax = fig.add_subplot(2, 3, 2)
#ax.imshow(aspect_crop, cmap='Greys_r')
cax = ax.imshow(u_H_crop, cmap='coolwarm', origin='upper',  
                vmax=np.nanpercentile(u_H_crop, 95), vmin=np.nanpercentile(u_H_crop, 5), alpha=0.5)
ax.set_title("Horizontal Displacement Magnitude")
ax.set_xticks([])
ax.set_yticks([])
divider = make_axes_locatable(ax)
c = divider.append_axes("right", size="5%", pad=0.05)
plt.colorbar(cax, cax=c)

# Vertical displacement
ax = fig.add_subplot(2, 3, 3)
#ax.imshow(aspect_crop, cmap='Greys_r')
cax = ax.imshow(vert_displ_crop, cmap='coolwarm', origin='upper', vmax=vmax, vmin=-vmax, alpha=0.5)
ax.set_title("Vertical Displacements (u_z)")
ax.set_xticks([])
ax.set_yticks([])
divider = make_axes_locatable(ax)
c = divider.append_axes("right", size="5%", pad=0.05)
plt.colorbar(cax, cax=c)

# Downslope direction (omega)
ax = fig.add_subplot(2, 3, 4)
cax = ax.imshow(omega_crop, cmap='Greys_r', origin='upper', alpha=0.5, vmax=360, vmin=0)
ax.set_title("Velocity Direction (clockwise from east)")
ax.set_xticks([])
ax.set_yticks([])
divider = make_axes_locatable(ax)
c = divider.append_axes("right", size="5%", pad=0.05)
plt.colorbar(cax, cax=c)

# Slope direction (omega)
ax = fig.add_subplot(2, 3, 5)
ax.imshow(aspect_crop, cmap='Greys_r', origin='upper', alpha=0.5, vmax=360, vmin=0)
ax.set_title("Slope Direction (clockwise from east)")
ax.set_xticks([])
ax.set_yticks([])
divider = make_axes_locatable(ax)
c = divider.append_axes("right", size="5%", pad=0.05)
plt.colorbar(cax, cax=c)

# Masked vertical displacement
ax = fig.add_subplot(2, 3, 6)
ax.imshow(dsm_crop, cmap='Greys_r')
cax = ax.imshow(masked_vert_displ_crop, cmap='coolwarm', origin='upper', vmax=vmax, vmin=-vmax, alpha=0.5)
ax.set_title("Masked Vertical Displacements")
ax.set_xticks([])
ax.set_yticks([])
divider = make_axes_locatable(ax)
c = divider.append_axes("right", size="5%", pad=0.05)
plt.colorbar(cax, cax=c)

plt.tight_layout()
plt.show()

