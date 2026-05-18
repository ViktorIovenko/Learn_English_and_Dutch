package com.learnwords.app.ui.learn

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.data.api.UpdateWordRequest
import com.learnwords.app.data.api.WordDto
import com.learnwords.app.utils.NetworkResult
import com.learnwords.app.utils.getExampleByLang
import com.learnwords.app.utils.getWordByLang
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

enum class CheckResult { CORRECT, WRONG, NONE }

data class LearnUiState(
    val isLoading: Boolean = false,
    val words: List<WordDto> = emptyList(),
    val currentIndex: Int = 0,
    val currentWord: WordDto? = null,
    val activeLang: String = "nl",
    val availableLangs: List<String> = listOf("nl", "en", "ru"),
    val scrambledLetters: List<Char> = emptyList(),
    val placedLetters: List<Char?> = emptyList(),
    val usedSlots: List<Int> = emptyList(),
    val checkResult: CheckResult = CheckResult.NONE,
    val showResultDialog: Boolean = false,
    val error: String? = null,
    val isFinished: Boolean = false
)

class LearnViewModel(savedStateHandle: SavedStateHandle) : ViewModel() {

    private val repo = LearnWordsApp.instance.repository
    private val prefs = LearnWordsApp.instance.preferencesManager
    val lesson: String = savedStateHandle.get<String>("lesson") ?: ""

    private val _uiState = MutableStateFlow(LearnUiState())
    val uiState: StateFlow<LearnUiState> = _uiState

    init {
        loadWords()
    }

    fun loadWords() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            val langsCsv = prefs.selectedLangs.first()
            val langs = langsCsv.split(",").filter { it.isNotBlank() }
            val activeLang = langs.firstOrNull() ?: "nl"

