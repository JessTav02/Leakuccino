import csv
import shutil
import sys
import os

import pandas as pd

# funzioni per makeReportFiles.py

# Funzione per convertire gli hprof nel formato Eclipse MAT
def convert_hprof(hprof_to_convert):
    if os.name == 'nt' or os.name == 'posix':
        if hprof_to_convert.endswith(".hprof"):
            input_file = hprof_to_convert
            output_file = hprof_to_convert.replace(".hprof", "_conv.hprof")
            cmd = f"hprof-conv {input_file} {output_file}"
            os.system(cmd)
            return output_file
        else:
            raise ValueError("Input file does not end with .hprof")
    else:
        raise ValueError("convert_hprof function is not available for your os.")

# Funzione che effettua la differenza degli hprof attraverso HprofAnalyzer.jar
def make_difference(destination_path, package, a_name, num_rot):
    hprof_b = destination_path + package + "_before_" + a_name + "_conv.hprof"
    hprof_a = destination_path + package + "_" + num_rot + "_after_" + a_name + "_conv.hprof"
    hprof_agc = destination_path + package + "_afterGC_" + a_name + "_conv.hprof"
    # Checking if the necessary files exist and have size > 0.
    cond1 = os.path.isfile(hprof_a) and os.path.getsize(hprof_a) > 0
    cond2 = os.path.isfile(hprof_agc) and os.path.getsize(hprof_agc) > 0
    cond3 = os.path.isfile(hprof_b) and os.path.getsize(hprof_b) > 0
    try:
        if (cond1 and cond2 and cond3):
            cmd = "java -jar Utils/HprofAnalyzer.jar " + package + " " + hprof_agc + " " + hprof_b  # Differenza afterGC-before
            os.system(cmd)
            cmd = "java -jar Utils/HprofAnalyzer.jar " + package + " " + hprof_a + " " + hprof_b  # Differnza after-before
            os.system(cmd)

            # Scrivi i risultati delle differenze su file CSV (modifica secondo necessità)
            csv_file1 = ("Difference_snapshot_Results_" + package + "_" + a_name + "_" + package + "_" + num_rot +
                         "_after_" + a_name + "_conv.csv")
            csv_file2 = ("Difference_snapshot_Results_" + package + "_" + a_name + "_" + package + "_AfterGC_"
                         + a_name + "_conv.csv")
            # Copia i file CSV generati (assumendo che siano prodotti da jhat o da un'altra parte)
            shutil.copyfile(csv_file1, destination_path + "Difference_After.csv")
            shutil.copyfile(csv_file2, destination_path + "Difference_AfterGC.csv")
            os.remove(csv_file1)
            os.remove(csv_file2)
        else:
            print("File .hprof non esistono o hanno dimensione < 0")
    except:
        print("[ERROR MAKING DIFFERENCE] Unexpected error:" + str(sys.exc_info()[0]))

def makeAfterGC_CSV(package, activity):
    if (os.path.isdir("Results/" + str(
            package) + "/" + activity + "/")):  # Se c'è una cartella risultato dell'activity.
        hprof_file = "Results/" + str(package) + "/" + activity + "/" + str(package) + "_afterGC_" + str(
            activity) + "_conv.hprof"
        if (os.path.isfile(hprof_file)):
            cmd = "java -jar Utils/HprofAnalyzer.jar " + package + " " + hprof_file
            os.system(cmd)
            destination_path = "Results/" + str(package) + "/" + activity + "/"
            csv_file = "Histogram_snapshot_Results_" + str(package) + "_" + str(activity) + "_" + str(
                package) + "_afterGC_" + str(activity) + "_conv.csv"
            shutil.move(csv_file,
                        destination_path + str(package) + "_AfterGC_" + str(activity) + "_conv.csv")

def makeBefore_CSV(package, activity):
    if (os.path.isdir("Results/" + str(
            package) + "/" + activity + "/")):  # Se c'è una cartella risultato dell'activity.
        hprof_file = "Results/" + str(package) + "/" + activity + "/" + str(package) + "_before_" + str(
            activity) + "_conv.hprof"
        if (os.path.isfile(hprof_file)):
            cmd = "java -jar Utils/HprofAnalyzer.jar " + package + " " + hprof_file
            os.system(cmd)
            destination_path = "Results/" + str(package) + "/" + activity + "/"
            csv_file = "Histogram_snapshot_Results_" + str(package) + "_" + str(activity) + "_" + str(
                package) + "_before_" + str(activity) + "_conv.csv"
            shutil.move(csv_file,
                        destination_path + str(package) + "_0_before_" + str(activity) + "_conv.csv")

