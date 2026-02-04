package net.jaklic.btwatch

import android.Manifest
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import net.jaklic.btwatch.ui.LogScreen
import net.jaklic.btwatch.ui.SettingsScreen

class MainActivity : ComponentActivity() {

    private val vm: SettingsViewModel by viewModels()

    private val requestPerms = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { /* no-op */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestPerms.launch(
            arrayOf(
                Manifest.permission.BLUETOOTH_SCAN,
                Manifest.permission.BLUETOOTH_CONNECT,
                Manifest.permission.ACCESS_FINE_LOCATION
            )
        )

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
                            onStart = {
                                startService(Intent(this@MainActivity, ScanService::class.java))
                            },
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
}
