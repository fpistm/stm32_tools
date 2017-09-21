#!/bin/bash -
#===============================================================================
#
#          FILE: arduino-builder-cli.sh
#
#         USAGE: ./arduino-builder-cli.sh
#
#   DESCRIPTION: Used to build sketch(es) thanks Arduino CLI for all core variants.
#
#       OPTIONS: See usage()
#  REQUIREMENTS: Launch this script at the top of Arduino IDE directory.
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
NB_BUILD_SKIPPED=0
CURRENT_SKETCH=1
TOTAL_SKETCH=0
TOTAL_BOARD=0
start_time=0
end_time=0

# Other
VERSION="0.2"
LOG_FILE="/tmp/`basename $0`_`date +\%d_\%m_\%Y_\%H_\%M`.log"
boards_pattern=""
sketch_pattern=""
param=""
myPath=`dirname $(readlink -f "\$0")`

# Default.
DEFAULT_CORE_PATH="hardware/STM32/stm32"
DEFAULT_BOARD_FILE="$DEFAULT_CORE_PATH/boards.txt"
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

#Arduino EXIT STATUS
# 0 Success
# 1 Build failed or upload failed
# 2 Sketch not found
# 3 Invalid (argument for) commandline option
# 4 Preference passed to --get-pref does not exist
check_result() {
  if [ $1 -eq 0 ]; then
    echo "$2 build PASSED." >> $LOG_FILE
    echo -e "\033[1;32mPASSED\033[0m"
    NB_BUILD_PASSED=$((NB_BUILD_PASSED+1))
  elif [ $1 -lt 5 ]; then
    echo "$2 build FAILED: $1" >> $LOG_FILE
    echo -e "\033[1;31mFAILED\033[0m"
    NB_BUILD_FAILED=$((NB_BUILD_FAILED+1))
  else
    echo "$2 build SKIPPED." >> $LOG_FILE
    echo -e "\033[1;33mSKIPPED\033[0m"
    NB_BUILD_SKIPPED=$((NB_BUILD_SKIPPED+1))
  fi
}

print_stat() {
   local _passed=`echo "scale=2;($NB_BUILD_PASSED*100)/$NB_BUILD_TOTAL" | bc`
   local _failed=`echo "scale=2;($NB_BUILD_FAILED*100)/$NB_BUILD_TOTAL" | bc`
   local _skipped=`echo "scale=2;($NB_BUILD_SKIPPED*100)/$NB_BUILD_TOTAL" | bc`

   echo -e "Total number of build:\t\t$NB_BUILD_TOTAL" >> $LOG_FILE
   echo -e "\t\tPASSED:\t\t$NB_BUILD_PASSED ($_passed%)" >> $LOG_FILE
   echo -e "\t\tFAILED:\t\t$NB_BUILD_FAILED ($_failed%)" >> $LOG_FILE
   echo -e "\t\tSKIPPED:\t$NB_BUILD_SKIPPED ($_skipped%)" >> $LOG_FILE
   echo "Build duration `date -d@$(($end_time - $start_time)) -u +%H:%M:%S`" >> $LOG_FILE

   echo -e "Total number of build:\t\t$NB_BUILD_TOTAL"
   echo -e "\t\t\033[1;32mPASSED\033[0m:\t\t$NB_BUILD_PASSED ($_passed%)"
   echo -e "\t\t\033[1;31mFAILED\033[0m:\t\t$NB_BUILD_FAILED ($_failed%)"
   echo -e "\t\t\033[1;33mSKIPPED\033[0m:\t$NB_BUILD_SKIPPED ($_skipped%)"
   echo "Build duration `date -d@$(($end_time - $start_time)) -u +%H:%M:%S`"
}

check_sketch_param_Serial() {
  local _sketch=$1
  local _serialx=`grep Serial[0-9] $_sketch`
  if [ -n "$_serialx" ]; then
    echo "Sketch requires to enable all Serial" >> $LOG_FILE
    echo "Sketch requires to enable all Serial"
    param="$param,xserial=SerialAll"
  fi
}

check_sketch_param_USB_HID() {
  local _sketch=$1
  local _usb_hid=`echo $_sketch | grep USB`
  if [ -n "$_usb_hid" ]; then
    echo "Sketch requires to enable USB HID" >> $LOG_FILE
    echo "Sketch requires to enable USB HID"
    param="$param,usb=HID"
  fi
}

check_target_param() {
  local _target=$1
  local _serialx=`echo $param | grep Serial`
  local _usb_hid=`echo $param | grep HID`
  if [ -n "$_serialx" ]; then
    # check if Serial1 are available in the variant
    local isserial1=`grep -E "^\s*HardwareSerial\s+Serial1" $DEFAULT_CORE_PATH/variants/$_target/variant.cpp`
    if [ -z "$isserial1" ]; then
      echo "Serial1 not defined for this board, skip it." >> $LOG_FILE
      check_result 5 $_target
	  return 1
    fi
  fi
  if [ -n "$_usb_hid" ]; then
    local isUSB=""
    if [ -f $DEFAULT_CORE_PATH/variants/$_target/usb/usbd_desc.h ]; then
      # check if HID_Desc are available in the variant
      isUSB=`grep -E "USBD_DescriptorsTypeDef\s+HID_Desc" $DEFAULT_CORE_PATH/variants/$_target/usb/usbd_desc.h`
    fi
    if [ -z "$isUSB" ]; then
      echo "USB HID not supported by this board, skip it." >> $LOG_FILE
      check_result 5 $_target
	  return 2
    fi
  fi
  return 0
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
    # Check option
    check_sketch_param_Serial $sketch
    check_sketch_param_USB_HID $sketch

    for board in ${board_list[@]}
    do
      local pack=`echo $board | cut -d'.' -f1`
      local target=`echo $board | cut -d'.' -f2`
      echo "build $target" >> $LOG_FILE
      echo -ne "build \033[1;34m$target\033[0m ..."
      NB_BUILD_TOTAL=$((NB_BUILD_TOTAL+1)) 

	  # Check if option are applicable for the target
	  check_target_param $target
      if [ $? -ne 0 ]; then
        continue
      fi
      build $pack $target $sketch "$param"
    done
	param=""
    CURRENT_SKETCH=$((CURRENT_SKETCH+1))
  done
}

build() {
  local _pack=$1
  local _target=$2
  local _sketch=$3
  local _param=$4

  #ex: ./arduino --board STM32:stm32:Nucleo_144:Nucleo_144_board=NUCLEO_F429ZI --verify $INO_FILE  >> $LOG_FILE 2>&1
  ./arduino --board STM32:stm32:${_pack}:pnum=${_target}${_param} --verify ${_sketch}  >> $LOG_FILE 2>&1
  check_result $? $_target
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
  sketch_list=(`find examples libraries -name "*.ino" | grep -i -E "$sketch_pattern" | grep -v -f $myPath/../conf/exclude_list.txt`)
fi

TOTAL_SKETCH=${#sketch_list[@]}
if [ $TOTAL_SKETCH -ne 0 ]; then
  echo "Number of sketch(es) to build: $TOTAL_SKETCH"
else
  echo "No sketch to build!"
  exit 2
fi

# Manage board
board_list=(`grep -E ".+\.menu\.pnum\.[^\.]+=" $DEFAULT_BOARD_FILE | grep -i -E "$boards_pattern" | cut -d'=' -f1 | cut -d'.' -f1,4 | sort -t. -k1r,1r -k2`)
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

