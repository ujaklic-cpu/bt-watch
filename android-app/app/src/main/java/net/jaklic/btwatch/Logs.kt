package net.jaklic.btwatch

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

object Logs {
    private val _logs = MutableStateFlow<List<String>>(emptyList())
    val logs: StateFlow<List<String>> = _logs

    fun add(entry: String) {
        _logs.value = (_logs.value + entry).takeLast(500)
    }
}
