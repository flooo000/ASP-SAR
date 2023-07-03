#!/usr/bin/bash

# module load asp

# $1 - data_dir (input of process_stereo.py), where data links are stored and parent dir of CORREL and GEOTIFF

# work_dir is path to current run dir (TIMESTAMP)
DATA_DIR=$1
WORK_DIR=$2
DATE1=$3
DATE2=$4
# name of directory for pair processing results f.e. 20220717_20221104
PAIR=$DATE1"_"$DATE2

# use update information to load correct asp_parameters.txt
# if update == True: use parameter file in working dir
# if update == False: use initial parameter file in ../CORREL/
UPDATE=$5
echo $UPDATE
if [ $UPDATE ]
then
. $WORK_DIR"/asp_parameters.txt"
else
. $DATA_DIR"/CORREL/asp_parameters.txt"
fi

IMG_PRE=$1"/GEOTIFF/"$3".VV.mod_log.tif"
IMG_POST=$1"/GEOTIFF/"$4".VV.mod_log.tif"

cd $WORK_DIR

mkdir $PAIR

cd $PAIR

if [ $FILTERING = true ]
then
parallel_stereo -t $SESSION_TYPE --alignment-method $A_M $IMG_PRE $IMG_POST $BLACK_LEFT $BLACK_RIGHT $OUTPUT_DIR --nodata-value $NO_DATA_S --datum $DATUM --prefilter-mode $PREF_MODE --prefilter-kernel-width $PREF_KER_M --corr-kernel $CORR_KERNEL --cost-mode $COST_MODE --stereo-algorithm $ST_ALG --corr-tile-size $CORR_T_S --subpixel-mode $SUBP_MODE --subpixel-kernel $SUBP_KERNEL --corr-seed-mode $CORR_S_MODE --processes $THREADS --xcorr-threshold $XCORR_TH --min-xcorr-level $MIN_XCORR_LVL --sgm-collar-size $SGM_C_SIZE --rm-quantile-percentile $RM_QUANT_PC --rm-quantile-multiple $RM_QUANT_MULT --rm-cleanup-passes $RM_CLEAN_PASS --filter-mode $FILTER_MODE --rm-half-kernel $RM_HALF_KERN --rm-min-matches $RM_MIN_MAT --rm-threshold $RM_TH

else
parallel_stereo -t $SESSION_TYPE --alignment-method $A_M $IMG_PRE $IMG_POST $BLACK_LEFT $BLACK_RIGHT $OUTPUT_DIR --nodata-value $NO_DATA_S --datum $DATUM --corr-kernel $CORR_KERNEL --cost-mode $COST_MODE --stereo-algorithm $ST_ALG --corr-tile-size $CORR_T_S --subpixel-mode $SUBP_MODE --subpixel-kernel $SUBP_KERNEL --corr-seed-mode $CORR_S_MODE --processes $THREADS --xcorr-threshold $XCORR_TH --min-xcorr-level $MIN_XCORR_LVL --sgm-collar-size $SGM_C_SIZE --prefilter-mode $PREF_MODE --prefilter-kernel-width $PREF_KER_M
fi

# maybe add disparitydebug here
disparitydebug asp/correl-F.tif
disparitydebug asp/correl-D_sub.tif

exit

