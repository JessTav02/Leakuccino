package ......

import android.app.ActivityManager
import android.content.Context
import android.content.pm.PackageManager
import android.content.res.Configuration
import android.os.Build
import android.os.Debug
import android.os.Environment
import android.util.Log
import android.widget.Toast
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.UiDevice
import java.io.BufferedReader
import java.io.File
import java.io.IOException
import java.io.InputStreamReader
import org.junit.Assert.fail

interface Functions {

    /** Estrae tutte le activity dichiarate nel Manifest.*/
    fun getManifestActivities(): Set<String>

    /** Estrae il nome dell'activity corrente */
    fun getCurrentActivityName(): String

    /** Ruota lo schermo */
    fun rotateScreen(device: UiDevice)

    /** Esegue il dump della memoria salvando i file nel device */
    fun dumpMemory(activity: String, stage: String)

    /** Funzione helper per eseguire comandi shell */
    fun executeCommand(command: String): String

    /** forza il garbage collector */
    fun garbageCollector(device: UiDevice)
}

class TestUtils : Functions {

    override fun getManifestActivities(): Set<String> {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val packageManager = context.packageManager
        val packageName = context.packageName
        val activities = mutableSetOf<String>()

        try {
            val appInfo = packageManager.getPackageInfo(packageName, PackageManager.GET_ACTIVITIES)
            appInfo.activities?.forEach {
                activities.add(it.name)
            }
        } catch (e: Exception) {
            Log.e("Test_log", "Error getting manifest activities: ", e)
        }

        println("Manifest Activities: $activities")
        return activities
    }

    override fun getCurrentActivityName(): String {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        return activityManager.appTasks[0].taskInfo.topActivity?.className ?: "Unknown Activity"
    }

    override fun rotateScreen(device: UiDevice) {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val orientation = context.resources.configuration.orientation

        if (orientation == Configuration.ORIENTATION_PORTRAIT) {
            device.setOrientationLeft() // Passa a landscape
        } else {
            device.setOrientationNatural() // Torna a portrait
        }
        Thread.sleep(1000) // Aspetta la rotazione
    }

    override fun dumpMemory(activity: String, stage: String) {
        Thread.sleep(2000)
        val packageName = "......"

        val activityName = activity.removePrefix("$packageName.")

        val fileName = "${packageName}_${stage}_${activityName}.hprof"
        Log.d("Test_log", "Nome dell'activity: $activityName")

        try {
            val dirPath = "/sdcard/Download/Dumpsys/$activityName"
            val dir = File(dirPath)
            if (!dir.exists()) {
                //throw IllegalStateException("Directory non trovata: $dirPath. Il test viene interrotto.")
                fail("Directory non trovata: $dirPath. Il test viene interrotto.")
            }
            val heapDumpPath = "$dirPath/$fileName"
            Debug.dumpHprofData(heapDumpPath)
            Log.d("Test_log", "Dump della memoria completato. File salvato in: $heapDumpPath")

        } catch (e: Exception) {
            Log.e("Test_log", "Errore durante il dump", e)
        }
    }

    override fun executeCommand(command: String): String {
        return try {
            val process = Runtime.getRuntime().exec(command)
            val reader = BufferedReader(InputStreamReader(process.inputStream))
            val output = reader.readText()
            reader.close()
            process.waitFor()
            output
        } catch (e: Exception) {
            e.printStackTrace()
            ""
        }
    }

    override fun garbageCollector(device: UiDevice) {
        val packageName = executeCommand("adb shell dumpsys window | findstr mCurrentFocus")

        Log.d("Test_log", "Garbage Collection")

        val pid = executeCommand("adb -s $device shell pidof $packageName").trim()

        if (pid.isNotEmpty()) {
            executeCommand("adb -s $device shell kill -10 $pid")
            Thread.sleep(2000)
        } else {
            Log.d("Test_log", "Errore: impossibile ottenere il PID del pacchetto $packageName")
        }
    }

}