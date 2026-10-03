package com.learnwords.app.utils

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "learnwords_prefs")

class PreferencesManager(private val context: Context) {

    companion object {
        val KEY_USER_ID = stringPreferencesKey("user_id")
        val KEY_AUTH_TOKEN = stringPreferencesKey("auth_token")
        val KEY_SERVER_URL = stringPreferencesKey("server_url")
        val KEY_USERNAME = stringPreferencesKey("username")
        val KEY_LAST_SYNC = longPreferencesKey("last_sync_ts")
        val KEY_TIMER_SECONDS = longPreferencesKey("timer_seconds")
        val KEY_TIMER_DATE = stringPreferencesKey("timer_date")
        val KEY_TIMER_RUNNING = booleanPreferencesKey("timer_running")
        val KEY_SELECTED_LANGS = stringPreferencesKey("selected_langs")
        val KEY_UI_LANGUAGE_OVERRIDE = stringPreferencesKey("ui_language_override")
        val KEY_IS_ADMIN = booleanPreferencesKey("is_admin")
        val KEY_AUTH_METHOD = stringPreferencesKey("auth_method")
        val KEY_CACHE_LIMIT_MB = intPreferencesKey("cache_limit_mb")
        // Last account_type ("child"/"standard"/"pending") confirmed by the server.
        // Used as a fail-safe fallback when a fresh /api/me call fails (network error,
        // stale server_url after a domain migration, transient 401/404, etc.) so a
        // known child account is never silently treated as an adult account just
        // because a request failed. Only ever overwritten by an explicit, successful
        // server response — never by a failure.
        val KEY_ACCOUNT_TYPE_CACHE = stringPreferencesKey("account_type_cache")
    }

    val userId: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_USER_ID] ?: ""
    }

    val authToken: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_AUTH_TOKEN] ?: ""
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

    val timerRunning: Flow<Boolean> = context.dataStore.data.map { prefs ->
        prefs[KEY_TIMER_RUNNING] ?: true
    }

    val selectedLangs: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_SELECTED_LANGS] ?: "nl,en,ru"
    }

    val uiLanguageOverride: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_UI_LANGUAGE_OVERRIDE] ?: ""
    }

    val cacheLimitMb: Flow<Int> = context.dataStore.data.map { prefs ->
        (prefs[KEY_CACHE_LIMIT_MB] ?: WordContentCache.DEFAULT_CACHE_MB)
            .coerceIn(WordContentCache.MIN_CACHE_MB, WordContentCache.MAX_CACHE_MB)
    }

    suspend fun saveUserId(userId: String) {
        context.dataStore.edit { prefs -> prefs[KEY_USER_ID] = userId }
    }

    suspend fun saveAuthToken(token: String) {
        context.dataStore.edit { prefs -> prefs[KEY_AUTH_TOKEN] = token }
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

    suspend fun saveTimerState(seconds: Long, date: String, running: Boolean) {
        context.dataStore.edit { prefs ->
            prefs[KEY_TIMER_SECONDS] = seconds
            prefs[KEY_TIMER_DATE] = date
            prefs[KEY_TIMER_RUNNING] = running
        }
    }

    suspend fun saveSelectedLangs(langs: String) {
        context.dataStore.edit { prefs -> prefs[KEY_SELECTED_LANGS] = langs }
    }

    suspend fun saveUiLanguageOverride(languageCode: String?) {
        context.dataStore.edit { prefs ->
            val value = languageCode.orEmpty()
            if (value.isBlank()) {
                prefs.remove(KEY_UI_LANGUAGE_OVERRIDE)
            } else {
                prefs[KEY_UI_LANGUAGE_OVERRIDE] = value
            }
        }
    }

    suspend fun saveCacheLimitMb(value: Int) {
        context.dataStore.edit { prefs ->
            prefs[KEY_CACHE_LIMIT_MB] = value.coerceIn(
                WordContentCache.MIN_CACHE_MB,
                WordContentCache.MAX_CACHE_MB
            )
        }
    }

    val isAdmin: Flow<Boolean> = context.dataStore.data.map { prefs ->
        prefs[KEY_IS_ADMIN] ?: false
    }

    suspend fun saveIsAdmin(value: Boolean) {
        context.dataStore.edit { prefs -> prefs[KEY_IS_ADMIN] = value }
    }

    val accountTypeCache: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_ACCOUNT_TYPE_CACHE] ?: ""
    }

    /**
     * Persists the last account_type confirmed by the server. Call only with a value
     * that actually came back from a successful server response — never to record
     * "unknown"/failure, so a previously-known child account can't be overwritten
     * just because a later request failed.
     */
    suspend fun saveAccountTypeCache(accountType: String) {
        if (accountType.isBlank()) return
        context.dataStore.edit { prefs -> prefs[KEY_ACCOUNT_TYPE_CACHE] = accountType }
    }

    suspend fun clearUser() {
        ChildLearningReminder.setEnabled(context, false)
        context.dataStore.edit { prefs ->
            prefs.remove(KEY_USER_ID)
            prefs.remove(KEY_AUTH_TOKEN)
            prefs.remove(KEY_USERNAME)
            prefs.remove(KEY_AUTH_METHOD)
            prefs.remove(KEY_IS_ADMIN)
            prefs.remove(KEY_ACCOUNT_TYPE_CACHE)
        }
    }
}
