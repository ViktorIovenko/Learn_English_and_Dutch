package com.learnwords.app.ui.admin

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.R
import com.learnwords.app.data.api.AdminUserDto
import com.learnwords.app.data.api.AdminTtsUsageDto
import com.learnwords.app.data.api.AdminTranslationUsageDto
import com.learnwords.app.utils.NetworkResult
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class AdminUiState(
    val isLoading: Boolean = false,
    val users: List<AdminUserDto> = emptyList(),
    val ttsUsage: AdminTtsUsageDto? = null,
    val translationUsage: AdminTranslationUsageDto? = null,
    val error: String? = null,
    val success: String? = null
)

class AdminViewModel : ViewModel() {

    private val repo = LearnWordsApp.instance.repository
    private val app = LearnWordsApp.instance

    private val _uiState = MutableStateFlow(AdminUiState())
    val uiState: StateFlow<AdminUiState> = _uiState

    init {
        loadUsers()
    }

    fun loadUsers() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = repo.getAdminUsers()) {
                is NetworkResult.Success -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    users = result.data.users,
                    ttsUsage = result.data.ttsUsage,
                    translationUsage = result.data.translationUsage
                )
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> {}
            }
        }
    }

    fun grantAccess(userId: String) {
        val uid = userId.trim()
        if (uid.isBlank()) {
            _uiState.value = _uiState.value.copy(error = app.getString(R.string.enter_telegram_user_id))
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            when (val result = repo.grantAccess(uid)) {
                is NetworkResult.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        success = app.getString(R.string.access_granted, uid)
                    )
                    loadUsers()
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> {}
            }
        }
    }

    fun revokeAccess(userId: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            when (val result = repo.revokeAccess(userId)) {
                is NetworkResult.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        success = app.getString(R.string.access_revoked, userId)
                    )
                    loadUsers()
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> {}
            }
        }
    }

    fun clearMessages() {
        _uiState.value = _uiState.value.copy(error = null, success = null)
    }

    fun unlinkFamily(parentUserId: String, childUserId: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            when (val result = repo.adminUnlinkFamily(parentUserId, childUserId)) {
                is NetworkResult.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        success = app.getString(R.string.admin_family_unlinked)
                    )
                    loadUsers()
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false, error = result.message
                )
                else -> Unit
            }
        }
    }

    fun resetTtsUsage(userId: String? = null) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            when (val result = repo.resetTtsUsage(userId)) {
                is NetworkResult.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        success = if (userId == null) {
                            app.getString(R.string.tts_usage_all_reset)
                        } else {
                            app.getString(R.string.tts_usage_user_reset, userId)
                        }
                    )
                    loadUsers()
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> Unit
            }
        }
    }

    fun resetTranslationUsage(userId: String? = null) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            when (val result = repo.resetTranslationUsage(userId)) {
                is NetworkResult.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        success = if (userId == null) {
                            app.getString(R.string.translation_usage_all_reset)
                        } else {
                            app.getString(R.string.translation_usage_user_reset, userId)
                        }
                    )
                    loadUsers()
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> Unit
            }
        }
    }
}
