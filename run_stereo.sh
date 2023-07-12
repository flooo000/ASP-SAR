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

if [ $FILTERING = true ]
then
parallel_stereo -t $SESSION_TYPE --alignment-method $A_M $IMG_PRE $IMG_POST $BLACK_LEFT $BLACK_RIGHT $OUTPUT_DIR --nodata-value $NO_DATA_S --datum $DATUM --prefilter-mode $PREF_MODE --prefilter-kernel-width $PREF_KER_M --corr-kernel $CORR_KERNEL --cost-mode $COST_MODE --stereo-algorithm $ST_ALG --corr-tile-size $CORR_T_S --subpixel-mode $SUBP_MODE --subpixel-kernel $SUBP_KERNEL --corr-seed-mode $CORR_S_MODE --processes $THREADS --xcorr-threshold $XCORR_TH --min-xcorr-level $MIN_XCORR_LVL --sgm-collar-size $SGM_C_SIZE --rm-quantile-percentile $RM_QUANT_PC --rm-quantile-multiple $RM_QUANT_MULT --rm-cleanup-passes $RM_CLEAN_PASS --filter-mode $FILTER_MODE --rm-half-kernel $RM_HALF_KERN --rm-min-matches $RM_MIN_MAT --rm-threshold $RM_TH  --median-filter-size $MED_FILTER_SIZE --texture-smooth-size $TEXT_SMOOTH_SIZE --texture-smooth-scale $TEXT_SMOOTH_SCALE

else
parallel_stereo -t $SESSION_TYPE --alignment-method $A_M $IMG_PRE $IMG_POST $BLACK_LEFT $BLACK_RIGHT $OUTPUT_DIR --nodata-value $NO_DATA_S --datum $DATUM --corr-kernel $CORR_KERNEL --cost-mode $COST_MODE --stereo-algorithm $ST_ALG --corr-tile-size $CORR_T_S --subpixel-mode $SUBP_MODE --subpixel-kernel $SUBP_KERNEL --corr-seed-mode $CORR_S_MODE --processes $THREADS --xcorr-threshold $XCORR_TH --min-xcorr-level $MIN_XCORR_LVL --sgm-collar-size $SGM_C_SIZE --prefilter-mode $PREF_MODE --prefilter-kernel-width $PREF_KER_M
fi

# maybe add disparitydebug here
disparitydebug asp/correl-F.tif
disparitydebug asp/correl-D_sub.tif

exit