def makeAfter_CSV(package, activity, num_rot):
    if (os.path.isdir("Results/" + str(
            package) + "/" + activity + "/")):  # Se c'è una cartella risultato dell'activity.
        hprof_file = "Results/" + str(package) + "/" + activity + "/" + str(package) + f"_{num_rot}_after_" + str(
            activity) + "_conv.hprof"
        if (os.path.isfile(hprof_file)):
            cmd = "java -jar Utils/HprofAnalyzer.jar " + package + " " + hprof_file
            os.system(cmd)
            destination_path = "Results/" + str(package) + "/" + activity + "/"
            csv_file = "Histogram_snapshot_Results_" + str(package) + "_" + str(activity) + "_" + str(
                package) + f"_{num_rot}_after_" + str(activity) + "_conv.csv"
            shutil.move(csv_file,
                        destination_path + str(package) + f"_{num_rot}_after_" + str(activity) + "_conv.csv")

# Function used by AndroLeak.py to create its final Report
def makeAndroLeakReport(numActivities, numCrashedActivities):
    listfiles = os.listdir("Results/")
    rows = []

    for f in listfiles:
        package = f.split("_")[0]
        if os.path.isdir("Results/" + f):
            ReportFile = "Results/" + f + "/LeakingReport.csv"
            num_activities = numActivities
            num_crashed_activities = numCrashedActivities
            num_leaked_activities = 0
            shallow_heap_total = 0
            retained_size_total = 0
            instance_total = 0

            tested_activities = max(0, num_activities - num_crashed_activities)

            # Legge LeakingReport.csv
            if os.path.isfile(ReportFile):
                with open(ReportFile, 'r') as open_file:
                    file_lines = open_file.readlines()
                    if len(file_lines) > 1:
                        second_line = file_lines[1].strip()
                        if "The application has no leaks!" not in second_line:
                            parts = second_line.split(';')
                            if len(parts) >= 3:
                                num_leaked_activities = int(parts[0])
                                shallow_heap_total = int(parts[1])
                                retained_size_total = int(parts[2])
                        for line in file_lines[2:]:
                            if "class" in line:
                                fields = line.strip().split(';')
                                if len(fields) >= 2:
                                    try:
                                        instance_total += int(fields[1])
                                    except:
                                        pass

            # Costruisci riga finale
            row = [
                package,
                num_activities,
                tested_activities,
                num_leaked_activities,
                shallow_heap_total,
                retained_size_total,
                instance_total
            ]
            rows.append(row)

    # Intestazioni delle colonne
    df = pd.DataFrame(rows, columns=[
        "APK", "Activities", "Tested Activities", "Leaked Activities",
        "Total Shallow Heap", "Total Retained Size", "Total Instance Number"
    ])

    # Salva CSV (compatibile con Excel, usa ; come separatore per sistemi EU)
    try:
        df.to_csv("Results/AndroLeakReport.csv", index=False, sep=';')
        print("AndroLeakReport.csv generato correttamente.")
    except:
        print("Errore scrivendo AndroLeakReport.csv:")
        raise


# Controlla se nel dump before ci sono 0 istanze di quella classe. Utile per evitare falsi positivi.
def hasZeroIstancesInBeforeDump(class_to_check,CSV_BeforeDump):
    result = False
    with open(CSV_BeforeDump) as csvfile: # Open the CSV file
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        next(spamreader, None)  # skip the headers
        for row in spamreader: # For each row
            class_name = row[0]
            num_objs = int(row[1]) #Getting instance number
            if class_name == class_to_check:
                if num_objs == 0:
                    result = True
        return result

