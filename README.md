# ASP-SAR

Processing tool package written in bash and python for image correlation of coregistered SAR images using the AMES stereo toolbox (https://stereopipeline.readthedocs.io/en/latest/). The coregistration is done using the MasTer toolbox().\
The processing chain additionally prepares the time series processing with NSBAS().

# To download the package

# Installation

# How to use it
1. Coregister SAR images using ALL2GIF.sh of MasTer toolbox
2. Prepare processing directory: prepare_correl_dir.py --data=YOUR_ALL2GIF_RESULTS --dest=YOUR_PROCESSING_DIR (processing directory needs to be created before)
3. Convert images to GeoTiff format: convert_geotiff.py --data=YOUR_PROCESSING_DIR
4. Adjust the correlation parameters in YOUR_PROCESSING_DIR/CORREL/asp_parameters.txt and start processing: process_stereo.py --data=YOUR_PROCESSING_DIR --pairs=PAIR_LIST (the pair list is created with prepa_MSBAS.sh of MasTer toolbox. It needs to be in the same format/naming). For each iteration, a new directory with the current timestamp is created as YOUR_PROCESSING_DIR/CORREL/TIMESTAMP (This will be referred as WORKING_DIR)
5. Prepare the results for download/analysis in QGIS: prepare_result_export.py --data=WORKING_DIR
6. Prepare files and directory structure for NSBAS processing: prepare_nsbas_process.py --data=WORKING_DIR
