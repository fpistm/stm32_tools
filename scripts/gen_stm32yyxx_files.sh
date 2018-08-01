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

HAL_outpath=cores/arduino/stm32/HAL
LL_outpath=cores/arduino/stm32/LL
series=("F0" "F1" "F2" "F3" "F4" "F7" "H7" "L0" "L1" "L4")
all_LL_file=stm32yyxx_ll.h

# Will create the file
print_HAL_header() {
if [[ $1 = *"template"* ]]; then
  echo "#if 0" > $HAL_outpath/$1
else
  touch $HAL_outpath/$1
fi
}

print_LL_header() {
upper=`echo $1 | awk '{print toupper($1)}' | sed -e "s/\./_/g"`
echo "#ifndef _${upper}_
#define _${upper}_
" > $LL_outpath/$1
}


# main
# Check if we are at the right place
if [ ! -d $HAL_outpath ]; then
  echo "Could not find $HAL_outpath!"
  echo "Launch $0 at the top of the Arduion STM32 core repository!"
  exit 1
fi
if [ ! -d $LL_outpath ]; then
  echo "Could not find $LL_outpath!"
  echo "Launch $0 at the top of the Arduion STM32 core repository!"
  exit 1
fi

# Remove old file
rm -f $HAL_outpath/* $LL_outpath/*

# Search all files for each series
for serie in ${series[@]}
do
  if [ -d system/Drivers/STM32${serie}xx_HAL_Driver/Src ]; then
    lower=`echo $serie | awk '{print tolower($0)}'`
    echo -n "Generating for $serie..."

    # Generate stm32yyxx_hal*.c file
    filelist=(`find system/Drivers/STM32${serie}xx_HAL_Driver/Src -maxdepth 1 -name "stm32${lower}xx_hal*.c"`)
    for fp in ${filelist[@]}
    do
      # File name
      f=`echo $fp | awk -F/ '{print $NF}'`
      # Compute generic file name
      g=`echo $f | sed -e "s/$lower/yy/g"`
      if [ ! -f $HAL_outpath/$g ]; then
        print_HAL_header $g
      fi
      # Amend file name under serie switch
      echo "#ifdef STM32${serie}xx" >> $HAL_outpath/$g
      echo "#include \"$f\"" >> $HAL_outpath/$g
      echo "#endif" >> $HAL_outpath/$g
    done

    # Generate stm32yyxx_ll_*.[ch] file
    filelist=(`find system/Drivers/STM32${serie}xx_HAL_Driver -maxdepth 2 -name "stm32${lower}xx_ll_*.[ch]"`)
    for fp in ${filelist[@]}
    do
      # File name
      f=`echo $fp | awk -F/ '{print $NF}'`
      # File extension
      e=`echo $f |awk -F . '{print $NF}'`
      # Compute generic file name
      g=`echo $f | sed -e "s/$lower/yy/g"`

      if [ $e == "h" ]; then
        if [ ! -f $LL_outpath/$g ]; then
          print_LL_header $g
        fi
        # Amend full LL header file
        echo "#include \"$g\"" >> $LL_outpath/${all_LL_file}.tmp
      fi
      # Amend file name under serie switch
      echo "#ifdef STM32${serie}xx" >> $LL_outpath/$g
      echo "#include \"$f\"" >> $LL_outpath/$g
      echo "#endif" >> $LL_outpath/$g
    done

    echo "done"
  fi
done

# Filter full LL header file
if [ ! -f $LL_outpath/$all_LL_file ]; then
  print_LL_header $all_LL_file
fi
echo "/* Include Low Layers drivers */" >> $LL_outpath/${all_LL_file}
echo "/* LL raised several warnings, ignore them */" >> $LL_outpath/${all_LL_file}
echo "#pragma GCC diagnostic push" >> $LL_outpath/${all_LL_file}
echo "#pragma GCC diagnostic ignored \"-Wunused-parameter\"" >> $LL_outpath/${all_LL_file}
echo "#pragma GCC diagnostic ignored \"-Wstrict-aliasing\"" >> $LL_outpath/${all_LL_file}
sort -u $LL_outpath/${all_LL_file}.tmp >> $LL_outpath/${all_LL_file}
echo "#pragma GCC diagnostic pop" >> $LL_outpath/${all_LL_file}
rm -f $LL_outpath/${all_LL_file}.tmp

# Search all template file to end "#if 0"
filelist=(`find $HAL_outpath -maxdepth 1 -name "stm32*_template.c"`)
for fp in ${filelist[@]}
do
 echo "#endif /* 0 */" >> $fp
done

# Search all LL header files to end guard
filelist=(`find $LL_outpath -maxdepth 1 -name "stm32yyxx_ll*.h"`)
for fp in ${filelist[@]}
do
  upper=`basename $fp | awk '{print toupper($1)}' | sed -e "s/\./_/g"`
  echo "#endif /* _${upper}_ */" >> $fp
done


