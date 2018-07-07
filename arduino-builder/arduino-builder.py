# -*- coding: utf-8 -*-

# File name            : arduino-builder.py
# Author               : Angela RANDOLPH <angela.randolph@reseau.eseo.fr>
# Other contributors   : Frederic PILLON <frederic.pillon@st.com>
# Created              : 26/04/2018
# Python Version       : >= 3.2 (due to concurrent.futures usage)

# Description         : Used to build sketch(es) thanks to Arduino Builder
#                       See https://github.com/arduino/arduino-builder
import os
import re
import sys
import json
import time
import shutil
import subprocess
import tempfile
import argparse
from datetime import timedelta
import concurrent.futures


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
        "Please set your configuration in '{}' file".format(
            os.path.join(script_path, config_filename)
        )
    )
    config_file = open(config_filename, "w")
    if sys.platform.startswith("win32"):
        print("Default config set for Windows environment.")
        arduino_path = "C:\\Program Files (x86)\\Arduino"  # arduino default path
        arduino_packages = home + "\\AppData\\Local\\Arduino15\\packages"  # Windows 7
        arduino_user_sketchbook = home + "\\My Documents\\Arduino"
        # Windows 7 temporary directory using by arduino builder
        build_output_dir = tempdir + "\\temp_arduinoBuilderOutput"
        root_output_dir = home + "\\arduinoBuilderOutput"  # output directory
    elif sys.platform.startswith("linux"):
        print("Default config set for Linux environment.")
        arduino_path = home + "/Documents/arduino-1.8.5"
        arduino_packages = home + "/.arduino15/packages"
        arduino_user_sketchbook = home + "/Documents/Arduino"
        build_output_dir = tempdir + "/temp_arduinoBuilderOutput"
        root_output_dir = home + "/Documents/arduinoBuilderOutput"
    elif sys.platform.startswith("darwin"):
        print("Default config set for Mac OSX environment.")
        arduino_path = home + "/Applications/Arduino/"
        arduino_packages = home + "/Library/Arduino15/packages"
        arduino_user_sketchbook = home + "/Documents/Arduino"
        build_output_dir = tempdir + "/temp_arduinoBuilderOutput"
        root_output_dir = home + "/Documents/arduinoBuilderOutput"
    else:
        print("Platform unknown.")
        arduino_path = "<Set Arduino install path>"
        arduino_packages = "<Set Arduino packages install path>"
        arduino_user_sketchbook = "<Set the user sketchbook location>"
        build_output_dir = "<Set arduino builder temporary folder install path>"
        root_output_dir = "<Set your output directory path>"
    config_file.write(
        json.dumps(
            {
                "ARDUINO_PATH": arduino_path,
                "ARDUINO_PACKAGES": arduino_packages,
                "ARDUINO_USER_SKETCHBOOK": arduino_user_sketchbook,
                "BUILD_OUPUT_DIR": build_output_dir,
                "ROOT_OUPUT_DIR": root_output_dir,
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
arduino_user_sketchbook = config["ARDUINO_USER_SKETCHBOOK"]
build_output_dir = config["BUILD_OUPUT_DIR"] + build_id
root_output_dir = config["ROOT_OUPUT_DIR"]

assert os.path.exists(
    arduino_path
), "Path does not exist: {} . Please set this path in the json config file".format(
    arduino_path
)
assert os.path.exists(
    arduino_packages
), "Path does not exist: {} . Please set this path in the json config file".format(
    arduino_packages
)

assert os.path.exists(
    arduino_user_sketchbook
), "Path does not exist: {} . Please set this path in the json config file".format(
    arduino_user_sketchbook
)

arduino_builder = os.path.join(arduino_path, "arduino-builder")
arduino_hardware_path = os.path.join(arduino_path, "hardware")
arduino_lib_path = os.path.join(arduino_path, "libraries")
arduino_sketchbook_path = os.path.join(arduino_path, "examples")
arduino_user_lib_path = os.path.join(arduino_user_sketchbook, "libraries")
tools_path = os.path.join(arduino_path, "tools-builder")
output_dir = os.path.join(root_output_dir, "build" + build_id)
log_file = os.path.join(output_dir, "build_result.log")


# Ouput directory path
bin_dir = "binaries"

# Default
sketch_default = os.path.join(
    arduino_sketchbook_path, "01.Basics", "Blink", "Blink.ino"
)
exclude_file_default = os.path.join("conf", "exclude_list.txt")

# List
sketch_list = []
board_list = []  # (board type, board name)
exclude_list = []

# Counter
nb_build_passed = 0
nb_build_failed = 0

# Timing
startTime = time.time()


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


# Create the log output file and folders
def create_output_log_tree():
    # Log output file
    with open(log_file, "w") as file:
        file.write("************************************** \n")
        file.write("*********** OUTPUT / RESULT ********** \n")
        file.write("************************************** \n")
        file.write(time.strftime("%A %d %B %Y %H:%M:%S "))
        file.write("\nPath : {} \n".format(os.path.abspath(output_dir)))
    # Folders
    for board in board_list:
        createFolder(os.path.join(output_dir, board[1]))
        if args.bin:
            createFolder(os.path.join(output_dir, board[1], bin_dir))
        createFolder(os.path.join(build_output_dir, board[1]))


def manage_exclude_list(file):
    global exclude_list
    global sketch_list
    with open(file, "r") as f:
        for line in f.readlines():
            exclude_list.append(line.rstrip())
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
                    print("Ignore {} as does not exist.".format(ino))
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


# Return a list of all board types and names using the board.txt file for
# stm32 architecture
def find_board():
    for path in [arduino_packages, arduino_hardware_path]:
        for root, dirs, files in os.walk(path, followlinks=True):
            if "boards.txt" in files and "stm32" in root:
                with open(os.path.join(root, "boards.txt"), "r") as f:
                    regex = "(.+)\.menu\.pnum\.([^\.]+)="
                    for line in f.readlines():
                        x = re.match(regex, line)
                        if x:
                            if args.board:
                                reg = ".*(" + args.board + ").*"
                                if re.match(reg, x.group(0), re.IGNORECASE) is None:
                                    continue
                            # board type, board name
                            board_list.append((x.group(1), x.group(2)))
                break
    assert len(board_list), "No board found!"
    return sorted(board_list)


# Check the status
def check_status(status, build_conf, boardKo):
    global nb_build_passed
    global nb_build_failed
    sketch_name = os.path.basename(build_conf[4][-1])
    if status == 0:
        print("  --> " + build_conf[0] + " SUCESS")
        if args.bin:
            bin_copy(build_conf[0], sketch_name)
        nb_build_passed += 1
    elif status == 1:
        print("  --> " + build_conf[0] + " FAILED")
        boardKo.append(build_conf[0])
        if args.travis:
            cat(os.path.join(build_conf[3], sketch_name + ".log"))
        nb_build_failed += 1
    else:
        print("Error ! Check the run_command exit status ! Return code = " + status)


# Log sketch build result
def log_sketch_build_result(sketch, boardKo):
    with open(log_file, "a") as f:
        f.write(
            """
Sketch: {0}
Build PASSED: {1}/{2}
Build FAILED: {3}/{2}
""".format(
                sketch, len(board_list) - len(boardKo), len(board_list), len(boardKo)
            )
        )
        if len(boardKo):
            f.write("Failed boards :\n" + "\n".join(boardKo))


# Log final result
def log_final_result():
    # Also equal to len(board_list) * len(sketch_list)
    nb_build_total = nb_build_passed + nb_build_failed
    passed = "TOTAL PASSED = {}/{} ({}%) ".format(
        nb_build_passed, nb_build_total, round(nb_build_passed * 100.0 / nb_build_total)
    )
    failed = "TOTAL FAILED = {}/{} ({}%) ".format(
        nb_build_failed, nb_build_total, round(nb_build_failed * 100.0 / nb_build_total)
    )
    duration = str(timedelta(seconds=time.time() - startTime))
    with open(log_file, "a") as f:
        f.write("\n****************** PROCESSING COMPLETED ******************\n")
        f.write(time.strftime("%A %d %B %Y %H:%M:%S\n"))
        f.write("{}\n".format(passed))
        f.write("{}\n".format(failed))
        f.write("Logs are available here: " + output_dir)
        f.write("Build duration: " + duration)
    print("\n****************** PROCESSING COMPLETED ******************")
    print(passed)
    print(failed)
    print("Logs are available here: " + output_dir)
    print("Build duration: " + duration)


# Create a "bin" directory for each board and copy all binary files
# from the builder output directory into it
def bin_copy(board_name, sketch_name):
    try:
        shutil.copy(
            os.path.join(build_output_dir, board_name, sketch_name + ".bin"),
            os.path.abspath(os.path.join(output_dir, board_name, bin_dir)),
        )
    except OSError as e:
        print(
            "Impossible to copy the binary from the arduino builder output: "
            + e.strerror
        )
        raise


# Set up specific options to customise arduino builder command
def set_varOpt(board):
    return (
        "STM32:stm32:"
        + board[0]
        + ":pnum="
        + board[1]
        + ",upload_method=STLink,xserial=generic,opt=osstd"
    )


# Generate arduino builder basic command
def genBasicCommand(board):
    cmd = []
    cmd.append(arduino_builder)
    cmd.append("-hardware")
    cmd.append(arduino_hardware_path)
    cmd.append("-hardware")
    cmd.append(arduino_packages)
    cmd.append("-tools")
    cmd.append(tools_path)
    cmd.append("-tools")
    cmd.append(arduino_packages)
    cmd.append("-libraries")
    cmd.append(arduino_lib_path)
    cmd.append("-libraries")
    cmd.append(arduino_user_lib_path)
    cmd.append("-ide-version=10805")
    cmd.append("-warnings=all")
    if args.verbose:
        cmd.append("-verbose")
    cmd.append("-build-path")
    cmd.append(os.path.join(build_output_dir, board[1]))
    cmd.append("-fqbn")
    cmd.append(set_varOpt(board))
    cmd.append("dummy_sketch")
    return cmd


def create_build_conf_list():
    build_conf_list = []
    for idx, board in enumerate(board_list):
        build_conf_list.append(
            (
                board[1],
                idx + 1,
                len(board_list),
                os.path.join(output_dir, board[1]),
                genBasicCommand(board),
            )
        )
    return build_conf_list


# Automatic run
def build_all():
    create_output_log_tree()
    build_conf_list = create_build_conf_list()

    for sketch_nb, sketch in enumerate(sketch_list, start=1):
        boardKo = []
        print("\nBuilding : {} ({}/{}) ".format(sketch, sketch_nb, len(sketch_list)))
        # Update command with sketch to build
        for idx in range(len(build_conf_list)):
            build_conf_list[idx][4][-1] = sketch

        with concurrent.futures.ProcessPoolExecutor() as executor:
            for build_conf, res in zip(
                build_conf_list, executor.map(build, build_conf_list)
            ):
                check_status(res, build_conf, boardKo)
        log_sketch_build_result(sketch, boardKo)
    log_final_result()


# Run arduino builder command
def build(build_conf):
    cmd = build_conf[4]
    print("Build {} ({}/{})... ".format(build_conf[0], build_conf[1], build_conf[2]))
    with open(
        os.path.join(build_conf[3], os.path.basename(cmd[-1]) + ".log"), "w"
    ) as stdout:
        res = subprocess.Popen(cmd, stdout=stdout, stderr=subprocess.STDOUT)
        res.wait()
        return res.returncode


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
    help="clean output directory " + root_output_dir,
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
    title="Sketch(es) options", description="By default build " + sketch_default
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
    Default path : "
    + os.path.join(script_path, exclude_file_default),
)

args = parser.parse_args()


def main():
    if args.clean:
        deleteFolder(root_output_dir)

    find_board()
    if args.list:
        print("%i board(s) available" % len(board_list))
        for b in board_list:
            print(b[1])
        quit()

    createFolder(build_output_dir)
    createFolder(output_dir)

    manage_inos()

    build_all()

    deleteFolder(build_output_dir)

    if nb_build_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
