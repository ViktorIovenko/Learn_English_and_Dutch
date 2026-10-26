package app.parallellingvo.ui.auth

import android.content.Intent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import app.parallellingvo.ParallelLingvoApp
import app.parallellingvo.R
import app.parallellingvo.utils.NetworkResult
import app.parallellingvo.utils.ChildLearningReminder
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

    private val repo = ParallelLingvoApp.instance.repository
    private val prefs = ParallelLingvoApp.instance.preferencesManager
    private val app = ParallelLingvoApp.instance

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState
    private val _googleSignInIntent = MutableSharedFlow<Intent>(extraBufferCapacity = 1)
    val googleSignInIntent = _googleSignInIntent

    val serverUrl = prefs.serverUrl
    val userId = prefs.userId

    fun loginWithEmail(email: String, password: String, serverUrl: String, language: String) {
        if (_uiState.value.isLoading) return
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches() || password.isEmpty()) {
            _uiState.value = _uiState.value.copy(error = app.getString(R.string.auth_email_invalid))
            return
        }
        _uiState.value = _uiState.value.copy(isLoading = true, error = null)
        viewModelScope.launch {
            prefs.savePendingAuth(null)
            when (val result = repo.loginEmail(serverUrl, email, password, language)) {
                is NetworkResult.Success -> {
                    val uid = result.data.userId.orEmpty()
                    val token = result.data.token.orEmpty()
                    if (!result.data.ok || uid.isBlank() || token.isBlank()) {
                        _uiState.value = _uiState.value.copy(isLoading = false, error = app.getString(R.string.auth_failed))
                        return@launch
                    }
                    repo.clearAuthCookies()
                    prefs.saveLoginSession(uid, token, "Email", serverUrl)
                    val me = (repo.getMe() as? NetworkResult.Success)?.data
                    val accountType = me?.accountType ?: prefs.accountTypeCache.first().ifBlank { null }
                    ChildLearningReminder.setEnabled(app, accountType == "child")
                    _uiState.value = _uiState.value.copy(
                        isLoading = false, isLoggedIn = true, accountType = accountType,
                        needsAccountType = me?.needsAccountType == true,
                        hasSubscriptionAccess = me?.let { it.canUseApp } == true
                    )
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(isLoading = false,
                    error = app.getString(when (result.code) {
                        401 -> R.string.auth_email_invalid
                        429 -> R.string.auth_rate_limited
                        else -> R.string.auth_failed
                    }))
                else -> Unit
            }
        }
    }

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
                    val uid = result.data.userId.orEmpty()
                    val token = result.data.token.orEmpty()
                    if (!result.data.ok || uid.isBlank() || token.isBlank()) {
                        _uiState.value = _uiState.value.copy(isLoading = false, error = app.getString(R.string.auth_failed))
                        return@launch
                    }
                    prefs.saveLoginSession(uid, token, app.getString(R.string.manual_login), serverUrl)
                    val me = repo.getMe()
                    var accountType: String? = null
                    var hasSubscriptionAccess = false
                    val needsAccountType = when (me) {
                        is NetworkResult.Success -> {
                            accountType = me.data.accountType
                            hasSubscriptionAccess = me.data.canUseApp
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
                    _uiState.value = _uiState.value.copy(isLoading = false, error = result.message)
                }
                else -> {}
            }
        }
    }

    fun startGoogleLogin(serverUrl: String) {
        if (_uiState.value.isLoading) return
        if (serverUrl.isBlank()) {
            _uiState.value = _uiState.value.copy(error = app.getString(R.string.enter_server_url))
            return
        }
        // Lock synchronously: another click may arrive before the coroutine resumes.
        _uiState.value = _uiState.value.copy(isLoading = true, error = null)
        viewModelScope.launch {
            prefs.savePendingAuth(null)
            when (val result = repo.getGoogleAuthConfig(serverUrl)) {
                is NetworkResult.Success -> {
                    val clientId = result.data.clientId.orEmpty()
                    if (!result.data.ok || clientId.isBlank()) {
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
                    val token = result.data.token.orEmpty()
                    if (!result.data.ok || userId.isNullOrBlank() || token.isBlank()) {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = app.getString(R.string.google_login_failed)
                        )
                        return@launch
                    }
                    repo.clearAuthCookies()
                    prefs.saveLoginSession(userId, token, app.getString(R.string.google_login), serverUrl)
                    val me = repo.getMe()
                    val serverAccountType = (me as? NetworkResult.Success)?.data?.accountType
                    // Fall back to the last confirmed account type if /api/me failed,
                    // instead of silently treating the account as an adult account.
                    val accountType = serverAccountType ?: prefs.accountTypeCache.first().ifBlank { null }
                    val hasSubscriptionAccess = (me as? NetworkResult.Success)?.data?.let {
                        it.canUseApp
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
        _uiState.value = _uiState.value.copy(isLoading = false, error = app.getString(R.string.google_login_cancelled))
    }

    fun googleLoginFailed(statusCode: Int? = null) {
        val message = app.getString(R.string.google_login_failed) +
            (statusCode?.let { " (Google: $it)" } ?: "")
        _uiState.value = _uiState.value.copy(isLoading = false, error = message)
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
