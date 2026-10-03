package com.learnwords.app.ui.auth

import android.content.Intent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.R
import com.learnwords.app.utils.NetworkResult
import com.learnwords.app.utils.ChildLearningReminder
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

data class AuthUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val isLoggedIn: Boolean = false,
    val hasSubscriptionAccess: Boolean = false,
    val needsAccountType: Boolean = false,
    val accountType: String? = null
)

class AuthViewModel : ViewModel() {

    private val repo = LearnWordsApp.instance.repository
    private val prefs = LearnWordsApp.instance.preferencesManager
    private val app = LearnWordsApp.instance

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState
    private val _googleSignInIntent = MutableSharedFlow<Intent>(extraBufferCapacity = 1)
    val googleSignInIntent = _googleSignInIntent

    val serverUrl = prefs.serverUrl
    val userId = prefs.userId

    fun login(userId: String, password: String, serverUrl: String) {
        if (userId.isBlank()) {
            _uiState.value = _uiState.value.copy(error = app.getString(R.string.enter_user_id))
            return
        }
        if (serverUrl.isBlank()) {
            _uiState.value = _uiState.value.copy(error = app.getString(R.string.enter_server_url))
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = repo.login(userId, password, serverUrl)) {
                is NetworkResult.Success -> {
                    val uid = result.data.userId ?: userId
                    prefs.saveUserId(uid)
                    prefs.saveAuthToken(result.data.token.orEmpty())
                    prefs.saveAuthMethod(app.getString(R.string.manual_login))
                    val me = repo.getMe()
                    var accountType: String? = null
                    var hasSubscriptionAccess = false
                    val needsAccountType = when (me) {
                        is NetworkResult.Success -> {
                            accountType = me.data.accountType
                            if (accountType != null) prefs.saveAccountTypeCache(accountType)
                            hasSubscriptionAccess = me.data.isAdmin == true || me.data.subscription?.isActive == true
                            ChildLearningReminder.setEnabled(app, accountType == "child")
                            me.data.needsAccountType
                        }
                        else -> {
                            // /api/me failed right after login (e.g. stale server_url,
                            // transient error during a domain migration) — don't treat
                            // this as "not a child": fall back to the last confirmed
                            // account type for this device instead of disabling it.
                            val cachedAccountType = prefs.accountTypeCache.first()
                            accountType = cachedAccountType.ifBlank { null }
                            ChildLearningReminder.setEnabled(app, accountType == "child")
                            false
                        }
                    }
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        isLoggedIn = true,
                        hasSubscriptionAccess = hasSubscriptionAccess,
                        needsAccountType = needsAccountType,
                        accountType = accountType
                    )
                }
                is NetworkResult.Error -> {
                    // If server returns 404 (endpoint not found), try saving user_id directly
                    if (result.code == 404 || result.code == 405) {
                        // A broken/old login endpoint (e.g. leftover from a domain
                        // migration) is not proof this is an adult account — keep
                        // whatever account type this device last confirmed for it.
                        val cachedAccountType = prefs.accountTypeCache.first().ifBlank { null }
                        ChildLearningReminder.setEnabled(app, cachedAccountType == "child")
                        prefs.saveUserId(userId)
                        prefs.saveAuthToken("")
                        prefs.saveAuthMethod(app.getString(R.string.manual_login))
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            isLoggedIn = true,
                            needsAccountType = false,
                            accountType = cachedAccountType
                        )
                    } else {
                        _uiState.value = _uiState.value.copy(isLoading = false, error = result.message)
                    }
                }
                else -> {}
            }
        }
    }

    fun loginOffline(userId: String, serverUrl: String) {
        if (userId.isBlank()) {
            _uiState.value = _uiState.value.copy(error = app.getString(R.string.enter_user_id))
            return
        }
        viewModelScope.launch {
            ChildLearningReminder.setEnabled(app, false)
            prefs.saveUserId(userId)
            prefs.saveAuthToken("")
            prefs.saveAuthMethod(app.getString(R.string.offline_login))
            if (serverUrl.isNotBlank()) prefs.saveServerUrl(serverUrl)
            _uiState.value = _uiState.value.copy(
                isLoggedIn = true,
                needsAccountType = false,
                accountType = null
            )
        }
    }

    fun startGoogleLogin(serverUrl: String) {
        if (serverUrl.isBlank()) {
            _uiState.value = _uiState.value.copy(error = app.getString(R.string.enter_server_url))
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = repo.getGoogleAuthConfig(serverUrl)) {
                is NetworkResult.Success -> {
                    val clientId = result.data.clientId.orEmpty()
                    if (clientId.isBlank()) {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = app.getString(R.string.google_login_failed)
                        )
                        return@launch
                    }
                    val options = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
                        .requestIdToken(clientId)
                        .requestEmail()
                        .build()
                    _googleSignInIntent.emit(GoogleSignIn.getClient(app, options).signInIntent)
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> Unit
            }
        }
    }

    fun loginWithGoogleToken(idToken: String, serverUrl: String) {
        if (idToken.isBlank()) {
            _uiState.value = _uiState.value.copy(isLoading = false, error = app.getString(R.string.google_login_failed))
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = repo.loginWithGoogleToken(serverUrl, idToken)) {
                is NetworkResult.Success -> {
                    val userId = result.data.userId
                    if (userId.isNullOrBlank()) {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = app.getString(R.string.google_login_failed)
                        )
                        return@launch
                    }
                    prefs.saveUserId(userId)
                    prefs.saveAuthToken(result.data.token.orEmpty())
                    prefs.saveAuthMethod(app.getString(R.string.google_login))
                    val me = repo.getMe()
                    val serverAccountType = (me as? NetworkResult.Success)?.data?.accountType
                    if (serverAccountType != null) prefs.saveAccountTypeCache(serverAccountType)
                    // Fall back to the last confirmed account type if /api/me failed,
                    // instead of silently treating the account as an adult account.
                    val accountType = serverAccountType ?: prefs.accountTypeCache.first().ifBlank { null }
                    val hasSubscriptionAccess = (me as? NetworkResult.Success)?.data?.let {
                        it.isAdmin == true || it.subscription?.isActive == true
                    } == true
                    ChildLearningReminder.setEnabled(app, accountType == "child")
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        isLoggedIn = true,
                        hasSubscriptionAccess = hasSubscriptionAccess,
                        needsAccountType = (me as? NetworkResult.Success)?.data?.needsAccountType == true,
                        accountType = accountType
                    )
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> Unit
            }
        }
    }

    fun googleLoginCancelled() {
        _uiState.value = _uiState.value.copy(error = app.getString(R.string.google_login_cancelled))
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
