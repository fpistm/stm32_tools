# stm32_tools
Useful tools for stm32

## genpinmap
This script is able to generate the PeripheralPins.c for a specific board.

After file generation, review it carefully and please report any issue
[here](https://github.com/fpistm/stm32_tools/issues)

Once generated, you should comment a line if the pin is generated
several times for the same IP or if the pin should not be used
(overlaid with some HW on the board, for instance)

USAGE: genpinmap_arduino.py \<BOARD_NAME\> \<product xml file name\>
   - \<BOARD_NAME\> is the name of the board as it will be named in mbed
   - \<product xml file name\> is the STM32 file description in Cube MX

!!This xml file contains non alpha characters in its name, you should call it with quotes
