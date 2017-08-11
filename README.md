# stm32_tools
Useful tools for stm32

## build_arduino.sh (linux)
Used to build sketch(es) thanks Arduino CLI for all core variants.
Launch this script at the top of Arduino IDE directory.
**Examples:** 
  * To build all ino file found in _examples_ and  _libraries_ directories:
  
_Note: exclude_list.txt is used to filter sketches found._
  
`./build_arduino.sh -a`
  * To build a specific sketch _\<path to my ino file\>/mysketch.ino_:
  
`./build_arduino.sh -s /tmp/SerialLoop.ino`
  
## genpinmap (Moved to [Arduino_Tools](https://github.com/stm32duino/Arduino_Tools))

## gen_cmsis_startup_file_list.sh
Used to generate the stm32_def_build.h file.
Launch it at the root of [Arduino_Core_STM32](https://github.com/stm32duino/Arduino_Core_STM32)