# Function used by ScriptADB.py to create its final report
def makeLeakingReport(package):
    APKhasLeaked = False
    listfiles = os.listdir("Results/" + package)

    LeakedLog = []  # Per LeakingReport.csv
    ActivityLeakedLog = []  # Per ActivityReport.csv

    numLeakedActivity = 0
    ShallowHeapTotal = 0
    RetainedSizeTotal = 0
    numActivityNoLeaked = 0

    for f in listfiles:
        activity_path = f"Results/{package}/{f}"
        if os.path.isdir(activity_path):
            CSVfile = f"{activity_path}/Difference_AfterGC.csv"
            CSVfile_before = f"{activity_path}/{package}_0_before_{f}_conv.csv"

            if (os.path.isfile(CSVfile) and os.path.isfile(CSVfile_before)):
                with open(CSVfile) as csvfile:  # Open the CSV file
                    ActivityhasLeaked = "False"
                    ActivityShallowHeap = 0
                    ActivityTotalHeap = 0
                    spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
                    for row in spamreader:  # For each row
                        class_name = row[0]
                        num_objs = int(row[1])  # Getting instance number
                        shallow_heap = int(row[2])
                        retained_size = int(row[3])
                        if (num_objs > 0 and not hasZeroIstancesInBeforeDump(class_name,
                                                                             CSVfile_before)):  # if num_obj is >0 there is a Memory Leak
                            ActivityShallowHeap = ActivityShallowHeap + shallow_heap
                            ActivityTotalHeap = ActivityTotalHeap + retained_size
                            if (ActivityhasLeaked == "False"):  # If is the first Memory Leak...
                                LeakedLog.append("--- " + f + " has leaked ---")  # logging this information
                                LeakedLog.append("Class Name,Istance Number,Shallow Heap,Retained Size")
                                numLeakedActivity = numLeakedActivity + 1
                                ActivityhasLeaked = "True"
                                APKhasLeaked = "True"
                            LeakedLog.append(class_name + "," + str(num_objs) + "," + str(shallow_heap) + "," + str(
                                retained_size))  # appending the leaked row
                            ShallowHeapTotal = ShallowHeapTotal + shallow_heap
                            RetainedSizeTotal = RetainedSizeTotal + retained_size
                    if (ActivityhasLeaked == "True"):
                        ActivityLeakedLog.append([f, ActivityShallowHeap, ActivityTotalHeap])
                    elif (ActivityhasLeaked == "False"):
                        numActivityNoLeaked = numActivityNoLeaked + 1;
    print("\n=== Leaked Log ===")
    for line in LeakedLog:
        print(line)

    print("\n=== Activity Leaked Log ===")
    for line in ActivityLeakedLog:
        print(line)

    # Scrittura LeakingReport.csv
    try:
        leaking_path = f"Results/{package}/LeakingReport.csv"
        if APKhasLeaked == "True":
            leaked_sections = []
            current_activity = ""
            detailed_entries = []

            for line in LeakedLog:
                if isinstance(line, str) and line.startswith("---") and "has leaked" in line:
                    if current_activity and detailed_entries:
                        leaked_sections.append((current_activity, detailed_entries))
                    current_activity = line.strip()
                    detailed_entries = []
                elif isinstance(line, str) and line.startswith("Class Name"):
                    continue
                else:
                    detailed_entries.append(line.split(","))

            if current_activity and detailed_entries:
                leaked_sections.append((current_activity, detailed_entries))

            rows = []
            rows.append(["Activity Leaked", "Total Shallow Heap", "Total Retained Size"])
            rows.append([numLeakedActivity, ShallowHeapTotal, RetainedSizeTotal])
            for activity, entries in leaked_sections:
                rows.append([])
                rows.append([activity])  # --- Name has leaked ---
                rows.append(["Class Name", "Instance Number", "Shallow Heap", "Retained Size"])
                rows.extend(entries)

            df = pd.DataFrame(rows)
            df.to_csv(leaking_path, index=False, header=False, sep=";")
        else:
            pd.DataFrame([["The application has no leaks!"]]).to_csv(leaking_path, index=False, header=False, sep=";")
    except:
        print("Unexpected error writing LeakingReport.txt")
        raise

    # Scrittura ActivityReport.csv e .xlsx
    try:
        activity_path = "Results/" + package + "/ActivityReport.csv"
        if APKhasLeaked == "True":
            # Creiamo il DataFrame con le colonne desiderate
            df_activity = pd.DataFrame(ActivityLeakedLog,
                                       columns=["Activity", "Total Shallow Heap", "Total Retained Size"])
            df_activity.to_csv(activity_path, index=False, sep=";")
        else:
            pd.DataFrame([["The application has no leaks! No Leak Activities are", numActivityNoLeaked]]) \
                .to_csv(activity_path, index=False, header=False)
    except Exception as e:
        print("Unexpected error writing ActivityReport.txt")
        raise