@echo off

REM ==============================================================================================================================
REM checkWinBuild.bat
REM This script aims at checking that all .ino files provided as "Examples" with the Arduino IDE do compile for a given platform.
REM Constraint: the sketches (.ino files) must have different names (at least the generated bin files must not have the same name).
REM ==============================================================================================================================
REM version 0.2 | handle a parameter to deal with the Arduino Uno which generates .hex files instead of .bin files
REM version 0.1 | initial revision
REM ==============================================================================================================================

SET ArduinoPath=C:\STM32\arduino-1.8.4-git
SET ArduinoBuilderExe=arduino-builder.exe
SET BuilderExe="%ArduinoPath%\%ArduinoBuilderExe%"
SET ResultFile="C:\TEMP\output\BuildResult.txt"
SET OutputPath="C:\TEMP\output"
SET BuildDirPath="C:\TEMP\output\builddir"
SET SketchesPath="%ArduinoPath%\examples"
SET LibSketchesPath="%ArduinoPath%\libraries"
SET BuildOptionsFiles="%~dp0\my.build.options.json"
SET BoardType="stm32"
SET BinaryExtension=bin

REM Print the version of the tool
echo ==============================================
%BuilderExe% -version
echo ==============================================

REM Prepare the build and output directories
if exist %OutputPath% del /f /q %OutputPath%\*.*
if not exist %OutputPath% mkdir %OutputPath%
if exist %BuildDirPath% rmdir /s /q  %BuildDirPath%
if not exist %BuildDirPath% mkdir %BuildDirPath%

REM Prepare the result file
echo "=========================" > %ResultFile%
echo "===== BUILD RESULTS =====" >> %ResultFile%
echo "=========================" >> %ResultFile%

REM Check if we do a STM32 build or Arduino Uno build
if "%1"=="" goto processing:
if "%1"=="Uno" set BoardType="ArduinoUno"
if "%1"=="Uno" set BinaryExtension=hex

REM The actual processing (compiling and checking)
:processing
echo "Board Type is: %BoardType%" >> %ResultFile%
echo "BinaryExtension is: %BinaryExtension%" >> %ResultFile%
REM Build all .ino files: Examples
echo "*** Examples ***" >> %ResultFile%
set /a counterExamples=0
FOR /r %SketchesPath% %%F IN (*.ino) DO (
  echo Building %%F using the option file %BuildOptionsFiles%
  set /a counterExamples+=1
  %BuilderExe% -compile -logger=human  -build-path %BuildDirPath% -build-options-file %BuildOptionsFiles% -verbose "%%F"
  xcopy /Y "%BuildDirPath%\%%~nxF.%BinaryExtension%" "%OutputPath%"
)
REM Check the status: Examples
set /a nbOkEx=0
set /a nbKoEx=0
FOR /r %SketchesPath% %%F IN (*.ino) DO (
	if exist %OutputPath%\%%~nxF.%BinaryExtension% set /a nbOkEx+=1
	if not exist %OutputPath%\%%~nxF.%BinaryExtension% set /a nbKoEx+=1
	if not exist %OutputPath%\%%~nxF.%BinaryExtension% echo "%%~nxF : compilation failure" 
	if not exist %OutputPath%\%%~nxF.%BinaryExtension% echo "%%~nxF : compilation failure" >> %ResultFile%
)

echo "%nbOkEx% PASSED and %nbKoEx% FAILED out of %counterExamples%"
echo "%nbOkEx% PASSED and %nbKoEx% FAILED out of %counterExamples%" >> %ResultFile%
echo "=========================" >> %ResultFile%

REM Build all .ino files: Libraries
echo "*** Libraries ***" >> %ResultFile%
set /a counterLibs=0
FOR /r %LibSketchesPath% %%F IN (*.ino) DO (
  echo Building %%F using the option file %BuildOptionsFiles%
  set /a counterLibs+=1
  %BuilderExe% -compile -logger=human  -build-path %BuildDirPath% -build-options-file %BuildOptionsFiles% -verbose "%%F"
  xcopy /Y "%BuildDirPath%\%%~nxF.%BinaryExtension%" "%OutputPath%"
)
REM Check the status: Libraries
set /a nbOkLib=0
set /a nbKoLib=0
FOR /r %LibSketchesPath% %%F IN (*.ino) DO (
	if exist %OutputPath%\%%~nxF.%BinaryExtension% set /a nbOkLib+=1
	if not exist %OutputPath%\%%~nxF.%BinaryExtension% set /a nbKoLib+=1
	if not exist %OutputPath%\%%~nxF.%BinaryExtension% echo "%%~nxF : compilation failure" 
	if not exist %OutputPath%\%%~nxF.%BinaryExtension% echo "%%~nxF : compilation failure" >> %ResultFile%
)

echo "%nbOkLib% PASSED and %nbKoLib% FAILED out of %counterLibs%"
echo "%nbOkLib% PASSED and %nbKoLib% FAILED out of %counterLibs%" >> %ResultFile%
echo "=========================" >> %ResultFile%