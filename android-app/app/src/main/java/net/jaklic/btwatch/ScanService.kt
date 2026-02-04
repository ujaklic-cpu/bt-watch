package net.jaklic.btwatch

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.first
import java.util.concurrent.ConcurrentLinkedQueue

class ScanService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private var api: IngestApi? = null
    private var hostId: String = "android-probe"
    private var hostLoc: String = ""
    private var targets: Set<String> = emptySet()
    private val queue = ConcurrentLinkedQueue<AdvertPayload>()

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(1, buildNotification("Starting..."))
        scope.launch { loadSettings() }
        scope.launch { poster() }
        startScan()
    }

    private suspend fun loadSettings() {
        val vm = SettingsViewModel(application)
        val s = vm.state.first()
        api = buildApi(s.hubUrl)
        hostId = s.hostId
        hostLoc = s.hostLocation
        targets = s.targets.lowercase()
            .split(",")
            .mapNotNull { it.trim().ifEmpty { null } }
            .toSet()
        Logs.add("Loaded settings hub=${s.hubUrl} host=$hostId loc=$hostLoc targets=${targets.size}")
    }

    private fun startScan() {
        val bt = (getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager).adapter
        val scanner = bt.bluetoothLeScanner ?: return
        scanner.startScan(callback)
        update("Scanning")
        Logs.add("Scan started")
    }

    private val callback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val addr = result.device?.address?.lowercase() ?: return
            if (targets.isNotEmpty() && addr !in targets) return
            val payload = AdvertPayload(
                host = hostId,
                location = hostLoc,
                address = addr,
                name = result.device.name ?: result.scanRecord?.deviceName,
                rssi = result.rssi,
                ts = System.currentTimeMillis() / 1000.0
            )
            queue.add(payload)
            Logs.add("Seen $addr rssi=${result.rssi}")
        }
    }

    private suspend fun poster() {
        while (isActive) {
            val apiLocal = api
            if (apiLocal != null) {
                while (true) {
                    val item = queue.poll() ?: break
                    try {
                        apiLocal.send(item)
                        Logs.add("Sent ${item.address} rssi=${item.rssi}")
                    } catch (_: Exception) { /* ignore */ }
                }
            }
            delay(1000)
        }
    }

    private fun update(msg: String) {
        val nm = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        nm.notify(1, buildNotification(msg))
    }

    private fun buildNotification(text: String): Notification {
        return NotificationCompat.Builder(this, "btwatch")
            .setContentTitle("BtWatch scanning")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.stat_sys_data_bluetooth)
            .setOngoing(true)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            val chan = NotificationChannel("btwatch", "BtWatch", NotificationManager.IMPORTANCE_LOW)
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).createNotificationChannel(chan)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        scope.cancel()
        val bt = (getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager).adapter
        bt.bluetoothLeScanner?.stopScan(callback)
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