            val words = repo.getWordsForLesson(lesson)
            if (words.isEmpty()) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "Слова не найдены"
                )
                return@launch
            }
            _uiState.value = _uiState.value.copy(
                isLoading = false,
                words = words,
                availableLangs = langs,
                activeLang = activeLang
            )
            showWord(0)
        }
    }

    fun setActiveLang(lang: String) {
        _uiState.value = _uiState.value.copy(activeLang = lang)
        showWord(_uiState.value.currentIndex)
    }

    fun showWord(index: Int) {
        val state = _uiState.value
        val words = state.words
        if (words.isEmpty() || index < 0 || index >= words.size) return

        val word = words[index]
        val wordText = word.getWordByLang(state.activeLang) ?: ""
        val letters = wordText.toMutableList().apply { shuffle() }
        val slots = MutableList<Char?>(wordText.length) { null }

        _uiState.value = state.copy(
            currentIndex = index,
            currentWord = word,
            scrambledLetters = letters,
            placedLetters = slots,
            usedSlots = emptyList(),
            checkResult = CheckResult.NONE,
            showResultDialog = false
        )
    }

    fun placeLetter(letterIndex: Int) {
        val state = _uiState.value
        val letters = state.scrambledLetters
        if (letterIndex < 0 || letterIndex >= letters.size) return

        // Find first empty answer slot
        val slots = state.placedLetters.toMutableList()
        val emptySlot = slots.indexOfFirst { it == null }
        if (emptySlot == -1) return

        slots[emptySlot] = letters[letterIndex]
        val usedSlots = state.usedSlots + letterIndex

        _uiState.value = state.copy(
            placedLetters = slots,
            usedSlots = usedSlots,
            checkResult = CheckResult.NONE
        )
    }

    fun removePlacedLetter(slotIndex: Int) {
        val state = _uiState.value
        val slots = state.placedLetters.toMutableList()
        if (slotIndex < 0 || slotIndex >= slots.size || slots[slotIndex] == null) return

        // Find corresponding source letter to un-use
        val removedChar = slots[slotIndex]
        slots[slotIndex] = null

        // Remove last usage of this character from usedSlots
        val usedSlots = state.usedSlots.toMutableList()
        val sourceIdx = state.scrambledLetters.indices
            .filter { it in usedSlots && state.scrambledLetters[it] == removedChar }
            .lastOrNull()
        if (sourceIdx != null) usedSlots.remove(sourceIdx)

        _uiState.value = state.copy(
            placedLetters = slots,
            usedSlots = usedSlots,
            checkResult = CheckResult.NONE
        )
    }

    fun checkAnswer() {
        val state = _uiState.value
        val word = state.currentWord ?: return
        val answer = state.placedLetters.joinToString("") { it?.toString() ?: "" }
        val target = word.getWordByLang(state.activeLang) ?: ""

        val isCorrect = answer.equals(target, ignoreCase = true)
        val result = if (isCorrect) CheckResult.CORRECT else CheckResult.WRONG

        _uiState.value = state.copy(
            checkResult = result,
            showResultDialog = result == CheckResult.WRONG
        )

        if (isCorrect) {
            viewModelScope.launch {
                repo.queueProgress(
                    scope = "learn",
                    eventType = "word_correct",
                    payloadJson = """{"word_id":${word.id},"lesson":"${lesson}"}"""
                )
            }
        }
    }

    fun nextWord() {
        val state = _uiState.value
        val nextIndex = state.currentIndex + 1
        if (nextIndex >= state.words.size) {
            _uiState.value = state.copy(isFinished = true, showResultDialog = false)
        } else {
            showWord(nextIndex)
        }
    }

    fun previousWord() {
        val state = _uiState.value
        val prevIndex = state.currentIndex - 1
        if (prevIndex >= 0) showWord(prevIndex)
    }

    fun dismissResult() {
        _uiState.value = _uiState.value.copy(showResultDialog = false)
    }

    fun ensureAudioForCurrent(lang: String) {
        val state = _uiState.value
        val word = state.currentWord ?: return
        viewModelScope.launch {
            when (repo.ensureAudio(listOf(word.id), listOf(lang))) {
                is NetworkResult.Success -> {
                    val refreshed = repo.refreshWordsForLesson(lesson)
                    if (refreshed.isNotEmpty()) {
                        val index = state.currentIndex.coerceAtMost(refreshed.lastIndex)
                        _uiState.value = state.copy(
                            words = refreshed,
                            currentWord = refreshed[index],
                            currentIndex = index
                        )
                    }
                }
                is NetworkResult.Error -> {
                    _uiState.value = state.copy(error = "Не удалось подготовить аудио")
                }
                else -> Unit
            }
        }
    }

    fun toggleDifficult() {
        val word = _uiState.value.currentWord ?: return
        val newDifficult = !word.difficult
        viewModelScope.launch {
            repo.setDifficult(word.id, newDifficult)
            // Update local state
            val words = _uiState.value.words.toMutableList()
            val idx = words.indexOfFirst { it.id == word.id }
            if (idx != -1) {
                words[idx] = word.copy(difficult = newDifficult)
                _uiState.value = _uiState.value.copy(
                    words = words,
                    currentWord = words[idx]
                )
            }
        }
    }

    fun deleteCurrentWord() {
        val word = _uiState.value.currentWord ?: return
        viewModelScope.launch {
            when (repo.deleteWord(word.id)) {
                is NetworkResult.Success -> {
                    val state = _uiState.value
                    val words = state.words.filter { it.id != word.id }
                    if (words.isEmpty()) {
                        _uiState.value = state.copy(words = emptyList(), isFinished = true)
                    } else {
                        _uiState.value = state.copy(words = words)
                        val newIndex = minOf(state.currentIndex, words.size - 1)
                        showWord(newIndex)
                    }
                }
                is NetworkResult.Error -> {
                    _uiState.value = _uiState.value.copy(error = "Не удалось удалить слово")
                }
                else -> {}
            }
        }
    }

    fun updateCurrentText(lang: String, isExample: Boolean, value: String) {
        val state = _uiState.value
        val word = state.currentWord ?: return
        val cleaned = value.trim()
        val oldValue = if (isExample) {
            word.getExampleByLang(lang).orEmpty()
        } else {
            word.getWordByLang(lang).orEmpty()
        }.trim()
        if (cleaned == oldValue) return

        val request = when {
            !isExample && lang == "nl" -> UpdateWordRequest(nl = cleaned)
            !isExample && lang == "en" -> UpdateWordRequest(en = cleaned)
            !isExample && lang == "ru" -> UpdateWordRequest(ru = cleaned)
            isExample && lang == "nl" -> UpdateWordRequest(exNl = cleaned)
            isExample && lang == "en" -> UpdateWordRequest(exEn = cleaned)
            isExample && lang == "ru" -> UpdateWordRequest(exRu = cleaned)
            else -> return
        }

        viewModelScope.launch {
            when (val result = repo.updateWord(word.id, request)) {
                is NetworkResult.Success -> {
                    val updated = result.data
                    val words = state.words.map { if (it.id == updated.id) updated else it }
                    _uiState.value = state.copy(
                        words = words,
                        currentWord = updated,
                        placedLetters = if (!isExample && lang == state.activeLang) {
                            List(cleaned.length) { null }
                        } else state.placedLetters,
                        scrambledLetters = if (!isExample && lang == state.activeLang) {
                            cleaned.toMutableList().apply { shuffle() }
                        } else state.scrambledLetters,
                        usedSlots = if (!isExample && lang == state.activeLang) emptyList() else state.usedSlots,
                        checkResult = if (!isExample && lang == state.activeLang) CheckResult.NONE else state.checkResult,
                        showResultDialog = false,
                        error = null
                    )
                }
                is NetworkResult.Error -> {
                    _uiState.value = state.copy(error = "Не удалось сохранить изменения")
                }
                else -> Unit
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
