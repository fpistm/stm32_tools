# -*- coding: utf-8 -*-

# File name            : arduino-builder.py
# Author               : Angela RANDOLPH <angela.randolph@reseau.eseo.fr>
# Other contributors   : Frederic PILLON <frederic.pillon@st.com>
# Created              : 26/04/2018
# Python Version       : 2.7 / 3.x

# Description         : Used to build sketch(es) thanks to Arduino Builder
#                       See https://github.com/arduino/arduino-builder
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
build_id = time.strftime("_%Y-%m-%d_%H-%M-%S")
script_path = os.path.dirname(os.path.abspath(__file__))

try:
    config_file = open(config_filename, "r")
except IOError:
    print(
        "Please set your configuration in '%s' file"
        % os.path.join(script_path, config_filename)
    )
    config_file = open(config_filename, "w")
    if sys.platform.startswith("win32"):
        print("Default config set for Windows environment.")
        arduino_path = "C:\\Program Files (x86)\\Arduino"  # arduino default path
        arduino_packages = home + "\\AppData\\Local\\Arduino15\\packages"  # Windows 7
        build_output_dir = (
            tempdir + "\\temp_arduinoBuilderOutput"
        )  # Windows 7 temporary directory using by arduino builder
        root_output_dir = home + "\\arduinoBuilderOutput"  # output directory
        sketchbook_path = home + "\\My Documents\\Arduino"
    elif sys.platform.startswith("linux"):
        print("Default config set for Linux environment.")
        arduino_path = home + "/Documents/arduino-1.8.5"
        arduino_packages = home + "/.arduino15/packages"
        build_output_dir = tempdir + "/temp_arduinoBuilderOutput"
        root_output_dir = home + "/Documents/arduinoBuilderOutput"
        sketchbook_path = home + "/Documents/Arduino"
    elif sys.platform.startswith("darwin"):
        print("Default config set for Mac OSX environment.")
        arduino_path = home + "/Applications/Arduino/"
        arduino_packages = home + "/Library/Arduino15/packages"
        build_output_dir = tempdir + "/temp_arduinoBuilderOutput"
        root_output_dir = home + "/Documents/arduinoBuilderOutput"
        sketchbook_path = home + "/Documents/Arduino"
    else:
        print("Platform unknown.")
        arduino_path = "<Set Arduino install path>"
        arduino_packages = "<Set Arduino packages install path>"
        build_output_dir = "<Set arduino builder temporary folder install path>"
        root_output_dir = "<Set your output directory path>"
        sketchbook_path = "<Set the sketchbook location>"
    config_file.write(
        json.dumps(
            {
                "ARDUINO_PATH": arduino_path,
                "ARDUINO_PACKAGES": arduino_packages,
                "BUILD_OUPUT_DIR": build_output_dir,
                "ROOT_OUPUT_DIR": root_output_dir,
                "SKETCHBOOK_PATH": sketchbook_path,
            },
            indent=2,
        )
    )
    config_file.close()
    exit(1)

config = json.load(config_file)
config_file.close()

# Common path
arduino_path = config["ARDUINO_PATH"]
arduino_packages = config["ARDUINO_PACKAGES"]
build_output_dir = config["BUILD_OUPUT_DIR"] + build_id
root_output_dir = config["ROOT_OUPUT_DIR"]
sketchbook_path = config["SKETCHBOOK_PATH"]

assert os.path.exists(arduino_path), (
    "Path does not exist: %s . Please set this path in the json config file"
    % arduino_path
)
assert os.path.exists(arduino_packages), (
    "Path does not exist: %s . Please set this path in the json config file"
    % arduino_packages
)

assert os.path.exists(sketchbook_path), (
    "Path does not exist: %s . Please set this path in the json config file"
    % sketchbook_path
)

arduino_builder = os.path.join(arduino_path, "arduino-builder")
hardware_path = os.path.join(arduino_path, "hardware")
lib_path_default = os.path.join(arduino_path, "libraries")
additional_lib_path = os.path.join(sketchbook_path, "libraries")
tools_path = os.path.join(arduino_path, "tools-builder")
output_dir = os.path.join(root_output_dir, "build" + build_id)
log_file = os.path.join(output_dir, "build_result.log")

# Ouput directory path
bin_dir = "binaries"
std_dir = "std_folder"

# Default
sketch_default = os.path.join(
    arduino_path, "examples", "01.Basics", "Blink", "Blink.ino"
)
exclude_file_default = os.path.join("conf", "exclude_list.txt")

# List
sketch_list = []
board_list = []
exclude_list = []

# Counter
nb_build_total = 0
nb_build_passed = 0
nb_build_failed = 0


