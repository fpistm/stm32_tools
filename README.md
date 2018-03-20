# stm32_tools
Useful tools for stm32

## arduino-builder-cli.sh (linux)
Used to build sketch(es) thanks Arduino CLI for all [Arduino_Core_STM32](https://github.com/stm32duino/Arduino_Core_STM32) variants.

Launch this script at the top of Arduino IDE directory.

**Examples:** 
  * To build all ino file found in _examples_ and  _libraries_ directories:
  
_Note: exclude_list.txt is used to filter sketches found._
  
`./arduino-builder-cli.sh -a`
  * To build a specific ino _\<path to my ino file\>/mysketch.ino_:
  
`./arduino-builder-cli.sh -i /tmp/SerialLoop.ino`
  * To build a specific set of sketch using a pattern:
  
`./arduino-builder-cli.sh -s "08\.|09\."`

will build all sketch in _examples/09.USB_ and _examples/08.Strings_ directories
  * To build a specific set of of boards using a pattern:
  
`./arduino-builder-cli.sh -b "F4"`

will build sketch for all variants name including **F4**.

## genpinmap (Moved to [Arduino_Tools](https://github.com/stm32duino/Arduino_Tools))

## gen_cmsis_startup_file_list.sh
Used to generate the stm32_def_build.h file.

Launch it at the root of [Arduino_Core_STM32](https://github.com/stm32duino/Arduino_Core_STM32)

## gen_stm32yyxx_files.sh
Used to generate stm32yyxx files to wrap HAL/LL files

Launch it at the root of [Arduino_Core_STM32](https://github.com/stm32duino/Arduino_Core_STM32)

## gen_peripheralpins_files.sh
Used to generate all `PeripheralPins.c` files for all STM32 MCU xml file description provided with [STM32CubeMX](http://www.st.com/en/development-tools/stm32cubemx.html) using [genpinmap.py](https://github.com/stm32duino/Arduino_Tools/blob/master/src/genpinmap/genpinmap_arduino.py) script.

Launch it from the same folder than [genpinmap.py](https://github.com/stm32duino/Arduino_Tools/blob/master/src/genpinmap/genpinmap_arduino.py) script.
