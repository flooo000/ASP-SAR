Short instructions to run the geocoding commands in ASP-SAR/geocoding

1) Prepare the AMSTer ALL2GIF.sh result directory
- running for the first time = run RenamePathAfterMove.sh SAT in main directory e.g. /data/processing/Master/SAR_SM/AMPLITUDES/PAZ/Nepal_Desc_059/MATHILO
RenamePathAfterMove.sh PAZ

2) copy data you want to geocode in ALL2GIF result directory for one pair e.g. /data/processing/Master/SAR_SM/AMPLITUDES/PAZ/Nepal_Desc_059/MATHILO/20230623_20220614_MATHILO_Zoom1_ML1_DateLabel100_100/i12/InSARProducts

- IMPORTANT: files have to be renamed to REGEOC.[your file name] - only these files will be geocoded

3) run geocoding of all REGEOC. files
- change to directory of pair e.g. for example above it will be /data/processing/Master/SAR_SM/AMPLITUDES/PAZ/Nepal_Desc_059/MATHILO/20230623_20220614_MATHILO_Zoom1_ML1_DateLabel100_100
- run following command with parameter file that has been used for ALL2GIF

ReGeocode_AmpliSeries.sh /data/processing/Master/DataSAR/SAR_AUX_FILES/PARAM_FILES/PAZ/Nepal_Desc_059/LaunchMasTerParam_Single_ML1_Ampli_Ple_Crop.txt

- CAREFUL: check the Geocoding parameter before running

4) check geocoded results
- results are stored in /data/processing/Master/SAR_SM/AMPLITUDES/PAZ/Nepal_Desc_059/MATHILO/20230623_20220614_MATHILO_Zoom1_ML1_DateLabel100_100/i12/GeoProjection

----------------------------------------------------------
Geocode the cube file from invers_pixel / invers_disp2coef.py
2024-02-20: needs to be done for each cube individually, so far no multiprocessing implemented


1) prepare cube - save all images as .r4 files for AMSTer
- run prepare_geocode_cube.py --data=<path> [--dest=<path>] [--cube=<path>] [--masked]
Example for masked directory
prepare_geocode_cube.py --data=/data/processing/ASP-SAR/nepal/PAZ/Nepal_Desc_059/NSBAS_PROCESS/MASKED/H --cube=/data/processing/ASP-SAR/nepal/PAZ/Nepal_Desc_059/NSBAS_PROCESS/MASKED/H/depl_cumule --masked

-> will use the depl_cumule file to extract images, saves them in EXPORT/TO_GEOCODE, important to set --masked if masked data is used because paths differ
-> setting --dest parameter, can directly save in AMSTer directory

2) get the results from geocding 
- run get_geocode_results.py --data=<path> --dest=<path>
Example 
get_gecode_results.py --data=/data/processing/Master/SAR_SM/AMPLITUDES/PAZ/Nepal_Desc_059/MATHILO/20230623_20220614_MATHILO_Zoom1_ML1_DateLabel100_100/i12/GeoProjection --dest=/data/processing/ASP-SAR/nepal/PAZ/Nepal_Desc_059

-> will link all .bil/.hdr files to EXPORT/GEOCODED, here important to only process one cube at the time (if want to process new one - remove content of EXPORT/GEOCODED)

3) build geocoded cube based on results
build_geocoded_cube.py --data=<path> [--dest=<path>] [--masked]
Example 
build_geocoded_cube.py --data=/data/processing/ASP-SAR/nepal/PAZ/Nepal_Desc_059/EXPORT/GEOCODED --dest=/data/processing/ASP-SAR/nepal/PAZ/Nepal_Desc_059/NSBAS_PROCESS/MASKED/H --masked

-> will use the data in EXPORT/GEOCODED and save cube + .hdr and lect_...in file to destination directory, set --masked if masked data is used - for naming


=> cube can be used now, select the created lect file for plotting 
e.g. 
/data/processing/ASP-SAR/nepal/PAZ/Nepal_Desc_059/NSBAS_PROCESS/MASKED/H$ invers_disp_pixel.py --cube=depl_cumule_geocoded_masked --cols=1358 --ligns=1200 --plot_dateslim=20220601,20240101 --lectfile=lect_depl_cumule_geocoded_masked.in
