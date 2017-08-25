# stm32_tools
Useful tools for stm32

## build_arduino.sh (linux)
Used to build sketch(es) thanks Arduino CLI for all [Arduino_Core_STM32](https://github.com/stm32duino/Arduino_Core_STM32) variants.

Launch this script at the top of Arduino IDE directory.

**Examples:** 
  * To build all ino file found in _examples_ and  _libraries_ directories:
  
_Note: exclude_list.txt is used to filter sketches found._
  
`./build_arduino.sh -a`
  * To build a specific ino _\<path to my ino file\>/mysketch.ino_:
  
`./build_arduino.sh -i /tmp/SerialLoop.ino`
  * To build a specific set of sketch using a pattern:
  
`./build_arduino.sh -s "08\.|09\."`

will build all sketch in _examples/09.USB_ and _examples/08.Strings_ directories
  * To build a specific set of of boards using a pattern:
  
`./build_arduino.sh -b "F4"`

will build sketch for all variants name including **F4**.

## genpinmap (Moved to [Arduino_Tools](https://github.com/stm32duino/Arduino_Tools))

## gen_cmsis_startup_file_list.sh
Used to generate the stm32_def_build.h file.
Launch it at the root of [Arduino_Core_STM32](https://github.com/stm32duino/Arduino_Core_STM32)

