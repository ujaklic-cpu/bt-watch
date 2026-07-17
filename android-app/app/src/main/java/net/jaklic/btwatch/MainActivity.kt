package net.jaklic.btwatch

import android.Manifest
import android.content.Intent
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.lifecycle.lifecycleScope
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.core.content.ContextCompat
import kotlinx.coroutines.launch
import kotlinx.coroutines.flow.first
import net.jaklic.btwatch.ui.LogScreen
import net.jaklic.btwatch.ui.SettingsScreen

class MainActivity : ComponentActivity() {

    private val vm: SettingsViewModel by viewModels()

    private val requestPerms = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { grants ->
        val denied = grants.filterValues { granted -> !granted }.keys
        val scannerPermissionsDenied = denied - Manifest.permission.POST_NOTIFICATIONS
        if (scannerPermissionsDenied.isNotEmpty()) {
            Logs.add("Bluetooth scanning permissions denied: ${scannerPermissionsDenied.joinToString()}")
        } else {
            if (Manifest.permission.POST_NOTIFICATIONS in denied) {
                Logs.add("Notifications denied; Android may hide scanner status")
            }
            lifecycleScope.launch {
                if (vm.state.first().autoStart) startScannerService()
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val permissions = mutableListOf(Manifest.permission.ACCESS_FINE_LOCATION)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            permissions += Manifest.permission.BLUETOOTH_SCAN
            permissions += Manifest.permission.BLUETOOTH_CONNECT
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions += Manifest.permission.POST_NOTIFICATIONS
        }
        requestPerms.launch(permissions.toTypedArray())

        setContent {
            val settings by vm.state.collectAsState(initial = Settings())
            val nav = rememberNavController()

            MaterialTheme {
                NavHost(navController = nav, startDestination = "settings") {
                    composable("settings") {
                        SettingsScreen(
                            settings = settings,
                            onSave = { hub, host, loc, targets, autostart ->
                                lifecycleScope.launch { vm.save(hub, host, loc, targets, autostart) }
                            },
                            onStart = ::startScannerService,
                            onStop = { stopService(Intent(this@MainActivity, ScanService::class.java)) },
                            onShowLog = { nav.navigate("log") }
                        )
                    }
                    composable("log") {
                        LogScreen(onBack = { nav.popBackStack() })
                    }
                }
            }
        }
    }

    private fun startScannerService() {
        ContextCompat.startForegroundService(this, Intent(this, ScanService::class.java))
    }
}
