#!/bin/bash -
#===============================================================================
#
#          FILE: gen_stm32yyxx_files.sh
#
#         USAGE: ./gen_stm32yyxx_files.sh
#
#   DESCRIPTION: generate all files to wrap HAL/LL files
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

outpath=cores/arduino/stm32/HAL
series=("F0" "F1" "F2" "F3" "F4" "F7" "H7" "L0" "L1" "L4")
llfile=stm32yyxx_ll.h

# Will create the file
print_header() {
echo "#include \"stm32_def_build.h\"
" > $outpath/$1
if [[ $1 = *"template"* ]]; then
  echo "#if 0" >> $outpath/$1
fi
}

# main
# Check if we are at the right place
if [ ! -d $outpath ]; then
	echo "Could not find $outpath!"
	echo "Launch $0 at the top of the Arduion STM32 core repository!"
	exit 1
fi

# Remove old file
rm $outpath/*
# Create ll header file
touch $outpath/$llfile

# Search all files for each series
for serie in ${series[@]}
do
	if [ -d system/Drivers/STM32${serie}xx_HAL_Driver/Src ]; then
		lower=`echo $serie | awk '{print tolower($0)}'`
		echo -n "Generating for $serie..."

		# Generate stm32yyxx*.c file
		filelist=(`find system/Drivers/STM32${serie}xx_HAL_Driver/Src -maxdepth 1 -name "stm32${lower}xx_*.c"`)
		for fp in ${filelist[@]}
		do
			# File name
			f=`echo $fp | awk -F/ '{print $NF}'`
			# Compute generic file name
			g=`echo $f | sed -e "s/$lower/yy/g"`
			if [ ! -f $outpath/$g ]; then
			  print_header $g
			fi
			# Amend file name under serie switch
			echo "#ifdef STM32${serie}xx" >> $outpath/$g
			echo "#include \"$f\"" >> $outpath/$g
			echo "#endif" >> $outpath/$g
		done

		# Generate ll header file
		# Amend file name under serie switch
		echo "#ifdef STM32${serie}xx" >> $outpath/$llfile
		# Search ll include file for the serie
		filelist=(`find system/Drivers/STM32${serie}xx_HAL_Driver/Inc -maxdepth 1 -name "stm32${lower}xx_ll_*.h" | sort`)
		for fp in ${filelist[@]}
		do
			# File name
			f=`echo $fp | awk -F/ '{print $NF}'`
			echo "#include \"$f\"" >> $outpath/$llfile
		done
		echo "#endif" >> $outpath/$llfile

		echo "done"
 	fi
done

# Search all template file to end "#if 0"
filelist=(`find $outpath -maxdepth 1 -name "stm32*_template.c"`)
for fp in ${filelist[@]}
do
 echo "#endif /* 0 */" >> $fp
done


