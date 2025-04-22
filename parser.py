import os
import re
import shutil
import sys
from importlib.resources import files


def make_copy(name_file, name_new_file):
    shutil.copy(name_file, name_new_file)
    print(f"Nuovo file creato: {name_new_file}")
    return name_new_file

def read_kotlin_file(file_path):
    #Legge il contenuto di un file Kotlin.4
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.readlines()

def write_kotlin_file(file_path, lines):
    #scrive il contenuto modificato nel file kotlin
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)

def rename_class(file_path, lines):
    new_class_name = os.path.basename(file_path).replace(".kt", "")
    for i, line in enumerate(lines):
        match = re.search(r'\bclass\s+(\w+)', line)
        if match:
            old_name = match.group(1)
            lines[i] = re.sub(r'\bclass\s+\w+', f'class {new_class_name}', line, count=1)
            break  # Si ferma dopo la prima sostituzione
    return lines

def insertImportLines(package_name, package_index, lines):
    lines_to_insert = [
        f"import {package_name}.TestUtils as funUtils",
        "\n"
        "import android.widget.Button",
        "import android.util.Log",
        "import androidx.test.platform.app.InstrumentationRegistry",
        "import androidx.test.uiautomator.UiDevice",
        "import androidx.test.espresso.assertion.ViewAssertions.matches",
        "import androidx.test.espresso.matcher.ViewMatchers.isRoot",
    ]
    for new_line in reversed(lines_to_insert):
        lines.insert(package_index + 1, new_line + "\n")

def insert_lines_in_class(lines):
    lines_to_insert = [
        "\tvar utils = funUtils()",
        "\tprivate val device: UiDevice = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())",
        "\tprivate val manifestActivities = utils.getManifestActivities()",
        "\tprivate val rotatedActivities = mutableSetOf<String>()"
    ]

    class_index = found_class(lines)


    if class_index is not None:
        # Trova la posizione dove iniziano le variabili (dentro `{}` della classe)
        insert_position = class_index + 1

        while insert_position < len(lines) and lines[insert_position].strip() == "{":
            insert_position += 1

        for new_line in reversed(lines_to_insert):
            lines.insert(insert_position, new_line + "\n")

        return lines
    else:
        print("Errore: Nessuna classe trovata nel file Espresso.")

def found_class(lines):
    for i, line in enumerate(lines):
        if re.match(r'^\s*class\s+\w+', line):
            class_index = i
            return class_index
    print("No class found")
    return None

def insert_perform_action_function(lines, num_rot):

    function_start = None
    function_end = None
    inside_function = False
    bracket_count = 0
    # Trova l'inizio e la fine della prima funzione
    for i, line in enumerate(lines):
        if re.match(r'^\s*fun\s+\w+\s*\(', line) and function_start is None:
            function_start = i
            inside_function = True
            bracket_count = 0
        if inside_function:
            bracket_count += line.count("{") - line.count("}")
            if bracket_count == 0:  # Significa che la funzione è chiusa
                function_end = i
                break

    if function_end is not None:
        rotation_block = [
            "            utils.rotateScreen(device)\n"
            "            utils.rotateScreen(device)"
            for _ in range(num_rot)
        ]
        perform_action_function = [
            "\n",
            "    private fun RotateAndDump() {",
            "        val currentActivity = utils.getCurrentActivityName()",
            "        Log.d(\"Test_log\", \"Testing Activity before click: $currentActivity\")",
            "        if (manifestActivities.contains(currentActivity) && !rotatedActivities.contains(currentActivity)) {",
            "            Log.d(\"Test_log\", \"Rotating screen before clicking: $currentActivity\")",
            "            utils.dumpMemory(currentActivity, \"before\")\n",
            "            Thread.sleep(1000)\n",
        ] + rotation_block + [
            "            Thread.sleep(1000)\n",
            "            utils.dumpMemory(currentActivity, \"after\")",
            "\n"
            "            System.gc()\n"
            "\n"
            "            Thread.sleep(1000)\n"
            "            utils.dumpMemory(currentActivity, \"afterGC\")"
            "\n",
            "            rotatedActivities.add(currentActivity) // Segna questa activity come già ruotata",
            "        } else {\n",
            "            Log.d(\"Test_log\", \"Skipping rotation: $currentActivity is not in the Manifest\")",
            "        }",
            "        Thread.sleep(1000)",
            "        onView(isRoot()).check(matches(isDisplayed()))",
            "    }\n"
        ]
        lines[function_end + 1:function_end + 1] = [line + "\n" for line in perform_action_function]
    return lines

def insert_function_before_val(lines):
    new_lines = []
    pattern = re.compile(r'^\s*val\s+\w+\s*=\s*onView\s*\(')

    for line in lines:
        if pattern.match(line):
            indent = re.match(r'^(\s*)', line).group(1)
            new_lines.append(f"{indent}Thread.sleep(2000)\n")
            new_lines.append(f"{indent}RotateAndDump()\n")
        new_lines.append(line)

    return new_lines

def find_package_name(file_path, lines):
    package_name = None
    package_index = None
    for i, line in enumerate(lines):
        match = re.match(r'^\s*package\s+([\w\.]+)', line)
        if match:
            package_name = match.group(1)  # Estrae il nome del package
            print(f"Debug: Nome del package trovato: {package_name}")
            package_index = i
            break

    if package_name and package_index is not None:
        insertImportLines(package_name, package_index, lines)

    return package_name

def modify_kotlin_file(file_path, num_rot):

    lines = read_kotlin_file(file_path)

    rename_class(file_path, lines)

    find_package_name(file_path, lines)

    lines = insert_lines_in_class(lines)

    # trova le stringhe perform(click()) e perform(scrollTo(), click())
    lines = insert_function_before_val(lines)

    #aggiunge la funzione PerformActionRotateAndDump
    insert_perform_action_function(lines, num_rot)

    # Scrive le modifiche nel file
    write_kotlin_file(file_path, lines)

def prepare_and_modify_file(file_path, num_rot):
    print(f"file path: {file_path}")
    # Estrai directory e nome file
    dir_name = os.path.dirname(file_path)
    print(dir_name)
    base_name = os.path.basename(file_path)  # Es: File.kt
    print(base_name)

    # Costruisci il nuovo nome del file con prefisso Modified_
    new_base_name = f"Modified_{base_name}"
    new_file_path = os.path.normpath(os.path.join(dir_name, new_base_name))

    print(f"file path: {new_file_path}")

    # Crea la copia del file
    make_copy(file_path, new_file_path)

    # Passa il nuovo file alla funzione che fa le modifiche
    modify_kotlin_file(new_file_path, num_rot)

    print(f"File modificato creato: {new_file_path}")


# ESEMPIO DI UTILIZZO
if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Errore: specificare il percorso del file Kotlin da modificare e il numero di rotazioni (1,2,10).")
        sys.exit(1)

    file_path = sys.argv[1]
    num_rot = int(sys.argv[2])
    prepare_and_modify_file(file_path, num_rot)
    print("Modifica del file kotlin completata!")

