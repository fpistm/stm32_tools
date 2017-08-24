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
# Counter
NB_BUILD_PASSED=0
NB_BUILD_FAILED=0
NB_BUILD_TOTAL=0
CURRENT_SKETCH=1
TOTAL_SKETCH=1
TOTAL_BOARD=1
start_time=0
end_time=0

# Other
VERSION="0.1"
LOG_FILE="/tmp/build_arduino_`date +\%d_\%m_\%Y_\%H_\%M`.log"
boards_pattern=""
sketch_pattern=""

# Default
DEFAULT_BOARD_FILE="hardware/STM32/stm32/boards.txt"
DEFAULT_SKETCH="examples/01.Basics/Blink/Blink.ino"
DEFAULT_BOARD="Nucleo_64.NUCLEO_F103RB"

# List
sketch_list=($DEFAULT_SKETCH)
board_list=($DEFAULT_BOARD)

# Option
ALL_OPT=0

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
    echo "## [-a] [-b <board pattern>] [-i <.ino path>|[-s <sketch pattern>]] [-v] "
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
    echo "## -b <board pattern>: pattern to find one or more boards to build"
    echo "## -i <ino filepath>: single ino file to build (default: $DEFAULT_SKETCH)"
    echo "##   or "
    echo "## -s <sketch pattern>: pattern to find one or more sketch to build"
    echo "## -v: print version"
    echo "##"
    echo "############################################################"
    exit 0
}

check_result() {
  if [ $1 -ne 0 ]; then
    echo "$2 build FAILED: $1" >> $LOG_FILE
    echo -e "\033[1;31mFAILED\033[0m"
    NB_BUILD_FAILED=$((NB_BUILD_FAILED+1))
  else
    echo "$2 build PASSED." >> $LOG_FILE
    echo -e "\033[1;32mPASSED\033[0m"
    NB_BUILD_PASSED=$((NB_BUILD_PASSED+1))
  fi
}

print_stat() {
   echo "Total number of build: $NB_BUILD_TOTAL" >> $LOG_FILE
   echo -e "\t\tPASSED: $NB_BUILD_PASSED" >> $LOG_FILE
   echo -e "\t\tFAILED: $NB_BUILD_FAILED" >> $LOG_FILE
   echo "Build duration `date -d@$(($end_time - $start_time)) -u +%H:%M:%S`" >> $LOG_FILE

   echo "Total number of build: $NB_BUILD_TOTAL"
   echo -e "\t\t\033[1;32mPASSED\033[0m: $NB_BUILD_PASSED"
   echo -e "\t\t\033[1;31mFAILED\033[0m: $NB_BUILD_FAILED"
   echo "Build duration `date -d@$(($end_time - $start_time)) -u +%H:%M:%S`"
}

build_all() {
  for sketch in ${sketch_list[@]}
  do
    echo "Sketch ($CURRENT_SKETCH/$TOTAL_SKETCH): $sketch" >> $LOG_FILE
    echo -e "Sketch ($CURRENT_SKETCH/$TOTAL_SKETCH): \033[1;36m$sketch\033[0m"
    if [ ! -f $sketch ]; then
      echo "$sketch does not exist! Skip it!" >> $LOG_FILE
      echo "$sketch does not exist! Skip it!"
      continue
    fi
    for board in ${board_list[@]}
    do
      local pack=`echo $board | cut -d'.' -f1`
      local target=`echo $board | cut -d'.' -f2`
      build $pack $target $sketch
    done
    CURRENT_SKETCH=$((CURRENT_SKETCH+1))
  done
}

build() {
  local Pack=$1
  local Target=$2
  local Sketch=$3
  echo "build $Target" >> $LOG_FILE
  echo -ne "build \033[1;34m$Target\033[0m ..."
  #ex: ./arduino --board STM32:stm32:Nucleo_144:Nucleo_144_board=NUCLEO_F429ZI --verify $INO_FILE  >> $LOG_FILE 2>&1
  ./arduino --board STM32:stm32:${Pack}:board_part_num=$Target --verify $Sketch  >> $LOG_FILE 2>&1
  check_result $? $Target
  NB_BUILD_TOTAL=$((NB_BUILD_TOTAL+1))
}

# parse command line arguments
# options may be followed by one colon to indicate they have a required arg
options=`getopt -o ab:hi:s:v -- "$@"`

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

eval set -- "$options"

while true ; do
    case "$1" in
    -a) echo "Build all sketches"
        ALL_OPT=1
        shift;;
    -b) echo "Board pattern to build: $2"
        boards_pattern=$2
        shift 2;;
    -h|-\?) usage
        shift;;
    -i) echo "Ino to build: $2"
        sketch_list=($2)
        shift 2;;
    -s) echo "Sketch pattern to build: $2"
        sketch_pattern=$2
        shift 2;;
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

# Manage sketch
if [ $ALL_OPT -eq 1 ] || [ -n "$sketch_pattern" ]; then
  sketch_list=(`find examples libraries -name "*.ino" | grep -i -E "$sketch_pattern" | grep -v -f exclude_list.txt`)
fi

TOTAL_SKETCH=${#sketch_list[@]}
if [ $TOTAL_SKETCH -ne 0 ]; then
  echo "Number of sketch(es) to build: $TOTAL_SKETCH"
else
  echo "No sketch to build!"
  exit 2
fi

# Manage board
board_list=(`grep -E ".+\.menu\.board_part_num\.[^\.]+=" $DEFAULT_BOARD_FILE | grep -i -E "$boards_pattern" | cut -d'=' -f1 | cut -d'.' -f1,4 | sort -t. -k1r,1r -k2`)
TOTAL_BOARD=${#board_list[@]}
if [ $TOTAL_BOARD -ne 0 ]; then
  echo "Number of board(s) to build: $TOTAL_BOARD"
else
  echo "No board to build!"
  exit 3
fi

# Do the job
echo "Build start: `date`" >>  $LOG_FILE
start_time=$(date +%s)
build_all
echo "Build end: `date`" >>  $LOG_FILE
end_time=$(date +%s)
print_stat

echo "Logs available here: $LOG_FILE"
echo "End Arduino build." >> $LOG_FILE
echo "End Arduino build."

exit 0

