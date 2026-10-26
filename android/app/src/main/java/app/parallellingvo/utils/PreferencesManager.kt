package app.parallellingvo.utils

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import com.google.gson.Gson
import app.parallellingvo.ParallelLingvoApp
import kotlinx.coroutines.flow.first

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "learnwords_prefs")

class PreferencesManager(private val context: Context) {
    private val secrets = SecretStore()

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
        val KEY_THEME_MODE = intPreferencesKey("theme_mode")
        val KEY_UI_LANGUAGE_OVERRIDE = stringPreferencesKey("ui_language_override")
        val KEY_ADMIN_PREVIEW_PLAN = stringPreferencesKey("admin_preview_plan")
        val KEY_ADMIN_PREVIEW_ADS = booleanPreferencesKey("admin_preview_ads")
        val KEY_IS_ADMIN = booleanPreferencesKey("is_admin")
        val KEY_AUTH_METHOD = stringPreferencesKey("auth_method")
        val KEY_PENDING_AUTH = stringPreferencesKey("pending_android_auth")
        val KEY_CACHE_LIMIT_MB = intPreferencesKey("cache_limit_mb")
        // Last account_type ("child"/"standard"/"pending") confirmed by the server.
        // Used as a fail-safe fallback when a fresh /api/me call fails (network error,
        // stale server_url after a domain migration, transient 401/404, etc.) so a
        // known child account is never silently treated as an adult account just
        // because a request failed. Only ever overwritten by an explicit, successful
        // server response — never by a failure.
        val KEY_ACCOUNT_TYPE_CACHE = stringPreferencesKey("account_type_cache")
    }

    val themeMode: Flow<Int> = context.dataStore.data.map { prefs ->
        prefs[KEY_THEME_MODE]?.takeIf { it in setOf(-1, 1, 2) } ?: -1
    }

    suspend fun saveThemeMode(mode: Int) {
        require(mode in setOf(-1, 1, 2))
        context.dataStore.edit { it[KEY_THEME_MODE] = mode }
    }

    val userId: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[KEY_USER_ID] ?: ""
    }

    val pendingAuth: Flow<PendingAndroidAuth?> = context.dataStore.data.map { prefs ->
        runCatching { Gson().fromJson(readSecret(prefs, KEY_PENDING_AUTH), PendingAndroidAuth::class.java) }.getOrNull()
    }

    suspend fun savePendingAuth(flow: PendingAndroidAuth?) {
        context.dataStore.edit { prefs ->
            if (flow == null) prefs.remove(KEY_PENDING_AUTH)
            else prefs[KEY_PENDING_AUTH] = secrets.seal(Gson().toJson(flow))
        }
    }

    suspend fun saveLoginSession(userId: String, token: String, method: String, serverUrl: String) {
        require(userId.isNotBlank() && token.isNotBlank())
        SessionBoundary.transition(cancelRequests = ::cancelSessionRequests) {
            val previous = context.dataStore.data.first()
            val accountChanged = previous[KEY_USER_ID] != userId ||
                currentServerUrl(previous[KEY_SERVER_URL].orEmpty()) != currentServerUrl(serverUrl)
            eraseSessionData(accountChanged)
            context.dataStore.edit { prefs ->
                if (accountChanged) clearAccountPreferences(prefs)
                prefs[KEY_USER_ID] = userId
                prefs[KEY_AUTH_TOKEN] = secrets.seal(token)
                prefs[KEY_AUTH_METHOD] = method
                prefs[KEY_SERVER_URL] = currentServerUrl(serverUrl)
                prefs.remove(KEY_PENDING_AUTH)
            }
        }
    }

    val authToken: Flow<String> = context.dataStore.data.map { prefs ->
        readSecret(prefs, KEY_AUTH_TOKEN)
    }

    val serverUrl: Flow<String> = context.dataStore.data.map { prefs ->
        currentServerUrl(prefs[KEY_SERVER_URL].orEmpty())
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

    suspend fun saveServerUrl(url: String) {
        context.dataStore.edit { prefs -> prefs[KEY_SERVER_URL] = currentServerUrl(url) }
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

    val adminPreviewPlan: Flow<String> = context.dataStore.data.map {
        it[KEY_ADMIN_PREVIEW_PLAN].orEmpty().takeIf { plan -> plan in setOf("free", "premium", "family") }.orEmpty()
    }
    val adminPreviewAds: Flow<Boolean> = context.dataStore.data.map { it[KEY_ADMIN_PREVIEW_ADS] ?: true }

    suspend fun saveAdminPreview(plan: String, ads: Boolean = plan == "free") {
        require(plan.isEmpty() || plan in setOf("free", "premium", "family"))
        context.dataStore.edit {
            if (it[KEY_IS_ADMIN] != true || plan.isEmpty()) {
                it.remove(KEY_ADMIN_PREVIEW_PLAN)
                it.remove(KEY_ADMIN_PREVIEW_ADS)
            } else {
                it[KEY_ADMIN_PREVIEW_PLAN] = plan
                it[KEY_ADMIN_PREVIEW_ADS] = ads
            }
        }
    }

    val isAdmin: Flow<Boolean> = context.dataStore.data.map { prefs ->
        prefs[KEY_IS_ADMIN] ?: false
    }

    suspend fun saveIsAdmin(value: Boolean) {
        context.dataStore.edit { prefs ->
            prefs[KEY_IS_ADMIN] = value
            if (!value) {
                prefs.remove(KEY_ADMIN_PREVIEW_PLAN)
                prefs.remove(KEY_ADMIN_PREVIEW_ADS)
            }
        }
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
    suspend fun saveAccountTypeCache(accountType: String, expectedGeneration: Long = SessionBoundary.generation) {
        if (accountType.isBlank()) return
        context.dataStore.edit { prefs ->
            if (expectedGeneration % 2L == 0L && SessionBoundary.generation == expectedGeneration) {
                prefs[KEY_ACCOUNT_TYPE_CACHE] = accountType
            }
        }
    }

    private suspend fun readSecret(prefs: Preferences, key: Preferences.Key<String>): String {
        val stored = prefs[key].orEmpty()
        if (stored.isNotBlank() && !stored.startsWith("ks1:")) {
            val encrypted = secrets.seal(stored)
            context.dataStore.edit { if (it[key] == stored) it[key] = encrypted }
        }
        return secrets.open(stored)
    }

    suspend fun clearAfterDeletion() {
        SessionBoundary.transition(cancelRequests = ::cancelSessionRequests) {
            eraseSessionData(true)
            context.dataStore.edit { it.clear() }
        }
    }

    suspend fun clearUser() {
        SessionBoundary.transition(cancelRequests = ::cancelSessionRequests) {
            eraseSessionData(true)
            context.dataStore.edit { clearAccountPreferences(it) }
        }
    }

    private suspend fun eraseSessionData(clearAccount: Boolean) {
        val app = context.applicationContext as ParallelLingvoApp
        app.repository.clearCurrentUser()
        app.apiClient.clearCookies()
        if (clearAccount) {
            ChildLearningReminder.setEnabled(context, false)
            app.database.clearAllTables()
            app.wordContentCache.clear()
        }
    }

    private fun cancelSessionRequests() {
        (context.applicationContext as ParallelLingvoApp).apiClient.clearCookies()
    }

    private fun clearAccountPreferences(prefs: MutablePreferences) {
        for (key in listOf(KEY_USER_ID, KEY_AUTH_TOKEN, KEY_USERNAME, KEY_AUTH_METHOD,
            KEY_PENDING_AUTH, KEY_ACCOUNT_TYPE_CACHE, KEY_SELECTED_LANGS, KEY_TIMER_DATE)) prefs.remove(key)
        prefs.remove(KEY_ADMIN_PREVIEW_PLAN)
        prefs.remove(KEY_ADMIN_PREVIEW_ADS)
        prefs.remove(KEY_IS_ADMIN)
        prefs.remove(KEY_LAST_SYNC)
        prefs.remove(KEY_TIMER_SECONDS)
        prefs.remove(KEY_TIMER_RUNNING)
    }
}
