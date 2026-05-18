package com.learnwords.app.utils

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import com.learnwords.app.data.ai.OllamaConfig
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "learnwords_prefs")

class PreferencesManager(private val context: Context) {

    companion object {
        val KEY_USER_ID = stringPreferencesKey("user_id")
        val KEY_SERVER_URL = stringPreferencesKey("server_url")
        val KEY_USERNAME = stringPreferencesKey("username")
        val KEY_LAST_SYNC = longPreferencesKey("last_sync_ts")
        val KEY_TIMER_SECONDS = longPreferencesKey("timer_seconds")
        val KEY_TIMER_DATE = stringPreferencesKey("timer_date")
        val KEY_SELECTED_LANGS = stringPreferencesKey("selected_langs")
        val KEY_OLLAMA_URL = stringPreferencesKey("ollama_url")
        val KEY_OLLAMA_MODEL = stringPreferencesKey("ollama_model")
        val KEY_IS_ADMIN = booleanPreferencesKey("is_admin")
        val KEY_AUTH_METHOD = stringPreferencesKey("auth_method")
    }

    val userId: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_USER_ID] ?: ""
    }

    val serverUrl: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_SERVER_URL] ?: ""
    }

    val username: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_USERNAME] ?: ""
    }

    val authMethod: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_AUTH_METHOD] ?: ""
    }

    val lastSyncTs: Flow<Long> = context.dataStore.data.map { prefs ->
        prefs[KEY_LAST_SYNC] ?: 0L
    }

    val timerSeconds: Flow<Long> = context.dataStore.data.map { prefs ->
        prefs[KEY_TIMER_SECONDS] ?: 0L
    }

    val timerDate: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_TIMER_DATE] ?: ""
    }

    val selectedLangs: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_SELECTED_LANGS] ?: "nl,en,ru"
    }

    val ollamaUrl: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_OLLAMA_URL] ?: OllamaConfig.DEFAULT_URL
    }

    val ollamaModel: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_OLLAMA_MODEL] ?: OllamaConfig.DEFAULT_MODEL
    }

    suspend fun saveUserId(userId: String) {
        context.dataStore.edit { prefs -> prefs[KEY_USER_ID] = userId }
    }

    suspend fun saveServerUrl(url: String) {
        context.dataStore.edit { prefs -> prefs[KEY_SERVER_URL] = url }
    }

    suspend fun saveUsername(name: String) {
        context.dataStore.edit { prefs -> prefs[KEY_USERNAME] = name }
    }

    suspend fun saveAuthMethod(method: String) {
        context.dataStore.edit { prefs -> prefs[KEY_AUTH_METHOD] = method }
    }

    suspend fun saveLastSyncTs(ts: Long) {
        context.dataStore.edit { prefs -> prefs[KEY_LAST_SYNC] = ts }
    }

    suspend fun saveTimerState(seconds: Long, date: String) {
        context.dataStore.edit { prefs ->
            prefs[KEY_TIMER_SECONDS] = seconds
            prefs[KEY_TIMER_DATE] = date
        }
    }

    suspend fun saveSelectedLangs(langs: String) {
        context.dataStore.edit { prefs -> prefs[KEY_SELECTED_LANGS] = langs }
    }

    suspend fun saveOllamaUrl(url: String) {
        context.dataStore.edit { prefs -> prefs[KEY_OLLAMA_URL] = url }
    }

    suspend fun saveOllamaModel(model: String) {
        context.dataStore.edit { prefs -> prefs[KEY_OLLAMA_MODEL] = model }
    }

    val isAdmin: Flow<Boolean> = context.dataStore.data.map { prefs ->
        prefs[KEY_IS_ADMIN] ?: false
    }

    suspend fun saveIsAdmin(value: Boolean) {
        context.dataStore.edit { prefs -> prefs[KEY_IS_ADMIN] = value }
    }

    suspend fun clearUser() {
        context.dataStore.edit { prefs ->
            prefs.remove(KEY_USER_ID)
            prefs.remove(KEY_USERNAME)
            prefs.remove(KEY_AUTH_METHOD)
            prefs.remove(KEY_IS_ADMIN)
        }
    }
}
