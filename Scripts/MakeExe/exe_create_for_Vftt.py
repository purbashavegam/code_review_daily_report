# "D:\\vegam_projects\\GIT_works\\Vegam_Analytics\\SourceCode\\app\\logs\\vAnalytics_"

import subprocess
import os
import sys

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, None, str(e)

# def resource_path(relative_path):
#     if hasattr(sys, '_MEIPASS'):
#         return os.path.join(sys._MEIPASS, relative_path)
#
#     return os.path.join(os.path.abspath("."), relative_path)


def resource_path(relative_path): # Executable is running as a bundled executable
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    # return os.path.join(os.path.abspath("."), relative_path.lstrip('.\\'))
    return os.path.join(os.path.abspath("../../Software/src"), relative_path)

def make_exe(script_path, output_dir):
    # Use resource_path to locate the JSON file
    FILE_PATH = resource_path("../../Software/src/Vegam_MQTT.json")#("../../Vegam_Analytics/SourceCode/mqtt/Vegam_MQTT.json")
    #("D://vegam_projects//GIT_works//Vegam_Analytics//SourceCode//mqtt//Vegam_MQTT.json")#("../SourceCode/mqtt/Vegam_MQTT.json")
    print(FILE_PATH,"<-----------line no 29")
    additional_files = [(FILE_PATH, ".")]

    additional_files_arg = ":".join([f"{src}{os.pathsep}{dst}" for src, dst in additional_files])
    command = f'pyinstaller --onefile --distpath {output_dir} --add-data "{additional_files_arg}" {script_path}'
    print(command)
    return execute_command(command)

if __name__ == "__main__":
    script_path = "class_structure_velo_fft.py"
    output_dir = "D://vegam_projects//GIT_works//Vegam_Analytics//MakeExe//exe_for_vfft"

    returncode, stdout, stderr = make_exe(script_path, output_dir)

    if returncode == 0:
        print("Exe creation successful")
    else:
        print("Exe creation failed")
        print("Stdout:", stdout)
        print("Stderr:", stderr)



# '''path will be : C:\Users\purba\AppData\Local\Temp\_MEI195122\Vegam_MQTT.json for my local
#
# for exe creation: you should create it in the path where app main file is placed, so this file is in the same path of where
# class_velo_fft is placed , and dependency file also will be in same path.
# --add-data file path, so mqtt json file is also here placed
# do not delete these'''