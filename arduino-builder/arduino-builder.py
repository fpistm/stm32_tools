# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import time
import fnmatch
import shutil
import subprocess
import tempfile
import argparse

# Create a Json file for a better path management
config_filename = "config.json"
home = os.path.expanduser("~")
tempdir = tempfile.gettempdir()
try:
    config_file = open(config_filename, "r")
except IOError:
    print("Please set your configuration in '%s' file" % config_filename)
    config_file = open(config_filename, "w")
    if sys.platform.startswith("win32"):
        print("Platform is Windows")
        arduino_path = "C:\\Program Files (x86)\\Arduino"  # arduino default path
        arduino_packages = home + "\\AppData\\Local\\Arduino15\\packages"  # Windows 7
        build_output_dir = (
            tempdir + "\\temp_arduinoBuilderOutput"
        )  # Windows 7 temporary directory using by arduino builder
        output_dir = home + "\\arduinoBuilderOutput"  # output directory
    elif sys.platform.startswith("linux"):
        print("Platform is Linux")
        arduino_path = home + "/Documents/arduino-1.8.5"
        arduino_packages = home + "/.arduino15/packages"
        build_output_dir = tempdir + "/temp_arduinoBuilderOutput"
        output_dir = home + "/Documents/arduinoBuilderOutput"
    elif sys.platform.startswith("darwin"):
        print("Platform is Mac OSX")
        arduino_path = home + "/Applications/Arduino/"
        arduino_packages = home + "/Library/Arduino15/packages"
        build_output_dir = tempdir + "/temp_arduinoBuilderOutput"
        output_dir = home + "/Documents/arduinoBuilderOutput"
    else:
        print("Platform unknown")
        arduino_path = "<Set Arduino install path>"
        arduino_packages = "<Set Arduino packages install path>"
        build_output_dir = "<Set arduino builder temporary folder install path>"
        output_dir = "<Set your output directory path>"
    config_file.write(
        json.dumps(
            {
                "ARDUINO_PATH": arduino_path,
                "ARDUINO_PACKAGES": arduino_packages,
                "BUILD_OUPUT_DIR": build_output_dir,
                "OUPUT_DIR": output_dir,
            }
        )
    )
    config_file.close()
    exit(1)

config = json.load(config_file)
config_file.close()

# Common path
arduino_path = config["ARDUINO_PATH"]
arduino_packages = config["ARDUINO_PACKAGES"]
build_output_dir = config["BUILD_OUPUT_DIR"]
output_dir = config["OUPUT_DIR"]

arduino_builder = os.path.join(arduino_path, "arduino-builder")
hardware_path = os.path.join(arduino_path, "hardware")
libsketches_path_default = os.path.join(arduino_path, "libraries")
tools_path = os.path.join(arduino_path, "tools-builder")

# Ouput directory path
bin_dir = os.path.join(output_dir, "binaries")
std_dir = os.path.join(output_dir, "std_folder")

# Default
sketch_default = os.path.join(
    arduino_path, "examples", "01.Basics", "Blink", "Blink.ino"
)

# List
sketch_list = []
board_list = []

# Counter
nb_build_total = 0
nb_build_passed = 0
nb_build_failed = 0


def createFolder(folder):
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
    except OSError:
        print("Error: Creating directory. " + folder)


# Set up specific options to customise arduino builder command
def set_varOpt(board):
    var_type_default = board[0]
    var_num_default = board[1]
    upload_method_default = "STLink"
    serial_mode_default = "generic"
    usb_mode_default = "none"
    option_default = "osstd"
    variantOption = "STM32:stm32:{var_type}:pnum={var_num}".format(
        var_type=var_type_default, var_num=var_num_default
    )
    variantOption += ",upload_method={upload_method}".format(
        upload_method=upload_method_default
    )
    variantOption += ",xserial={serial_mode},usb={usb_mode},opt={option}".format(
        serial_mode=serial_mode_default,
        usb_mode=usb_mode_default,
        option=option_default,
    )

    return variantOption


