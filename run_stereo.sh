#!/usr/bin/bash

#module load asp

# correl_dir is path to current run dir (data_dir/CORREL)
DATA_DIR=$1
CORREL_DIR=$2
DATE1=$3
DATE2=$4
# name of directory for pair processing results f.e. 20220717_20221104
PAIR=$DATE1"_"$DATE2

# load asp_parameters.txt in DATA_DIR (DATA_DIR = WORK_DIR)
. $DATA_DIR"/asp_parameters.txt"

IMG_PRE=$DATA_DIR"/GEOTIFF/"$3".VV.mod_log.tif"
IMG_POST=$DATA_DIR"/GEOTIFF/"$4".VV.mod_log.tif"

cd $CORREL_DIR

mkdir $PAIR

cd $PAIR

session="-t $SESSION_TYPE --alignment-method $A_M --threads-multiprocess $THREADS --nodata-value $NO_DATA_S"
stereo="--corr-kernel $CORR_KERNEL --cost-mode $COST_MODE --stereo-algorithm $ST_ALG --corr-tile-size $CORR_T_S --subpixel-mode $SUBP_MODE --subpixel-kernel $SUBP_KERNEL --corr-seed-mode $CORR_S_MODE --xcorr-threshold $XCORR_TH --min-xcorr-level $MIN_XCORR_LVL --sgm-collar-size $SGM_C_SIZE"
denoising="--filter-mode $FILTER_MODE --rm-quantile-multiple $RM_QUANT_MULT"
filtering="--median-filter-size $MED_FILTER_SIZE --texture-smooth-size $TEXT_SMOOTH_SIZE --texture-smooth-scale $TEXT_SMOOTH_SCALE"

parallel_stereo $session $IMG_PRE $IMG_POST $BLACK_LEFT $BLACK_RIGHT $OUTPUT_DIR $stereo $denoising $filtering

exit

