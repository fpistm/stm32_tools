#!/bin/bash -
#===============================================================================
#
#          FILE: gen_peripheralpins_files.sh
#
#         USAGE: Launch ./gen_peripheralpins_files.sh from the same folder
#                than genpinmap.py script
#
#   DESCRIPTION: generate all PeripheralPins.c file
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Frederic.Pillon <frederic.pillon@st.com>
#  ORGANIZATION: STMicroelectronics
#     COPYRIGHT: Copyright (C) 2018, STMicroelectronics - All Rights Reserved
#       CREATED: 03/16/18 12:03
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error

inpath=${HOME}/STM32CubeMX/db/mcu
genpinmap=genpinmap_arduino.py
outpath=Arduino

# main
# Check if we are at the right place
if [ ! -d $inpath ]; then
	echo "Could not find $inpath!"
	exit 1
fi

if [ ! -f $genpinmap ]; then
	echo "Could not find $genpinmap!"
	exit 1
fi

# Remove old file
if [ -d $outpath ]; then
	echo "Deleting $outpath"
	rm -fr $outpath/*
fi

# Search all mcu files 
filelist=(`find $inpath -maxdepth 1 -name "STM32*.xml"`)

for fp in ${filelist[@]}
do
	# File name
	f=`echo $fp | awk -F/ '{print $NF}'`
	# Compute generic file name
	n=`echo $f | sed -e "s/\.xml//g"`
	# Generate PeripheralPins.c
	python $genpinmap "$n" "$f"
done