# Configure arduino builder command
def build(variant, sketch_path):
    cmd = []
    cmd.append(arduino_builder)
    cmd.append("-hardware")
    cmd.append(hardware_path)
    cmd.append("-hardware")
    cmd.append(arduino_packages)
    cmd.append("-tools")
    cmd.append(tools_path)
    cmd.append("-tools")
    cmd.append(arduino_packages)
    cmd.append("-libraries")
    cmd.append(libsketches_path_default)
    cmd.append("-fqbn")
    cmd.append(variant)
    cmd.append("-ide-version=10805")
    cmd.append("-build-path")
    cmd.append(build_output_dir)
    cmd.append("-verbose")
    cmd.append(sketch_path)
    return cmd


# Run arduino builder command
def run_command(cmd, board_name, sketch_name):
    boardstd = os.path.join(
        std_dir, board_name
    )  # Board specific folder that contain stdout and stderr files
    createFolder(boardstd)
    timer = time.strftime("%Y-%m-%d-%Hh%M")
    stddout_name = timer + "_" + sketch_name + "_stdout.txt"
    stdderr_name = timer + "_" + sketch_name + "_stderr.txt"
    with open(os.path.join(boardstd, stddout_name), "w") as stdout, open(
        os.path.join(boardstd, stdderr_name), "w"
    ) as stderr:
        res = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
        print("Building in progress ...")
        res.wait()
        return res.returncode


# Manage sketches list
def manage_inos():
    global sketch_list
    # Find all inos or all patterned inos
    if args.all or args.sketches:
        sketch_list = find_inos()
    # Only one ino
    elif args.ino:
        if os.path.exists(args.ino):
            sketch_list = [args.ino]
        else:
            assert os.path.exists(
                os.path.join(arduino_path, args.ino)
            ), "Ino path does not exist"
            sketch_list = [os.path.join(arduino_path, args.ino)]
    # Inos listed in a file
    elif args.file:
        assert os.path.exists(args.file), "Sketches list file does not exist"
        with open(args.file, "r") as f:
            for line in f.readlines():
                ino = line.rstrip()
                if os.path.exists(ino):
                    sketch_list.append(ino)
                elif os.path.exists(os.path.join(arduino_path, ino)):
                    sketch_list.append(os.path.join(arduino_path, ino))
                else:
                    print("Ignore %s as does not exist." % ino)
    # Defailt ino to build
    else:
        sketch_list = [sketch_default]
    assert len(sketch_list), "No sketch to build!"


# Find all .ino files
def find_inos():
    inoList = []
    for root, dirs, files in os.walk(arduino_path):
        for file in files:
            if file.endswith(".ino"):
                if args.sketches:
                    regex = ".*(" + args.sketches + ").*"
                    x = re.match(regex, os.path.join(root, file), re.IGNORECASE)
                    if x:
                        inoList.append(os.path.join(root, x.group(0)))
                else:
                    inoList.append(os.path.join(root, file))
    return sorted(inoList)


# Return a list of all board types and names using the board.txt file
def find_board():
    for path in [arduino_packages, hardware_path]:
        for root, dirs, files in os.walk(path, followlinks=True):
            for file in files:
                if fnmatch.fnmatch(file, "boards.txt"):
                    if os.path.getsize(os.path.join(root, file)) != 0:
                        with open(os.path.join(root, file), "r") as f:
                            regex = "(.+)\.menu\.pnum\.([^\.]+)="
                            for line in f.readlines():
                                x = re.match(regex, line)
                                if x:
                                    if args.board:
                                        reg = ".*(" + args.board + ").*"
                                        y = re.match(reg, x.group(0), re.IGNORECASE)
                                        if y:
                                            board_type = x.group(1)
                                            board_name = x.group(2)
                                            board = (board_type, board_name)
                                            board_list.append(board)
                                    else:
                                        board_type = x.group(1)
                                        board_name = x.group(2)
                                        board = (board_type, board_name)
                                        board_list.append(board)
    return sorted(board_list)


# Check the status
def check_status(status, board_name, sketch_name):
    global nb_build_passed
    global nb_build_failed
    global nb_build_total
    nb_build_total += 1
    if status == 0:
        print("SUCESS")
        bin_copy(board_name, sketch_name)
        nb_build_passed += 1
    elif status == 1:
        print("FAILED")
        nb_build_failed += 1
    else:
        print("Error ! Check the run_command exit status ! Return code = ", status)


