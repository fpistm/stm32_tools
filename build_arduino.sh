#!/bin/bash -
#===============================================================================
#
#          FILE: build.sh
#
#         USAGE: ./build.sh
#
#   DESCRIPTION:
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Frederic.Pillon <frederic.pillon@st.com>
#  ORGANIZATION: STMicroelectronics
#     COPYRIGHT: Copyright (C) 2017, STMicroelectronics - All Rights Reserved
#       CREATED: 06/21/17 15:24
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error
NB_OK=0
NB_KO=0
NB_BUILD=0
VERSION="0.1"
LOG_FILE=/tmp/build_arduino_`date +\%d_\%m_\%Y_\%H_\%M`.log
INO_FILE=examples/01.Basics/Blink/Blink.ino
ALL_INO=0

###############################################################################
## Help function
usage()
{
    echo "############################################################"
    echo "##"
    echo "##  `basename $0`"
    echo "##"
    echo "############################################################"
    echo "##"
    echo "## `basename $0`"
    echo "## [-a] [-s <sketch .ino path>][-v] "
    echo "##"
    echo "## Launch this script at the top of Arduino IDE directory."
    echo "##"
    echo "## Mandatory options:"
    echo "##"
    echo "## None"
    echo "##"
    echo "## Optionnal:"
    echo "##"
    echo "## -a: build all sketch found."
	echo "## -s <sketch filepath>: ino file to build (default: $INO_FILE)"
    echo "## -v: print version"
    echo "##"
    echo "############################################################"
    exit 0
}

check_result() {
  if [ $1 -ne 0 ]; then
    echo "$2 build KO: $1" >> $LOG_FILE
    echo -e "\033[1;31mKO\033[0m"
	NB_KO=$((NB_KO+1))
  else
    echo "$2 build OK." >> $LOG_FILE
    echo -e "\033[1;32mOK\033[0m"
	NB_OK=$((NB_OK+1))
  fi
  echo ""
}

print_stat() {
   echo "Total number of build: $NB_BUILD" >> $LOG_FILE
   echo "\t\tPASS: $NB_OK" >> $LOG_FILE
   echo "\t\tFAIL: $NB_KO" >> $LOG_FILE

   echo "Total number of build: $NB_BUILD"
   echo "\t\tPASS: $NB_OK"
   echo "\t\tFAIL: $NB_KO"
   echo ""
}

build_all() {
  local Sketch=$INO_FILE
  if [ $# -ne 0 ]; then
    Sketch=$1
  fi
  echo "Sketch: $Sketch" >> $LOG_FILE
  echo -e "Sketch: \033[1;36m$Sketch\033[0m"

  build NUCLEO_F030R8 Nucleo_64 $Sketch
  build NUCLEO_F091RC Nucleo_64 $Sketch
  build NUCLEO_F103RB Nucleo_64 $Sketch
  build NUCLEO_F207ZG Nucleo_144 $Sketch
  build NUCLEO_F303RE Nucleo_64 $Sketch
  build NUCLEO_F401RE Nucleo_64 $Sketch
  build NUCLEO_F411RE Nucleo_64 $Sketch
  build NUCLEO_F429ZI Nucleo_144 $Sketch

  build NUCLEO_L053R8 Nucleo_64 $Sketch
  build NUCLEO_L432KC Nucleo_32 $Sketch
  build NUCLEO_L476RG Nucleo_64 $Sketch

  build DISCO_F100RB Disco $Sketch
  build DISCO_F407VG Disco $Sketch
  build DISCO_F746NG Disco $Sketch

  #build BLUEPILL_F103C8 Other $sketch_file
  #build MAPLEMINI_F103CB Other $sketch_file
}

build() {
  local Target=$1
  local Pack=$2
  local Sketch=$3
  echo "build $Target" >> $LOG_FILE
  echo -ne "build \033[1;34m$Target\033[0m ..."
  #ex: ./arduino --board STM32:stm32:Nucleo_144:Nucleo_144_board=NUCLEO_F429ZI --verify $INO_FILE  >> $LOG_FILE 2>&1
  ./arduino --board STM32:stm32:${Pack}:board_part_num=$Target --verify $Sketch  >> $LOG_FILE 2>&1
  check_result $? $Target
  NB_BUILD=$((NB_BUILD+1))
}

# parse command line arguments
# options may be followed by one colon to indicate they have a required arg
options=`getopt -o as:hv -- "$@"`

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

eval set -- "$options"

while true ; do
    case "$1" in
    -a) echo "Build all sketches"
		ALL_INO=1
        shift;;
	-s) echo "Sketch to build: $2"
        INO_FILE=$2
        shift 2;;
    -h|-\?) usage
        shift;;
    -v) echo "`basename $0`: $VERSION"
		exit 0
        shift;;
    --) shift;
        break;;
    *) break;;
    esac
done

echo "Start Arduino build..." > $LOG_FILE 2>&1
if [ $? -ne 0 ]; then
    echo "Could not create log file $LOG_FILE"
    exit 1
fi

if [ $ALL_INO -eq 0 ]; then
  if [ ! -f $INO_FILE ]; then
    echo "$INO_FILE does not exist!"
    exit 2
  fi
  build_all
else
  list=(`find portable  examples libraries -name "*.ino"`)
  if [ ${#list[@]} -ne 0 ]; then
    echo "Number of ino files found: ${#list[@]}"
  else
    echo "No ino files found!"
    exit 3
  fi
  for i in ${list[@]}
  do
    build_all $i
  done
fi

print_stat

echo "End Arduino build." >> $LOG_FILE
echo "Logs available here: $LOG_FILE"
echo "End Arduino build."

exit 0

