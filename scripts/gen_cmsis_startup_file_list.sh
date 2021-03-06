#!/bin/bash -
#===============================================================================
#
#          FILE: gen_cmsis_startup_file_list.sh
#
#         USAGE: ./gen_cmsis_startup_file_list.sh
#
#   DESCRIPTION: generate CMSIS startup files list
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Frederic.Pillon <frederic.pillon@st.com>
#  ORGANIZATION: STMicroelectronics
#     COPYRIGHT: Copyright (C) 2017, STMicroelectronics - All Rights Reserved
#       CREATED: 08/02/17 08:25
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error

outfile=cores/arduino/stm32/stm32_def_build.h

print_header() {
echo "#ifndef _STM32_DEF_BUILD_
#define _STM32_DEF_BUILD_

#if !defined(CMSIS_STARTUP_FILE) && !defined(CUSTOM_STARTUP_FILE)" > $outfile
}

print_footer() {
echo "#else
#error UNKNOWN CHIP
#endif
#else
#warning \"No CMSIS startup file defined, custom one should be used\"
#endif /* !CMSIS_STARTUP_FILE && !CUSTOM_STARTUP_FILE */
#endif /* _STM32_DEF_BUILD_ */" >> $outfile
}

print_list() {
# Handle first elements
local upper=`echo ${list[0]} | awk -F'[_.]' '{print toupper($2)}' | tr X x`
echo "#if defined($upper)
#define CMSIS_STARTUP_FILE \"${list[0]}\"" >> $outfile

if [ ${#list[@]} -gt 1 ]; then
	for i in ${list[@]:1}
    do
		upper=`echo $i | awk -F'[_.]' '{print toupper($2)}' | tr X x`
		echo "#elif defined($upper)
#define CMSIS_STARTUP_FILE \"$i\"" >> $outfile
	done
fi
}

# check if we are at the right place
if [ ! -f $outfile ]; then
	echo "Could not find $outfile!"
	echo "Launch $0 at the top of the Arduion STM32 core repository!"
	exit 1
fi

list=(`find -name "startup_*.s" | grep gcc | awk -F/ '{print $NF}' | sort -u`)
if [ ${#list[@]} -ne 0 ]; then
	echo "Number of startup files: ${#list[@]}"
	print_header
	print_list
	print_footer
else
	echo "No startup files found!"
fi
