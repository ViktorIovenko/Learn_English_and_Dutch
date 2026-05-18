package com.learnwords.app.ui.upload

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.data.ai.OllamaConfig
import com.learnwords.app.data.ai.OllamaStatus
import com.learnwords.app.data.api.WordDto
import com.learnwords.app.utils.NetworkResult
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class UploadUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val success: String? = null,
    val generatedWords: List<WordDto> = emptyList(),
    val dbWords: List<WordDto> = emptyList(),
    val dbTotal: Int = 0,
    val dbPage: Int = 1,
    val dbQuery: String = "",
    val shareLessons: List<com.learnwords.app.data.api.LessonDto> = emptyList(),
    val shareUrl: String? = null,
    val ollamaStatus: String? = null
)

class UploadViewModel : ViewModel() {

    private val repo = LearnWordsApp.instance.repository
    private val prefs = LearnWordsApp.instance.preferencesManager

    private val _uiState = MutableStateFlow(UploadUiState())
    val uiState: StateFlow<UploadUiState> = _uiState

    val serverUrl = prefs.serverUrl

    val ollamaUrl: StateFlow<String> = prefs.ollamaUrl
        .stateIn(viewModelScope, SharingStarted.Eagerly, OllamaConfig.DEFAULT_URL)

    val ollamaModel: StateFlow<String> = prefs.ollamaModel
        .stateIn(viewModelScope, SharingStarted.Eagerly, OllamaConfig.DEFAULT_MODEL)

    // ─── Ollama settings ─────────────────────────────────────────────────────

    fun saveOllamaSettings(url: String, model: String) {
        viewModelScope.launch {
            prefs.saveOllamaUrl(url.trim())
            prefs.saveOllamaModel(model.trim().ifBlank { OllamaConfig.DEFAULT_MODEL })
        }
    }

    fun checkOllamaConnection() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, ollamaStatus = null)
            val status = repo.checkOllamaConnection()
            _uiState.value = _uiState.value.copy(
                isLoading = false,
                ollamaStatus = when (status) {
                    is OllamaStatus.Available -> {
                        val models = status.models.take(3).joinToString(", ").ifBlank { "нет моделей" }
                        "Доступна. Модели: $models"
                    }
                    is OllamaStatus.Error -> "Ошибка: ${status.message}"
                }
            )
        }
    }

    // ─── Manual word entry ───────────────────────────────────────────────────

    fun translateWord(word: String, fromLang: String, toLangs: List<String>) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = repo.translateWord(word, fromLang, toLangs)) {
                is NetworkResult.Success -> {
                    val current = _uiState.value.generatedWords.toMutableList()
                    current.add(result.data)
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        generatedWords = current
                    )
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> {}
            }
        }
    }

    // ─── Generate by topic ───────────────────────────────────────────────────

    fun generateByTopic(topic: String, level: String, count: Int, languages: List<String>) {
        if (topic.isBlank()) {
            _uiState.value = _uiState.value.copy(error = "Введите тему")
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null, generatedWords = emptyList())
            when (val result = repo.generateByTopic(topic, level, count, languages)) {
                is NetworkResult.Success -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    generatedWords = result.data
                )
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> {}
            }
        }
    }

    // ─── Import words ────────────────────────────────────────────────────────

    fun importWords(lesson: String, words: List<Map<String, String?>>) {
        if (lesson.isBlank()) {
            _uiState.value = _uiState.value.copy(error = "Введите название урока")
            return
        }
        if (words.isEmpty()) {
            _uiState.value = _uiState.value.copy(error = "Нет слов для импорта")
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = repo.importWords(lesson, words)) {
                is NetworkResult.Success -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    success = "Импортировано: ${result.data.imported}, пропущено: ${result.data.skipped}",
                    generatedWords = emptyList()
                )
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> {}
            }
        }
    }

    // ─── Word database ───────────────────────────────────────────────────────

    fun searchWords(query: String, page: Int = 1) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, dbQuery = query, dbPage = page)
            when (val result = repo.getWords(query.ifBlank { null }, page, 30)) {
                is NetworkResult.Success -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    dbWords = result.data.words,
                    dbTotal = result.data.total ?: 0
                )
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> {}
            }
        }
    }

    fun deleteWord(wordId: Int) {
        viewModelScope.launch {
            when (val result = repo.deleteWord(wordId)) {
                is NetworkResult.Success -> {
                    val state = _uiState.value
                    _uiState.value = state.copy(
                        dbWords = state.dbWords.filter { it.id != wordId },
                        success = "Слово удалено"
                    )
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(error = result.message)
                else -> {}
            }
        }
    }

    fun ensureAudio(wordIds: List<Int>) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            when (val result = repo.ensureAudio(wordIds)) {
                is NetworkResult.Success -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    success = "Аудио создано: ${result.data.generated}, пропущено: ${result.data.skipped}"
                )
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false, error = result.message
                )
                else -> {}
            }
        }
    }

    // ─── Share ───────────────────────────────────────────────────────────────

    fun loadShareLessons() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = repo.getShareSourceLessons()) {
                is NetworkResult.Success -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    shareLessons = result.data
                )
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> {}
            }
        }
    }

    fun createShare(lessons: List<String>, title: String?) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, shareUrl = null)
            when (val result = repo.createShare(lessons, title, null)) {
                is NetworkResult.Success -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    shareUrl = result.data.url
                )
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false, error = result.message
                )
                else -> {}
            }
        }
    }

    fun clearMessages() {
        _uiState.value = _uiState.value.copy(error = null, success = null, ollamaStatus = null)
    }
}
