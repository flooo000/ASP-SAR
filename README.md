# ASP-SAR

Processing tool package written in bash and python for image correlation of coregistered SAR images using the AMES stereo toolbox (https://stereopipeline.readthedocs.io/en/latest/). The coregistration is done using the AMSTer toolbox(https://github.com/AMSTerUsers/AMSTer_Distribution/).\
The processing chain additionally compute the time series analysis with NSBAS .

![Alt text](logo-pnts.jpg)

# To download the package

# Installation

# How to use it
# MASTER Toolbox coregistration
1. Coregister SAR images using ALL2GIF.sh of MasTer toolbox (e.g. ALL2GIF.sh 20220723 /data/processing/Master/DataSAR/SAR_AUX_FILES/PARAM_FILES/PAZ/Nepal_Asc_033/LaunchMasTerParam_Single_ML1_Ampli_Ple.txt 100 100)
2. Prepare list pair table for correlation:
   * lns_All_Img.sh /data/processing/Master/SAR_CSL/TSX/Nepal_Desc_105/Crop_MATHILO_28.44-28.38_84.38-84.44 /data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105
   * Prepa_MSBAS.sh /data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105 300 120 20230506
3. Check ALL2GIF processing before continuing with processing: check_all2gif.py --check=YOUR_ALL2GIF_RESULTS (e.g check_all2gif.py --check=/data/processing/Master/SAR_SM/AMPLITUDES/PAZ/Nepal_Desc_059/MATHILOAll2Gif2)

# Correlations with ASP Toolbox
4. Prepare processing directory: prepare_correl_dir.py --data=YOUR_ALL2GIF_RESULTS --dest=YOUR_PROCESSING_DIR (processing directory needs to be created before) (e.g prepare_correl_dir.py --data=/data/processing/Master/SAR_SM/AMPLITUDES/TSX/Nepal_Desc_105/MATHILO --dest=/data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105)
5. Convert images to GeoTiff format (1 single band, REAL4): convert_geotiff.py --data=YOUR_PROCESSING_DIR (e.g convert_geotiff.py --data=/data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105)
6. Adjust the correlation parameters in YOUR_PROCESSING_DIR/asp_parameters.txt (example in /contrib) and start processing: process_stereo.py --data=YOUR_PROCESSING_DIR --pairs=PAIR_LIST (the pair list is created with prepa_MSBAS.sh of MasTer toolbox. It needs to be in the same format/naming). 

# Export file 
8. Prepare the results for download/analysis in QGIS: prepare_result_export.py --data=WORKING_DIR (e.g prepare_result_export.py --data=/data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105)

# Export for NSBAS time series analysis
9. Prepare files and directory structure for NSBAS processing: prepare_nsbas_process.py --data=WORKING_DIR (e.g prepare_nsbas_process.py --data=/data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105/)

# Masking data set based on CC and process masked results
After step 8. Export file
1. Mask the results in EXPORT directory: mask_result_export_cc.py --data=EXPORT_DIR (e.g. mask_correl_results_cc.py --data=/data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105_crop/EXPORT)
2. Re-run prepare_result_export.py with extra --masked option: prepare_result_export.py --data=WORKING_DIR --masked (e.g. prepare_result_export.py --data=/data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105_crop --masked)
3. Run prepare_nsbas_process.py with --masked to use the masked data for the inversion input files: prepare_nsbas_process.py --data=WORKING_DIR --masked (e.g. prepare_nsbas_process.py --data=/data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105_crop --masked)
4. Run inversion in WORKING_DIR/NSBAS_PROCESS/MASKED/H|V

# Geocoding of cube file or single NSBAS results
After performing NSBAS processing (invers_pixel and/or invers_disp2coef.py). The processing steps assume that the masked data is used. If this is not the case, remove the --masked flags at the corresponding command
1. Prepare AMSTer ALL2GIF result directory and run RenamePathAfterMove.sh (ONLY IF GEOCODING IS DONE FOR THE FIRST TIME IN THIS DIRECTORY): RenamePathAfterMove.sh SAT (e.g. cd /data/processing/Master/SAR_SM/AMPLITUDES/PAZ/Nepal_Desc_059/MATHILO -> RenamePathAfterMove.sh PAZ)
2. copy data you want to geocode in ALL2GIF result directory for one pair (e.g. /data/processing/Master/SAR_SM/AMPLITUDES/PAZ/Nepal_Desc_059/MATHILO/20230623_20220614_MATHILO_Zoom1_ML1_DateLabel100_100/i12/InSARProducts)
   - single file: rename the file to REGEOC.[filename] and copy it in the given directory
   - cube file:prepare export of cube by running prepare_geocode_cube.py --data=<path> [--dest=<path>] [--cube=<path>] [--masked] (e.g. prepare_geocode_cube.py --data=/data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105_crop/NSBAS_PROCESS/MASKED/H --cube=/data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105_crop/NSBAS_PROCESS/MASKED/H/depl_cumule --dest=/data/processing/Master/SAR_SM/AMPLITUDES/TSX/Nepal_Desc_105/MATHILO/20230301_20221225_MATHILO_Zoom1_ML1_DateLabel100_100/i12/InSARProducts --masked)
3. run geocoding using AMSTer function ReGeocode_AmpliSeries.sh PARAM_FILE(that was used for ALL2GIF processing) (e.g cd /data/processing/Master/SAR_SM/AMPLITUDES/TSX/Nepal_Desc_105/MATHILO/20230301_20221225_MATHILO_Zoom1_ML1_DateLabel100_100 -> ReGeocode_AmpliSeries.sh /data/processing/Master/DataSAR/SAR_AUX_FILES/PARAM_FILES/TSX/Nepal_Desc_105/LaunchMasTerParam_ML1_Ampli_ple_crop.txt)
4. copy geocoded products to wanted directory. for cube file use: get_geocode_results.py --data=<path> --dest=<path> --name=<value> (e.g. get_geocode_results.py --data=/data/processing/Master/SAR_SM/AMPLITUDES/TSX/Nepal_Desc_105/MATHILO/20230301_20221225_MATHILO_Zoom1_ML1_DateLabel100_100/i12/GeoProjection --dest=/data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105_crop --name=range_depl_cumule_masked)
5. build the geocoded cube file based on results build_geocoded_cube.py --data=<path> [--dest=<path>] [--masked] (e.g build_geocoded_cube.py --data=/data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105_crop/EXPORT/GEOCODED/range_depl_cumule_masked --dest=/data/processing/ASP-SAR/nepal/TSX/Nepal_Desc_105_crop/NSBAS_PROCESS/MASKED/H --masked)