# Create a folder if not exists
def createFolder(folder):
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
    except OSError:
        print("Error: Creating directory. " + folder)


# Delete targeted folder recursively
def deleteFolder(folder):
    if os.path.isdir(folder):
        shutil.rmtree(folder, ignore_errors=True)


def cat(file):
    with open(file, "r") as f:
        print(f.read())


# Create the output file
def create_output_log_file():
    with open(log_file, "w") as file:
        file.write("************************************** \n")
        file.write("*********** OUTPUT / RESULT ********** \n")
        file.write("************************************** \n")
        file.write(time.strftime("%A %d %B %Y %H:%M:%S "))
        file.write("\nFull path = {} \n".format(os.path.abspath(output_dir)))


def manage_exclude_list(file):
    global exclude_list
    global sketch_list
    with open(file, "r") as f:
        for line in f.readlines():
            ino = line.rstrip()
            exclude_list.append(ino)
    if exclude_list:
        for pattern in exclude_list:
            regex = ".*(" + pattern + ").*"
            for s in reversed(sketch_list):
                x = re.match(regex, s, re.IGNORECASE)
                if x:
                    sketch_list.remove(x.group(0))


# Manage sketches list
def manage_inos():
    global sketch_list
    global exclude_list
    # Find all inos or all patterned inos
    if args.all or args.sketches:
        sketch_list = find_inos()
        if args.exclude:
            assert os.path.exists(args.exclude), "Exclude list file does not exist"
            manage_exclude_list(args.exclude)
        elif os.path.exists(exclude_file_default):
            manage_exclude_list(exclude_file_default)
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
    # Default ino to build
    else:
        sketch_list = [sketch_default]
    assert len(sketch_list), "No sketch to build!"


# Find all .ino files
def find_inos():
    inoList = []
    for root, dirs, files in os.walk(arduino_path, followlinks=True):
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
    assert len(board_list), "No board found!"
    return sorted(board_list)


# Check the status
def check_status(status, board_name, sketch_name, boardOk, boardKo):
    global nb_build_passed
    global nb_build_failed
    global nb_build_total
    stderr_file = os.path.join(
        output_dir, board_name, std_dir, sketch_name + "_stderr.txt"
    )
    nb_build_total += 1
    if status == 0:
        print("SUCESS")
        boardOk.append(board_name)
        if args.bin:
            bin_copy(board_name, sketch_name)
        nb_build_passed += 1
    elif status == 1:
        print("FAILED")
        boardKo.append(board_name)
        if args.travis:
            cat(stderr_file)
        nb_build_failed += 1
    else:
        print("Error ! Check the run_command exit status ! Return code = " + status)


# Log sketch build result
def log_sketch_build_result(sketch, boardOk, boardKo):
    with open(log_file, "a") as f:
        f.write("\nSketch : " + sketch)
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
                f.write(str(b) + "\n")
        f.write(
            "\nTotal build FAILED for this sketch : {} / {}\n".format(
                len(boardKo), len(board_list)
            )
        )


# Log final result
def log_final_result():
    with open(log_file, "a") as f:
        f.write("\n****************** PROCESSING COMPLETED ******************\n")
        f.write(
            "TOTAL PASSED : {} % \n".format(nb_build_passed * 100.0 / nb_build_total)
        )
        f.write(
            "TOTAL FAILED : {} % \n".format(nb_build_failed * 100.0 / nb_build_total)
        )
        f.write("Logs are available here: " + output_dir)
    print("\n****************** PROCESSING COMPLETED ******************")
    print(
        "PASSED = {}/{} ({}%) ".format(
            nb_build_passed,
            nb_build_total,
            round(nb_build_passed * 100.0 / nb_build_total),
        )
    )
    print(
        "FAILED = {}/{} ({}%) ".format(
            nb_build_failed,
            nb_build_total,
            round(nb_build_failed * 100.0 / nb_build_total),
        )
    )
    print("Logs are available here: " + output_dir)


# Create a "bin" directory for each board and copy all binary files
# from the builder output directory into it
def bin_copy(board_name, sketch_name):
    board_bin = os.path.join(output_dir, board_name, bin_dir)
    createFolder(board_bin)
    binfile = os.path.join(build_output_dir, sketch_name + ".bin")
    try:
        shutil.copy(binfile, os.path.abspath(board_bin))
    except OSError as e:
        print(
            "Impossible to copy the binary from the arduino builder output: "
            + e.strerror
        )
        raise


