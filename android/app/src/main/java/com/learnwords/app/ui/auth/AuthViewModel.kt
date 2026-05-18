package com.learnwords.app.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.utils.NetworkResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

data class AuthUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val isLoggedIn: Boolean = false
)

class AuthViewModel : ViewModel() {

    private val repo = LearnWordsApp.instance.repository
    private val prefs = LearnWordsApp.instance.preferencesManager

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState

    val serverUrl = prefs.serverUrl
    val userId = prefs.userId

    fun login(userId: String, password: String, serverUrl: String) {
        if (userId.isBlank()) {
            _uiState.value = _uiState.value.copy(error = "Введите User ID")
            return
        }
        if (serverUrl.isBlank()) {
            _uiState.value = _uiState.value.copy(error = "Введите URL сервера")
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = repo.login(userId, password, serverUrl)) {
                is NetworkResult.Success -> {
                    val uid = result.data.userId ?: userId
                    prefs.saveUserId(uid)
                    prefs.saveAuthMethod("Ручной вход")
                    _uiState.value = _uiState.value.copy(isLoading = false, isLoggedIn = true)
                }
                is NetworkResult.Error -> {
                    // If server returns 404 (endpoint not found), try saving user_id directly
                    if (result.code == 404 || result.code == 405) {
                        prefs.saveUserId(userId)
                        prefs.saveAuthMethod("Ручной вход")
                        _uiState.value = _uiState.value.copy(isLoading = false, isLoggedIn = true)
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
            _uiState.value = _uiState.value.copy(error = "Введите User ID")
            return
        }
        viewModelScope.launch {
            prefs.saveUserId(userId)
            prefs.saveAuthMethod("Без сервера")
            if (serverUrl.isNotBlank()) prefs.saveServerUrl(serverUrl)
            _uiState.value = _uiState.value.copy(isLoggedIn = true)
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
