import csv
import shutil
import sys
import os
import time

import pandas as pd
from makeReportFilesUtils import *

# "py makeReportFiles.py num_rot package num_activities"
num_rot = sys.argv[1]
package_folder = sys.argv[2]
numActivities = int(sys.argv[3])

print("Numero di rotazioni:", num_rot)
print("Package folder:", package_folder)
print("Numero attività previste:", numActivities)


results_root = "Results"
if not os.path.exists(results_root):
    print(f"Errore: la cartella '{results_root}' non esiste.")
    sys.exit(1)

print("\n--------------------------------------")
print(f"\n[INFO] Avvio generazione report in {results_root} (SCRIPT FUNESDROID)")
print("\n--------------------------------------")

numCrashedActivities = 0
package_path = os.path.join(results_root, package_folder)
package = package_folder.split("_")[0]
print(f"\nAnalisi per package: {package}")

activity_folders = [act for act in os.listdir(package_path) if os.path.isdir(os.path.join(package_path, act))]

for activity in activity_folders:
    time.sleep(4)

    activity_path = "Results/" + package + "/" + activity + "/"
    dump_files = os.listdir(activity_path)

    if not dump_files:
        print(f"[WARNING] Cartella vuota per activity: {activity}.")
        numCrashedActivities += 1
        continue

    print("\n---------- " + activity + " ----------\n")

    activity_path = "Results/" + package + "/" + activity + "/"
    # Lista di dump disponibili
    dump_files = os.listdir(activity_path)
    for file in dump_files:
        if (
                file.startswith(f"{package}_after_") and f"_{num_rot}_after_" not in file and
                "_afterGC_" not in file
        ):
            old_path = os.path.join(activity_path, file)
            new_name = file.replace("_after_", f"_{num_rot}_after_")
            new_path = os.path.join(activity_path, new_name)
            os.rename(old_path, new_path)

    dump_files = os.listdir(activity_path)
    # Converte tutti gli hprof
    for file in dump_files:
        if file.endswith("_after_" + activity + ".hprof") and f"_{num_rot}_after_" not in file:
            old_path = os.path.join(activity_path, file)
            new_name = file.replace("_after_", f"_{num_rot}_after_")
            new_path = os.path.join(activity_path, new_name)
            os.rename(old_path, new_path)
        if file.endswith(".hprof") and not file.endswith("_conv.hprof"):
            hprof_path = os.path.join(activity_path, file)
            print(hprof_path)
            hprof_path_conv = convert_hprof(hprof_path)
            print("Generato file: ", hprof_path_conv)

    print("\nMaking Histogram")
    time.sleep(5)

    # Istogramma BEFORE
    makeBefore_CSV(package, activity)

    # Istogramma AFTER
    makeAfter_CSV(package, activity, num_rot)

    # Istogramma AfterGC
    makeAfterGC_CSV(package, activity)

    time.sleep(1)

    # Genera i file difference
    make_difference(activity_path, package, activity, num_rot)

# Report dei leak per app
makeLeakingReport(package_folder)

# Report finale aggregato
makeAndroLeakReport(numActivities, numCrashedActivities)

print("\nYou can find results in Results/ folder\n")

print("\n=================================")
print(f"[RIEPILOGO] Attività totali previste: {numActivities}")
print(f"[RIEPILOGO] Attività crashate (cartelle vuote): {numCrashedActivities}")
print(f"[RIEPILOGO] Attività analizzate correttamente: {numActivities - numCrashedActivities}")
print("=================================")

#salvo il package come package_1_doc
os.rename(f"Results/{package}", f"Results/{package}_{num_rot}_doc")
