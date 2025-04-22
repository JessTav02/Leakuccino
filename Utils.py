import shutil
import subprocess
import os
import time
import json
from datetime import datetime
from parser import read_kotlin_file, write_kotlin_file

def extract_manifest(apk_path, app_name):
    if os.path.exists(apk_path):
        print("Extracting AndroidManifest.xml")
        subprocess.call(['java', '-jar', 'Utils/apktool/apktool.jar', 'f', 'd', apk_path])
        shutil.copy(f"{app_name}/AndroidManifest.xml", os.getcwd())
    else:
        raise FileNotFoundError(f"APK {apk_path} non trovato.")

def parse_manifest():
    print("Parsing AndroidManifest.xml")
    os.system("java -jar Utils/ManifestParser.jar AndroidManifest.xml > tmpFile")
    with open("tmpFile") as f:
        tokens = f.read().split()
        package = tokens[1]
        tokens = [t for t in tokens if t not in ["PACKAGE", "ACTIVITIES", package]]
        return package, tokens

def prepare_test_utils(package, test_path):
    dir_test_path = os.path.dirname(test_path)
    destination_file = os.path.join(dir_test_path, 'TestUtils.kt')

    if not os.path.exists(destination_file):
        shutil.copy("TestUtils.kt", dir_test_path)

    lines = read_kotlin_file(destination_file)
    if lines:
        lines[0] = lines[0].replace('...', package) + '\n'
        write_kotlin_file(destination_file, lines)

def create_device_folders(activity_names):
    for activity in activity_names:
        subprocess.run(["adb", "shell", "mkdir", f"/sdcard/Download/{activity}"], capture_output=True)

def check_created_folders(activity_names):
    existing = []
    for activity in activity_names:
        result = subprocess.run(["adb", "shell", "ls", f"/sdcard/Download/{activity}"],
                                capture_output=True, text=True)
        if result.returncode == 0:
            existing.append(activity)
    return existing

def cleanup(package_dir, test_utils_path, modified_test_path):
    if os.path.exists(test_utils_path):
        os.remove(test_utils_path)
    if os.path.exists(modified_test_path):
        os.remove(modified_test_path)
    if os.path.exists("tmpFile"):
        os.remove("tmpFile")
    if os.path.exists("AndroidManifest.xml"):
        os.remove("AndroidManifest.xml")
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)

def move_download_files(parent_dir):
    # parent = r"C:\Users\jessi\Desktop\TESTING\Results\com.forz.calculator"
    # move_download_files(parent)

    download_path = os.path.join(parent_dir, "Dumpsys")

    if not os.path.isdir(download_path):
        print(f"Nessuna cartella 'Dumpsys' trovata in {parent_dir}")
        return

    for item in os.listdir(download_path):
        src_path = os.path.join(download_path, item)
        dest_path = os.path.join(parent_dir, item)

        if os.path.exists(dest_path):
            if os.path.isdir(dest_path):
                shutil.rmtree(dest_path)
            else:
                os.remove(dest_path)

        shutil.move(src_path, dest_path)

    # Elimina la cartella Download
    shutil.rmtree(download_path)
