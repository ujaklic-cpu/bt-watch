package net.jaklic.btwatch

import android.app.Application
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import androidx.lifecycle.AndroidViewModel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Application.dataStore by preferencesDataStore("settings")

data class Settings(
    val hubUrl: String = "http://192.168.1.10:8000",
    val hostId: String = "android-probe",
    val hostLocation: String = "",
    val targets: String = "",
    val autoStart: Boolean = false
)

class SettingsViewModel(app: Application) : AndroidViewModel(app) {
    private val HUB = stringPreferencesKey("hub")
    private val HOST = stringPreferencesKey("host")
    private val LOC = stringPreferencesKey("loc")
    private val TARGETS = stringPreferencesKey("targets")
    private val AUTO = stringPreferencesKey("auto")

    val state: Flow<Settings> = app.dataStore.data.map { prefs ->
        Settings(
            hubUrl = prefs[HUB] ?: "http://192.168.1.10:8000",
            hostId = prefs[HOST] ?: "android-probe",
            hostLocation = prefs[LOC] ?: "",
            targets = prefs[TARGETS] ?: "",
            autoStart = (prefs[AUTO] ?: "false").toBoolean()
        )
    }

    suspend fun save(hub: String, host: String, loc: String, targets: String, auto: Boolean) {
        getApplication<Application>().dataStore.edit {
            it[HUB] = hub
            it[HOST] = host
            it[LOC] = loc
            it[TARGETS] = targets
            it[AUTO] = auto.toString()
        }
    }
}
