# Leakuccino

Leakuccino is a tool designed to detect whether the Activity classes of an Android application suffer from memory leaks related to the activity lifecycle.

The tool automatically executes the Double Orientation Change (DOC) test, which consists of rotating the device twice: from landscape to portrait, and back to landscape — or, alternatively, from portrait to landscape, and back to portrait. This sequence is known to be particularly prone to triggering memory leaks in Android apps.

In order to execute the tool in the experimental modality, the following steps have to be executed:
1. Create an AppsTesting/ folder in this directory.
2. Add your app code source in the AppsTesting/ directory.
3. Launch an Android Virtual Device (or real device).
4. Execute launchTest.py from the command line
5. The obtained results are in the Results folder. In details, a subfolder for each tested application and configuration will be created. The name of the folder includes information about the executed tests.

During its execution, AndroLeak creates many temporary files. They should be automatically removed at the end of the experiments, but it is possible that they remain on the disk, in some systems. In these cases, you should manually delete them via operating system utilities.
