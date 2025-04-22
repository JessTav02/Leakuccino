import subprocess
import time

from parser import *
from Utils import *


if len(sys.argv) < 2:
    print("Uso corretto: python launchTest.py <numero_rotazioni>")
    sys.exit(1)

num_rot = int(sys.argv[1])
try:
    if num_rot not in (1, 2, 10):
        raise ValueError("Il numero di rotazioni deve essere 1, 2 o 10.")
except ValueError as ve:
    print(f"Parametro non valido: {ve}")
    sys.exit(1)

base_dir = os.getcwd()  # dir users\\jessi\\Desktop\\TESTING
app_name = input("Inserisci il nome dell'applicazione: ")
test_path_app = input("Inserisci il path del TestEspresso.kt: ")

# creazione delle sottocartelle in Dumpsys per ogni activity presente nel minefest (vedere funesdroid)
# se una activity non è stata trovata nel test espresso allora fare il lancio automatico. "adb shell am start ..."

apk_name = app_name + ".apk"
# Crea l'Android Manifest a partire dall'apk.
if os.path.exists(f"InputAPK/{apk_name}"):
    print("Extracting AndroidManifest.xml")
    subprocess.call(['java', '-jar', 'Utils/apktool/apktool.jar', 'f', 'd', f"InputAPK/{apk_name}"])
else:
    print(f"APK {apk_name} non trovato nella cartella Utils.")

# Copio il manifest nella directory corrente.
my_path = os.getcwd()
shutil.copy(f"{app_name}/AndroidManifest.xml", my_path + '/')

# Installa l'apk sul dispositivo
# print("Installing apk " + app_name)
# subprocess.call(['adb','install','-g','-r', apk_path])

os.system(
    "adb shell content insert --uri content://settings/system --bind name:s:accelerometer_rotation --bind value:i:0")

# ESTRAZIONE DELLE ACTIVITY DAL FILE MANIFEST
print("Parsing AndroidManifest.xml")
results = os.system("java -jar Utils/ManifestParser.jar AndroidManifest.xml > tmpFile")

time.sleep(15)
# Pongo adb in root state
os.system("adb root")

# Recupera le attività ed il package dal file temporaneo
f = open("tmpFile")
tokens = f.read()
tokens = tokens.split()
package= tokens[1]
tokens.remove("PACKAGE")
tokens.remove("ACTIVITIES")
tokens.remove(package)
activities = tokens
f.close()

print(activities)
numActivities = len(activities)

# Stampo informazioni utili
print("App Package: " + package)

# Torno in home e resetto (occorre iniziare gli esperimenti dalla Home).
print("App resetting")
os.system("adb shell am force-stop " + package)
os.system("adb shell input keyevent KEYCODE_HOME")

modify_package = package.replace(".", "/")
test_path = f"AppsTesting/{app_name}/{test_path_app}"
# input("Inserisci il path del test Espresso (kotlin) da modificare: ").strip()
dir_test_path = os.path.dirname(test_path)  # AppsTesting/...
test_name = os.path.basename(test_path)  # TestEspresso.kt
destination_file = os.path.join(dir_test_path, 'TestUtils.kt')

if not os.path.exists(destination_file):
    shutil.copy("TestUtils.kt", dir_test_path)
    print(f"File 'TestUtils.kt' copiato con successo nella directory {dir_test_path}")
else:
    print(f"Il file 'TestUtils.kt' esiste già nella directory {dir_test_path}.")


linesUtils = read_kotlin_file(f"{dir_test_path}/TestUtils.kt")
if linesUtils:
    # Sostituisci tutti i "......" con il nome del package in ogni riga
    linesUtils = [line.replace("......", package) for line in linesUtils]

    # Scrivi il contenuto modificato nel file
    write_kotlin_file(f"{dir_test_path}/TestUtils.kt", linesUtils)
    print(f"File 'TestUtils.kt' modificato con il package: {package}")

# creazione cartella per memorizzare i dump
if not os.path.exists(f"Results/{package}"):
    os.mkdir(f"{base_dir}/Results/{package}")
    print(f"La cartella '{package}' è stata creata.")
else:
    print(f"La cartella '{package}' esiste già.")

# mi sposto nella directory dell'app
os.chdir(f"AppsTesting/{app_name}")

log_lines = []
log_filename = f"log_{package}_{num_rot}.txt"
log_path = os.path.join(f"Results/{package}/", log_filename)


def log(msg):
    print(msg)
    log_lines.append(msg)


# 1. Crea cartella su emulatore
log("Creazione della cartella /sdcard/Download/Dumpsys...")
result = subprocess.run(
    ["adb", "shell", "mkdir", "/sdcard/Download/Dumpsys"],
    capture_output=True, text=True
)
log(result.stdout.strip())
if result.stderr:
    log("Errore mkdir: " + result.stderr.strip())

# per ogni activity presente nel file manifest creo la cartella per contenere i 3 file dump
# Crea una lista con solo i nomi delle attività
activity_names = []
for activity in activities:
    print("Nome attività: ", activity)
    if "/" in activity:
        activity = activity.split("/")[-1]  # prendi solo .ui.MainActivity
        # Rimuovi eventuale punto iniziale
    if activity.startswith("."):
        activity = activity[1:]
        # Ora rimuovi il package se è completo
    if activity.startswith(package + "."):
        relative_activity = activity[len(package) + 1:]
    else:
        relative_activity = activity
    activity_names.append(relative_activity)

