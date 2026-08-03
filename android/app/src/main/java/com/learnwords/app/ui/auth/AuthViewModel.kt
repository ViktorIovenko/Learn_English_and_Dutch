package com.learnwords.app.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.R
import com.learnwords.app.utils.NetworkResult
import com.learnwords.app.utils.ChildLearningReminder
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

data class AuthUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val isLoggedIn: Boolean = false,
    val needsAccountType: Boolean = false,
    val accountType: String? = null
)

class AuthViewModel : ViewModel() {

    private val repo = LearnWordsApp.instance.repository
    private val prefs = LearnWordsApp.instance.preferencesManager
    private val app = LearnWordsApp.instance

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState

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
                    prefs.saveAuthMethod(app.getString(R.string.manual_login))
                    val me = repo.getMe()
                    var accountType: String? = null
                    val needsAccountType = when (me) {
                        is NetworkResult.Success -> {
                            accountType = me.data.accountType
                            ChildLearningReminder.setEnabled(app, accountType == "child")
                            me.data.needsAccountType
                        }
                        else -> false
                    }
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        isLoggedIn = true,
                        needsAccountType = needsAccountType,
                        accountType = accountType
                    )
                }
                is NetworkResult.Error -> {
                    // If server returns 404 (endpoint not found), try saving user_id directly
                    if (result.code == 404 || result.code == 405) {
                        ChildLearningReminder.setEnabled(app, false)
                        prefs.saveUserId(userId)
                        prefs.saveAuthMethod(app.getString(R.string.manual_login))
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            isLoggedIn = true,
                            needsAccountType = false,
                            accountType = null
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
            prefs.saveAuthMethod(app.getString(R.string.offline_login))
            if (serverUrl.isNotBlank()) prefs.saveServerUrl(serverUrl)
            _uiState.value = _uiState.value.copy(
                isLoggedIn = true,
                needsAccountType = false,
                accountType = null
            )
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
