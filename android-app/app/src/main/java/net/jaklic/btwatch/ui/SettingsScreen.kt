package net.jaklic.btwatch.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.unit.dp
import net.jaklic.btwatch.Settings

@Composable
fun SettingsScreen(
    settings: Settings,
    onSave: (String, String, String, String, Boolean) -> Unit,
    onStart: () -> Unit,
    onStop: () -> Unit,
    onShowLog: () -> Unit
) {
    var hub by remember(settings.hubUrl) { mutableStateOf(TextFieldValue(settings.hubUrl)) }
    var hostId by remember(settings.hostId) { mutableStateOf(TextFieldValue(settings.hostId)) }
    var hostLoc by remember(settings.hostLocation) { mutableStateOf(TextFieldValue(settings.hostLocation)) }
    var targets by remember(settings.targets) { mutableStateOf(TextFieldValue(settings.targets)) }
    var autoStart by remember(settings.autoStart) { mutableStateOf(settings.autoStart) }

    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        OutlinedTextField(hub, { hub = it }, label = { Text("Hub URL") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(hostId, { hostId = it }, label = { Text("HOST_ID") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(hostLoc, { hostLoc = it }, label = { Text("HOST_LOCATION") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(targets, { targets = it }, label = { Text("Target MACs (comma)") }, modifier = Modifier.fillMaxWidth())
        Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
            Checkbox(checked = autoStart, onCheckedChange = { autoStart = it })
            Text("Auto-start scanning on app launch")
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(onClick = {
                onSave(
                    hub.text.trim(),
                    hostId.text.trim(),
                    hostLoc.text.trim(),
                    targets.text.trim(),
                    autoStart
                )
            }) { Text("Save") }
            Button(onClick = onStart) { Text("Start") }
            OutlinedButton(onClick = onStop) { Text("Stop") }
        }
        OutlinedButton(onClick = onShowLog) { Text("View log") }
    }
}
