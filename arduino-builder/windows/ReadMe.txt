=================
checkWinBuild.bat
=================

This script aims at checking that all .ino files provided as "Examples" with the Arduino IDE do compile for a given platform.
This script works for Windows 7. 

Constraint: the sketches (.ino files) must have different names (at least the generated bin files must not have the same name).

Installation
============
* copy 'checkWinBuild.bat' and 'my.build.options.json' in a local folder of your Windows 7 computer.
(We assume that you already have an up and running Arduino IDE environment with all required boards installed).


Customization
=============
You need to tune:

* the paths and tools you want to use in 'checkWinBuild.bat'
      ** ArduinoBuilderPath: path where the Arduino Environment (the IDE, not your specific boards files) is installed in your local machine
			** ArduinoBuilderExe: arduino build tool to be used ("arduino-builder.exe")
			** BuilderExe: path to the arduino build tool
			** ResultFile: log file consolidating the output of this build campaign
			** OutputPath: where the bianry files will be stored (results of the compilations)
			** BuildDirPath: path used to run the compilation
			** SketchesPath: where to find the .ino files belonging to the "basic" examples
			** LibSketchesPath: where to find the .ino files belonging to the "libraries" examples
			** BuildOptionsFiles: build option file to use
			
* the arduino compiler options you want to use in 'my.build.options.json':
      ** typically you will update here the platform you want to check
         Example: "fqbn": "STM32:stm32l4xx:NUCLEO-L476RG"


Usage
=============
1. Start a Windows Console.
2. Go to the directory where you installed 'checkWinBuild.bat'.
3. Launch the script with or witout a parameter:
* no parameter => the script expects a build process for an STM32 target.
* parameter set => the script expects a build process for the target you specify.
Currently, only 1 value is supported: "Uno" to indicate you are compiling for Arduino Uno target.
4. Check the result file.