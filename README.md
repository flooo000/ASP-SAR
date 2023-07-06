# ASP-SAR

Processing tool package written in bash and python for image correlation of coregistered SAR images using the AMES stereo toolbox (https://stereopipeline.readthedocs.io/en/latest/). The coregistration is done using the MasTer toolbox().\
The processing chain additionally compute the time series analysis with NSBAS .

# To download the package

# Installation

# How to use it
1. Coregister SAR images using ALL2GIF.sh of MasTer toolbox (e.g. ALL2GIF.sh 20220723 /data/processing/Master/DataSAR/SAR_AUX_FILES/PARAM_FILES/PAZ/Nepal_Asc_033/LaunchMasTerParam_Single_ML1_Ampli_Ple.txt 100 100)
2. Prepare processing directory: prepare_correl_dir.py --data=YOUR_ALL2GIF_RESULTS --dest=YOUR_PROCESSING_DIR (processing directory needs to be created before) (e.g prepare_correl_dir.py --data=/data/processing/Master/SAR_SM/AMPLITUDES/PAZ/Nepal_Desc_059/MATHILOAll2Gif2 --dest=/data/scratch/florian/correl/PAZ/Nepal_Desc_059/MATHILOAll2Gif2)
3. Convert images to GeoTiff format (1 single band, REAL4): convert_geotiff.py --data=YOUR_PROCESSING_DIR (e.g convert_geotiff.py --data=/data/scratch/florian/correl/PAZ/Nepal_Desc_059/MATHILOAll2Gif2)
4. Adjust the correlation parameters in YOUR_PROCESSING_DIR/CORREL/asp_parameters.txt and start processing: process_stereo.py --data=YOUR_PROCESSING_DIR --pairs=PAIR_LIST (the pair list is created with prepa_MSBAS.sh of MasTer toolbox. It needs to be in the same format/naming). For each iteration, a new directory with the current timestamp is created as YOUR_PROCESSING_DIR/CORREL/TIMESTAMP (This will be referred as WORKING_DIR) (e.g process_stereo.py --data=/data/scratch/florian/correl/PAZ/Nepal_Desc_059/MATHILOAll2Gif2 --pairs=/data/processing/Master/SAR_SM/MSBAS/MATHILLO/set3/table_0_400_0_400.txt)
5. Prepare the results for download/analysis in QGIS: prepare_result_export.py --data=WORKING_DIR (e.g prepare_result_export.py --data=/data/scratch/florian/correl/PAZ/Nepal_Desc_059/MATHILOAll2Gif2/CORREL/20230612_101207)
6. Prepare files and directory structure for NSBAS processing: prepare_nsbas_process.py --data=WORKING_DIR (e.g prepare_nsbas_process.py --data=/data/scratch/florian/correl/PAZ/Nepal_Desc_059/MATHILOAll2Gif2/CORREL/20230612_101207)
