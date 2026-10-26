package app.parallellingvo.ui.upload

import app.parallellingvo.data.api.LessonDto

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import app.parallellingvo.ParallelLingvoApp
import app.parallellingvo.R
import app.parallellingvo.data.api.WordDto
import app.parallellingvo.utils.NetworkResult
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
    val shareLessons: List<LessonDto> = emptyList(),
    val shareUrl: String? = null,
    val duplicates: List<WordDto> = emptyList()
)

class UploadViewModel : ViewModel() {

    private val repo = ParallelLingvoApp.instance.repository
    private val prefs = ParallelLingvoApp.instance.preferencesManager
    private val app = ParallelLingvoApp.instance

    private fun aiError(result: NetworkResult.Error): String = when {
        result.message.contains("upgrade_required") -> app.getString(R.string.plan_ai_upgrade)
        result.message.contains("paid_ai_disabled") -> app.getString(R.string.plan_ai_paused)
        else -> result.message
    }

    private val _uiState = MutableStateFlow(UploadUiState())
    val uiState: StateFlow<UploadUiState> = _uiState

    val serverUrl = prefs.serverUrl

    private val topicLanguageCodes = setOf("nl", "en", "ru", "de", "fr", "es", "it", "pt", "pl", "uk")

    // ─── Manual word entry (облачная генерация через AI Platform) ───────────

    fun translateWords(words: List<String>, fromLang: String) {
        if (_uiState.value.isLoading || words.isEmpty()) return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null, generatedWords = emptyList())
            val translated = mutableListOf<WordDto>()
            for (word in words) {
                when (val result = repo.translateWord(word, fromLang)) {
                    is NetworkResult.Success -> translated.add(result.data)
                    is NetworkResult.Error -> {
                        _uiState.value = _uiState.value.copy(isLoading = false, error = aiError(result))
                        return@launch
                    }
                    else -> return@launch
                }
            }
            _uiState.value = _uiState.value.copy(isLoading = false, generatedWords = translated)
        }
    }

    // ─── Generate by topic (облачная генерация через AI Platform) ───────────

    fun createLessonByTopic(topic: String, level: String, count: Int) {
        if (_uiState.value.isLoading) return
        if (topic.isBlank()) {
            _uiState.value = _uiState.value.copy(error = app.getString(R.string.enter_topic))
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null, generatedWords = emptyList())
            when (val result = repo.generateByTopic(topic, level, count.coerceIn(1, 50))) {
                is NetworkResult.Success -> {
                    val gson = com.google.gson.Gson()
                    val words = result.data.map { word ->
                        gson.toJsonTree(word).asJsonObject.entrySet()
                            .filter { (key, value) ->
                                (key in topicLanguageCodes || key.removePrefix("ex_") in topicLanguageCodes) &&
                                    !value.isJsonNull
                            }
                            .associate { (key, value) -> key to value.asString }
                    }
                    if (words.isEmpty()) {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false, error = app.getString(R.string.no_words_to_import)
                        )
                        return@launch
                    }
                    when (val imported = repo.importWords(topic, words)) {
                        is NetworkResult.Success -> {
                            repo.refreshLessons()
                            _uiState.value = _uiState.value.copy(
                                isLoading = false,
                                success = app.getString(R.string.import_result, imported.data.imported, imported.data.skipped)
                            )
                        }
                        is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                            isLoading = false, error = imported.message
                        )
                        else -> {}
                    }
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = aiError(result)
                )
                else -> {}
            }
        }
    }

    // ─── Import words ────────────────────────────────────────────────────────

    fun importWords(lesson: String, words: List<Map<String, String?>>) {
        if (lesson.isBlank()) {
            _uiState.value = _uiState.value.copy(error = app.getString(R.string.enter_lesson_title))
            return
        }
        if (words.isEmpty()) {
            _uiState.value = _uiState.value.copy(error = app.getString(R.string.no_words_to_import))
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            when (val result = repo.importWords(lesson, words)) {
                is NetworkResult.Success -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    success = app.getString(R.string.import_result, result.data.imported, result.data.skipped),
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
            _uiState.value = _uiState.value.copy(
                isLoading = true,
                error = null,
                success = null,
                dbQuery = query,
                dbPage = page
            )
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
                        success = app.getString(R.string.word_deleted)
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
                    success = app.getString(R.string.audio_created, result.data.generated, result.data.skipped)
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

    fun checkDuplicates() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isLoading = true,
                error = null,
                success = null,
                duplicates = emptyList()
            )
            when (val result = repo.getDuplicates()) {
                is NetworkResult.Success -> {
                    if (result.data.isEmpty()) {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            success = app.getString(R.string.no_duplicates)
                        )
                    } else {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            duplicates = result.data
                        )
                    }
                }
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> {}
            }
        }
    }

    fun clearDuplicates() {
        _uiState.value = _uiState.value.copy(duplicates = emptyList())
    }

    fun clearMessages() {
        _uiState.value = _uiState.value.copy(error = null, success = null)
    }
}
