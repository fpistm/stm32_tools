#!/bin/bash -
#===============================================================================
#
#          FILE: genpinmap_arduino.sh
#
#         USAGE: ./genpinmap_arduino.sh
#
#   DESCRIPTION:
#
#       OPTIONS: None
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: fpistm
#  ORGANIZATION: STMicroelectronics
#       CREATED: 03/07/17 08:42
#      REVISION: 1.0
#===============================================================================

set -o nounset                              # Treat unset variables as an error

# See xml file name in <STM32CubeMX install dir>\db\mcu

# GPIO AF function not supported:: python genpinmap_arduino.py NUCLEO_F030R8 "STM32F030R8Tx.xml"
# GPIO AF function not supported::python genpinmap_arduino.py DISCO_F051R8  "STM32F051R8Tx.xml"
#
python genpinmap_arduino.py NUCLEO-F429ZI "STM32F429Z(E-G-I)Tx.xml"
