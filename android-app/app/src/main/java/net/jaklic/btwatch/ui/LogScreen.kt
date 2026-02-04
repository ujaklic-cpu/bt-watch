package net.jaklic.btwatch.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import net.jaklic.btwatch.Logs

@Composable
fun LogScreen(onBack: () -> Unit) {
    val entries by Logs.logs.collectAsState()
    Column(modifier = Modifier.fillMaxSize()) {
        Button(onClick = onBack) { Text("Back") }
        LazyColumn {
            items(entries.takeLast(200).reversed()) { row ->
                Text(row)
            }
        }
    }
}
