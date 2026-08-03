package com.learnwords.app.ui.settings

import android.content.res.Resources
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.R
import com.learnwords.app.data.api.LanguageOption
import com.learnwords.app.data.api.UserLanguageDto
import com.learnwords.app.utils.NetworkResult
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class LangSettingsUiState(
    val isLoading: Boolean = false,
    val allLanguages: List<LanguageOption> = emptyList(),
    val selectedLangs: MutableList<String> = mutableListOf(),
    val uiLanguage: String = "",
    val detectedUiLanguage: String = "",
    val uiLanguageOverride: String? = null,
    val error: String? = null,
    val saved: Boolean = false
)

class LanguageSettingsViewModel : ViewModel() {

    private val repo = LearnWordsApp.instance.repository
    private val prefs = LearnWordsApp.instance.preferencesManager
    private val app = LearnWordsApp.instance

    val isAdmin: StateFlow<Boolean> = prefs.isAdmin
        .stateIn(viewModelScope, SharingStarted.Eagerly, false)

    val userId: StateFlow<String> = prefs.userId
        .stateIn(viewModelScope, SharingStarted.Eagerly, "")

    val serverUrl: StateFlow<String> = prefs.serverUrl
        .stateIn(viewModelScope, SharingStarted.Eagerly, "")

    val authMethod: StateFlow<String> = prefs.authMethod
        .stateIn(viewModelScope, SharingStarted.Eagerly, "")

    private val _uiState = MutableStateFlow(LangSettingsUiState())
    val uiState: StateFlow<LangSettingsUiState> = _uiState

    init {
        loadLanguages()
    }

    private fun loadLanguages() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            val localUiLanguageOverride = prefs.uiLanguageOverride.first().ifBlank { null }
            val systemUiLanguage = systemLanguageCode()

            val optionsResult = repo.getLanguageOptions()
            val selectedResult = repo.getUserLanguages()
            val uiLanguageResult = repo.getUiLanguage()

            val allLangs = if (optionsResult is NetworkResult.Success) {
                optionsResult.data
            } else {
                defaultLanguageOptions()
            }

            val selected = if (selectedResult is NetworkResult.Success) {
                selectedResult.data.sortedBy { it.priority }.map { it.langCode }.ifEmpty {
                    listOf("nl", "en", "ru")
                }.toMutableList()
            } else {
                mutableListOf("nl", "en", "ru")
            }

            val uiLanguage = if (uiLanguageResult is NetworkResult.Success) {
                localUiLanguageOverride ?: systemUiLanguage
            } else {
                localUiLanguageOverride ?: systemUiLanguage
            }
            val detectedUiLanguage = if (uiLanguageResult is NetworkResult.Success) {
                uiLanguageResult.data.detectedUiLanguage.orEmpty().ifBlank { systemUiLanguage }
            } else {
                systemUiLanguage
            }
            val uiLanguageOverride = localUiLanguageOverride

            _uiState.value = _uiState.value.copy(
                isLoading = false,
                allLanguages = allLangs,
                selectedLangs = selected,
                uiLanguage = uiLanguage,
                detectedUiLanguage = detectedUiLanguage,
                uiLanguageOverride = uiLanguageOverride
            )
        }
    }

    fun addLanguage(langCode: String) {
        val state = _uiState.value
        if (langCode in state.selectedLangs || state.selectedLangs.size >= 5) return
        _uiState.value = state.copy(
            selectedLangs = (state.selectedLangs + langCode).toMutableList()
        )
    }

    fun removeLanguage(langCode: String) {
        val state = _uiState.value
        if (state.selectedLangs.size <= 3) return
        _uiState.value = state.copy(
            selectedLangs = state.selectedLangs.filter { it != langCode }.toMutableList()
        )
    }

    fun moveUp(langCode: String) {
        val state = _uiState.value
        val list = state.selectedLangs.toMutableList()
        val idx = list.indexOf(langCode)
        if (idx <= 0) return
        list.removeAt(idx)
        list.add(idx - 1, langCode)
        _uiState.value = state.copy(selectedLangs = list)
    }

    fun moveDown(langCode: String) {
        val state = _uiState.value
        val list = state.selectedLangs.toMutableList()
        val idx = list.indexOf(langCode)
        if (idx < 0 || idx >= list.size - 1) return
        list.removeAt(idx)
        list.add(idx + 1, langCode)
        _uiState.value = state.copy(selectedLangs = list)
    }

    fun save() {
        viewModelScope.launch {
            val langs = _uiState.value.selectedLangs
            if (langs.size !in 3..5) {
                _uiState.value = _uiState.value.copy(error = app.getString(R.string.choose_3_to_5_languages))
                return@launch
            }
            _uiState.value = _uiState.value.copy(isLoading = true)
            when (val result = repo.saveUserLanguages(langs)) {
                is NetworkResult.Success -> {
                    repo.getUiLanguage()
                    _uiState.value = _uiState.value.copy(
                        isLoading = false, saved = true
                    )
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false, error = result.message
                )
                else -> {}
            }
        }
    }

    fun saveUiLanguageOverride(languageCode: String?) {
        viewModelScope.launch {
            val normalizedCode = languageCode?.takeIf { it.isNotBlank() }
            prefs.saveUiLanguageOverride(normalizedCode)
            _uiState.value = _uiState.value.copy(
                isLoading = true,
                uiLanguage = normalizedCode ?: systemLanguageCode(),
                detectedUiLanguage = _uiState.value.detectedUiLanguage.ifBlank { systemLanguageCode() },
                uiLanguageOverride = normalizedCode
            )
            when (val result = repo.saveUiLanguage(languageCode)) {
                is NetworkResult.Success -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    uiLanguage = normalizedCode ?: result.data.detectedUiLanguage.orEmpty().ifBlank { systemLanguageCode() },
                    detectedUiLanguage = result.data.detectedUiLanguage.orEmpty().ifBlank { systemLanguageCode() },
                    uiLanguageOverride = normalizedCode,
                    saved = true
                )
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> {}
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    fun clearSaved() {
        _uiState.value = _uiState.value.copy(saved = false)
    }

    fun logout() {
        viewModelScope.launch {
            prefs.clearUser()
        }
    }

    private fun systemLanguageCode(): String =
        Resources.getSystem().configuration.locales[0].language

    private fun defaultLanguageOptions() = listOf(
        LanguageOption("nl", "Nederlands", "🇳🇱"),
        LanguageOption("en", "English", "🇬🇧"),
        LanguageOption("ru", "Русский", "🇷🇺"),
        LanguageOption("de", "Deutsch", "🇩🇪"),
        LanguageOption("fr", "Français", "🇫🇷"),
        LanguageOption("es", "Español", "🇪🇸"),
        LanguageOption("it", "Italiano", "🇮🇹"),
        LanguageOption("pt", "Português", "🇵🇹"),
        LanguageOption("pl", "Polski", "🇵🇱"),
        LanguageOption("uk", "Українська", "🇺🇦")
    )
}