print(activity_names)

for activity in activity_names:
    log(f"Creazione della cartella /sdcard/Download/Dumpsys/{activity}...")
    result = subprocess.run(
        ["adb", "shell", "mkdir", f"/sdcard/Download/Dumpsys/{activity}"],
        capture_output=True, text=True
    )
    log(result.stdout.strip())
    if result.stderr:
        log("Errore mkdir: " + result.stderr.strip())

# Controllo effettiva creazione delle cartelle
for activity in activity_names:
    check_result = subprocess.run(
        ["adb", "shell", "ls", f"/sdcard/Download/Dumpsys/{activity}"],
        capture_output=True, text=True
    )
    if check_result.returncode == 0:
        log(f"Cartella '{activity}' creata correttamente.")
    else:
        log(f"Cartella '{activity}' NON trovata.")

print("Current working directory:", os.getcwd())
# 2. Esegui parser.py
log("\nAvvio parser.py...")
if os.path.exists(f"{base_dir}/parser.py"):
    result = subprocess.run(
        ["python", f"{base_dir}/parser.py", test_path_app, f"{num_rot}"],
        capture_output=True, text=True
    )
    log(result.stdout.strip())
    if result.stderr:
        log("Errore parser.py: " + result.stderr.strip())
else:
    log(f"parser.py non trovato in {base_dir}/parser.py")

time.sleep(5)

class_name = test_name.replace(".kt", "")
new_class_name = f"Modified_{class_name}"

# 3. esecuzione del test kotlin
log("\nAvvio test Kotlin con gradle...")

cmd = ("gradlew :app:connectedAndroidTest "
       f"\"-Pandroid.testInstrumentationRunnerArguments.class={package}.{new_class_name}")

print("Inizio test sul file: " + cmd)
os.system(cmd)

os.chdir(base_dir)

# cancello i file copiati
os.remove(f"{dir_test_path}/TestUtils.kt")
os.remove(f"{dir_test_path}/{new_class_name}.kt")

time.sleep(10)

# 4. Pull della cartella Dumpsys dal dispositivo al PC
log(f"Pull della cartella Download sul PC, nella cartella Results/{package}...")
result = subprocess.run(
    ["adb", "pull", "/sdcard/Download/Dumpsys", f"Results/{package}"],
    capture_output=True, text=True
)

time.sleep(10)

log(result.stdout.strip())
if result.stderr:
    log("Errore pull: " + result.stderr.strip())


# 5. Elimina la cartella Dumpsys dal dispositivo
log(f"Eliminazione delle cartelle dal dispositivo...")
result = subprocess.run(
    ["adb", "shell", "rm", "-r", "/sdcard/Download/Dumpsys"],
    capture_output=True, text=True
)

if result.returncode == 0:
    log("Cartelle eliminata dal dispositivo.")
else:
    log("Errore durante l'eliminazione delle cartelle: " + result.stderr.strip())

# 6. Salvataggio del log
log("\nOperazione completata.")
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log(f"Fine esecuzione: {timestamp}")

with open(log_path, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

print(f"\nLog salvato in {log_path}")

os.chdir(f"Results/{package}")
# se un folder è vuoto vuol dire che quell'activity non è stata ruotate.
# controllo e prendo i nomi delle activity non ruotate.
nonRotatedActivityNames = []
for folder_name in os.listdir():
    folder_path = os.path.join(os.getcwd(), folder_name)
    if os.path.isdir(folder_path):
        if not os.listdir(folder_path):
            nonRotatedActivityNames.append(folder_name)


def keep_strings_containing_element(first_list, second_list):
    # Usa list comprehension per mantenere solo gli elementi della prima lista che contengono una stringa della seconda lista
    return [item for item in first_list if any(substring in item for substring in second_list)]


nonRotatedActivities = keep_strings_containing_element(activities, nonRotatedActivityNames)
print("\nActivity non ruotate:", nonRotatedActivities)

# mette qua il codice di lacio activity

# cancello il file tmpFile, la cartella che per estrarre l'apk
os.chdir(base_dir)
os.remove("tmpFile")
os.remove("AndroidManifest.xml")
shutil.rmtree(app_name)

move_download_files(f"Results/{package}")
"""
nonRotatedActivities = ['com.forz.calculator/.MainActivity', 'com.forz.calculator/.AboutActivity']
print(nonRotatedActivities)
# lanciare le activity che non sono state ruotate manualmente e fa i dump (funesdroid)
file_path_act = "activities.txt"
with open(file_path_act, 'w') as file:
    for activity in nonRotatedActivities:
        file.write(activity + '\n')

cmd = f"python testActivityManual.py"
os.system(cmd)
"""

time.sleep(10)
#close the emulator
os.popen("adb -s emulator-5554 emu kill")
print("Testing Accomplished!")

cmd = f"\npy makeReportFiles.py {num_rot} {package} {numActivities}"
# GENERA I REPORT (FUNESDROID)
print("Esecuzione: ", cmd)
os.system(cmd)
