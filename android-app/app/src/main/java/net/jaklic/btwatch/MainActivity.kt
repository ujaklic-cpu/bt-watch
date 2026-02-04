package net.jaklic.btwatch

import android.Manifest
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.unit.dp
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

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
            val settings by vm.state.collectAsState()
            var hub by remember { mutableStateOf(TextFieldValue(settings.hubUrl)) }
            var hostId by remember { mutableStateOf(TextFieldValue(settings.hostId)) }
            var hostLoc by remember { mutableStateOf(TextFieldValue(settings.hostLocation)) }
            var targets by remember { mutableStateOf(TextFieldValue(settings.targets)) }
            var running by remember { mutableStateOf(false) }

            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        OutlinedTextField(hub, { hub = it }, label = { Text("Hub URL") }, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(hostId, { hostId = it }, label = { Text("HOST_ID") }, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(hostLoc, { hostLoc = it }, label = { Text("HOST_LOCATION") }, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(targets, { targets = it }, label = { Text("Target MACs (comma)") }, modifier = Modifier.fillMaxWidth())
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            Button(onClick = {
                                lifecycleScope.launch {
                                    vm.save(
                                        hub.text.trim(),
                                        hostId.text.trim(),
                                        hostLoc.text.trim(),
                                        targets.text.trim()
                                    )
                                }
                            }) { Text("Save") }
                            Button(onClick = {
                                startService(Intent(this@MainActivity, ScanService::class.java))
                                running = true
                            }) { Text("Start") }
                            OutlinedButton(onClick = {
                                stopService(Intent(this@MainActivity, ScanService::class.java))
                                running = false
                            }) { Text("Stop") }
                        }
                        Text(text = "Status: ${if (running) "Running" else "Stopped"}")
                    }
                }
            }
        }
    }
}