# Create a "bin" directory for each board and copy all binary files
# from the builder output directory into it
def bin_copy(board_name, sketch_name):
    board_bin = os.path.join(bin_dir, board_name)
    createFolder(board_bin)
    binfile = os.path.join(build_output_dir, sketch_name + ".bin")
    try:
        shutil.copy(binfile, os.path.abspath(board_bin))
    except OSError as e:
        print(
            "Impossible to copy the binary from the arduino builder output: ",
            e.strerror,
        )
        raise


# Create the output file --> Ongoing improvment
def create_output_file():
    filename = os.path.join(output_dir, time.strftime("Result_file_%Y-%m-%d.txt"))
    with open(filename, "w") as file:
        file.write(" ************************************** \n")
        file.write(" *********** OUTPUT / RESULT ********** \n")
        file.write(" ************************************** \n")
        file.write(time.strftime(" %A %d %B %Y %H:%M:%S "))
        file.write("\n Full path = {} \n".format(os.path.abspath(output_dir)))
    return filename


# Automatic run
def run_auto():
    file = create_output_file()
    current_sketch = 0
    for files in sketch_list:
        boardOk = []
        boardKo = []
        current_board = 0
        current_sketch += 1
        sketch_name = os.path.basename(files)
        print(
            "\nRUNNING : {} ({}/{}) ".format(
                sketch_name, current_sketch, len(sketch_list)
            )
        )
        print("Sketch path : " + files)
        for board in board_list:
            board_name = board[1]
            current_board += 1
            print(
                "\nBoard ({}/{}) : {}".format(
                    current_board, len(board_list), board_name
                )
            )
            variant = set_varOpt(board)
            command = build(variant, files)
            status = run_command(command, board_name, sketch_name)
            if status == 0:
                boardOk.append(board_name)
            if status == 1:
                boardKo.append(board_name)
            check_status(status, board_name, sketch_name)
        with open(file, "a") as f:
            f.write("\nSketch : " + sketch_name)
            f.write("\nSketch location : " + files)
            if len(boardOk):
                f.write("\nBuild PASSED for these boards :\n")
                for b in boardOk:
                    f.write(str(b) + "\n")
            f.write(
                "Total build PASSED for this sketch : {} / {}".format(
                    len(boardOk), len(board_list)
                )
            )
            if len(boardKo):
                f.write("\nBuild FAILED for these boards :\n")
                for b in boardKo:
                    f.write(str(b))
            f.write(
                "\nTotal build FAILED for this sketch : {} / {}\n".format(
                    len(boardKo), len(board_list)
                )
            )
    print("\n****************** PROCESSING COMPLETED ******************")
    print("PASSED = {}/{}".format(nb_build_passed, nb_build_total))
    print("FAILED = {}/{}".format(nb_build_failed, nb_build_total))
    print("Logs are available here: " + output_dir)


# Create output folders
createFolder(build_output_dir)
createFolder(output_dir)
createFolder(bin_dir)
createFolder(std_dir)

assert os.path.exists(arduino_path), (
    "Path does not exist: %s . Please set this path in the json config file"
    % arduino_path
)
assert os.path.exists(arduino_packages), (
    "Path does not exist: %s . Please set this path in the json config file"
    % arduino_packages
)
assert os.path.exists(build_output_dir), (
    "Path does not exist: %s . Please set this path in the json config file"
    % build_output_dir
)
assert os.path.exists(output_dir), (
    "Path does not exist: %s . Please set this path in the json config file"
    % output_dir
)

# Parser
parser = argparse.ArgumentParser(description="Automatic build script")
parser.add_argument(
    "-a",
    "--all",
    help="-a : automatic build - build all sketches for all board",
    action="store_true",
)
parser.add_argument(
    "-b",
    "--board",
    help="-b <board pattern>: pattern to find one or more boards to build",
)
group = parser.add_mutually_exclusive_group()
group.add_argument("-i", "--ino", help="-i <ino filepath>: single ino file to build")
group.add_argument(
    "-f",
    "--file",
    help=" -f <sketches list file>: file containing list of sketches to build",
)
group.add_argument(
    "-s",
    "--sketches",
    help=" -s <sketch pattern>: pattern to find one or more sketch to build",
)
args = parser.parse_args()

manage_inos()
find_board()

# Run builder
run_auto()