# Set up specific options to customise arduino builder command
def set_varOpt(board):
    var_type_default = board[0]
    var_num_default = board[1]
    upload_method_default = "STLink"
    serial_mode_default = "generic"
    option_default = "osstd"
    variantOption = "STM32:stm32:{var_type}:pnum={var_num}".format(
        var_type=var_type_default, var_num=var_num_default
    )
    variantOption += ",upload_method={upload_method}".format(
        upload_method=upload_method_default
    )
    variantOption += ",xserial={serial_mode},opt={option}".format(
        serial_mode=serial_mode_default, option=option_default
    )

    return variantOption


# Create arduino builder command
def create_command(board, sketch_path):
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
    cmd.append(lib_path_default)
    cmd.append("-libraries")
    cmd.append(additional_lib_path)
    cmd.append("-fqbn")
    cmd.append(set_varOpt(board))
    cmd.append("-ide-version=10805")
    cmd.append("-build-path")
    cmd.append(build_output_dir)
    cmd.append("-warnings=all")
    if args.verbose:
        cmd.append("-verbose")
    cmd.append(sketch_path)
    return cmd


# Automatic run
def build_all():
    create_output_log_file()
    sketch_nb = 0
    for sketch in sketch_list:
        boardOk = []
        boardKo = []
        bord_nb = 0
        sketch_nb += 1
        sketch_name = os.path.basename(sketch)
        print(
            "\nRUNNING : {} ({}/{}) ".format(sketch_name, sketch_nb, len(sketch_list))
        )
        print("Sketch path : " + sketch)
        for board in board_list:
            board_name = board[1]
            bord_nb += 1
            sys.stdout.write(
                "Build {} ({}/{})... ".format(board_name, bord_nb, len(board_list))
            )
            sys.stdout.flush()

            command = create_command(board, sketch)
            build(command, board_name, sketch_name, boardOk, boardKo)
        log_sketch_build_result(sketch, boardOk, boardKo)
    log_final_result()


# Run arduino builder command
def build(cmd, board_name, sketch_name, boardOk, boardKo):
    boardstd = os.path.join(
        output_dir, board_name, std_dir
    )  # Board specific folder that contain stdout and stderr files
    createFolder(boardstd)
    stddout_name = sketch_name + "_stdout.txt"
    stdderr_name = sketch_name + "_stderr.txt"
    with open(os.path.join(boardstd, stddout_name), "w") as stdout, open(
        os.path.join(boardstd, stdderr_name), "w"
    ) as stderr:
        res = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
        res.wait()
        check_status(res.returncode, board_name, sketch_name, boardOk, boardKo)


# Parser
parser = argparse.ArgumentParser(
    description="Manage arduino-builder command line tool for compiling\
    Arduino sketch(es)."
)

g0 = parser.add_mutually_exclusive_group()
g0.add_argument("-l", "--list", help="list of available board(s)", action="store_true")
g0.add_argument(
    "-a",
    "--all",
    help="build all sketches found for all available boards",
    action="store_true",
)
parser.add_argument(
    "-b",
    "--board",
    metavar="pattern",
    help="pattern to find one or more board(s) to build",
)
parser.add_argument(
    "-c",
    "--clean",
    help="clean output directory by deleting %s folder" % root_output_dir,
    action="store_true",
)
parser.add_argument(
    "-v", "--verbose", help="enable arduino-builder verbose mode", action="store_true"
)

g1 = parser.add_mutually_exclusive_group()
g1.add_argument("--bin", help="save binaries", action="store_true")
g1.add_argument(
    "--travis", help="Custom configuration for Travis CI build", action="store_true"
)

# Sketch options
sketchg0 = parser.add_argument_group(
    title="Sketch(es) options", description="By default build %s" % sketch_default
)

sketchg1 = sketchg0.add_mutually_exclusive_group()
sketchg1.add_argument(
    "-i", "--ino", metavar="filepath", help="single ino file to build"
)
sketchg1.add_argument(
    "-f", "--file", metavar="filepath", help="file containing list of sketches to build"
)
sketchg1.add_argument(
    "-s",
    "--sketches",
    metavar="pattern",
    help="pattern to find one or more sketch to build",
)
sketchg1.add_argument(
    "-e",
    "--exclude",
    metavar="filepath",
    help="file containing pattern of sketches to ignore.\
    Default path : %s"
    % os.path.join(script_path, exclude_file_default),
)

args = parser.parse_args()

# Clean previous build results
if args.clean:
    deleteFolder(root_output_dir)

# List boards available
if args.list:
    find_board()
    print("%i board(s) available" % len(board_list))
    for b in board_list:
        print(b[1])
    quit()

# Create output folders
createFolder(build_output_dir)
createFolder(output_dir)

manage_inos()
find_board()

# Run builder
build_all()

# Remove build output
deleteFolder(build_output_dir)

if args.travis:
    if nb_build_failed:
        sys.exit(1)
