package com.learnwords.app.ui.learn

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.R
import com.learnwords.app.data.api.UpdateWordRequest
import com.learnwords.app.data.api.WordDto
import com.learnwords.app.utils.NetworkResult
import com.learnwords.app.utils.getExampleByLang
import com.learnwords.app.utils.getWordByLang
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.util.TimeZone

enum class CheckResult { CORRECT, WRONG, MASTERED, NONE }

data class LearnUiState(
    val isLoading: Boolean = false,
    val words: List<WordDto> = emptyList(),
    val currentIndex: Int = 0,
    val currentWord: WordDto? = null,
    val activeLang: String = "nl",
    val availableLangs: List<String> = listOf("nl", "en", "ru"),
    val scrambledLetters: List<Char> = emptyList(),
    val placedLetters: List<Char?> = emptyList(),
    val placedLetterIndices: List<Int?> = emptyList(),
    val usedSlots: List<Int> = emptyList(),
    val checkResult: CheckResult = CheckResult.NONE,
    val showResultDialog: Boolean = false,
    val error: String? = null,
    val isFinished: Boolean = false,
    val isChild: Boolean = false,
    val todayCount: Int = 0,
    val dailyGoal: Int = 25,
    val statusMilestone: Int = 0,
    val goalType: String = "minutes",
    val goalValue: Int = 10
)

class LearnViewModel(savedStateHandle: SavedStateHandle) : ViewModel() {

    private val repo = LearnWordsApp.instance.repository
    private val prefs = LearnWordsApp.instance.preferencesManager
    private val app = LearnWordsApp.instance
    val lesson: String = savedStateHandle.get<String>("lesson") ?: ""
    private val wordSet: String = savedStateHandle.get<String>("wordSet") ?: "lesson"
    val isDifficultMode: Boolean = wordSet == "difficult"
    val lessonTitle: String = if (isDifficultMode) {
        app.getString(R.string.nav_difficult)
    } else {
        lesson
    }

    private val _uiState = MutableStateFlow(LearnUiState())
    val uiState: StateFlow<LearnUiState> = _uiState
    private var hasSubscriptionAccess = false
    private var childStatusRequestId = 0

    // Одноразовое событие: перейти на другой урок (название урока)
    private val _navigateToLesson = MutableSharedFlow<String>(extraBufferCapacity = 1)
    val navigateToLesson: SharedFlow<String> = _navigateToLesson

    init {
        loadWords()
    }

    fun loadWords() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            val accessResult = repo.getMe()
            hasSubscriptionAccess = (accessResult as? NetworkResult.Success)?.data?.let {
                it.isAdmin == true || it.subscription?.isActive == true
            } == true
            if (!hasSubscriptionAccess) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = app.getString(R.string.no_subscription)
                )
                return@launch
            }
            // Источник истины — сервер (может отличаться от локального кэша,
            // если языки были изменены с другого устройства/веба). Локальный
            // кэш используется только как офлайн-резерв.
            val languagesResult = repo.getUserLanguages()
            val langs = (languagesResult as? NetworkResult.Success)
                ?.data?.sortedBy { it.priority }?.map { it.langCode }?.ifEmpty { null }
                ?: prefs.selectedLangs.first().split(",").filter { it.isNotBlank() }

            val me = repo.getMe()
            val serverAccountType = (me as? NetworkResult.Success)?.data?.accountType
            if (serverAccountType != null) prefs.saveAccountTypeCache(serverAccountType)
            // Never fall back to "adult" just because this request failed — reuse the
            // last account_type the server confirmed (fail-safe, not fail-open).
            val effectiveAccountType = serverAccountType ?: prefs.accountTypeCache.first()
            val isChild = effectiveAccountType == "child"
            val goalResult = repo.getDailyGoal()
            val goalType = (goalResult as? NetworkResult.Success)?.data?.goalType ?: if (isChild) "words" else "minutes"
            val goalValue = (goalResult as? NetworkResult.Success)?.data?.goalValue ?: if (isChild) 25 else 10
            val words = if (isDifficultMode) {
                val result = repo.refreshDifficultWords()
                if (result is NetworkResult.Error) {
                    _uiState.value = _uiState.value.copy(error = result.message)
                }
                repo.getDifficultWordsOnce()
            } else {
                // Всегда тянем свежие данные с сервера (не только для детских
                // аккаунтов): иначе после добавления нового языка в настройках
                // урок, закэшированный до этого момента, вечно показывал бы
                // старый набор языков.
                repo.refreshWordsForLesson(lesson)
            }.filterNot { isChild && it.learned }
            if (words.isEmpty()) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = app.getString(if (isDifficultMode) R.string.no_difficult_words else R.string.words_not_found)
                )
                return@launch
            }
            // Показываем только языки, у которых в этом уроке переведены ВСЕ
            // слова (как на вебе, см. lessonHasCompleteLanguage в learn.js) —
            // а не просто все языки из настроек аккаунта. Частично переведённый
            // урок (генерация не завершена) кнопку языка не получает.
            val langsWithContent = langs.filter { lang -> words.all { !it.getWordByLang(lang).isNullOrBlank() } }
            val effectiveLangs = langsWithContent.ifEmpty { langs }
            val activeLang = effectiveLangs.firstOrNull() ?: "nl"
            _uiState.value = _uiState.value.copy(
                isLoading = false,
                words = words,
                // «Все» — первой кнопкой (как на вебе), затем языки с контентом
                availableLangs = (listOf("all") + effectiveLangs).distinct(),
                activeLang = activeLang,
                isChild = isChild,
                goalType = goalType,
                goalValue = goalValue,
                dailyGoal = if (isChild) goalValue else 25
            )
            refreshLearningStatus()
            showWord(0)
        }
    }

    fun refreshLessonContent() {
        if (!hasSubscriptionAccess || isDifficultMode || lesson.isBlank() || _uiState.value.isLoading) return
        viewModelScope.launch {
            val state = _uiState.value
            val fresh = repo.refreshWordsForLesson(lesson).filterNot { state.isChild && it.learned }
            if (fresh.isEmpty() || fresh == state.words) return@launch
            val currentId = state.currentWord?.id
            val newIndex = fresh.indexOfFirst { it.id == currentId }
                .takeIf { it >= 0 }
                ?: state.currentIndex.coerceIn(0, fresh.lastIndex)
            _uiState.value = state.copy(words = fresh, currentIndex = newIndex)
            showWord(newIndex)
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
            placedLetterIndices = List(wordText.length) { null },
            usedSlots = emptyList(),
            checkResult = CheckResult.NONE,
            showResultDialog = false
        )
    }

    fun placeLetter(letterIndex: Int) {
        placeLetterAt(letterIndex, null)
    }

    fun placeLetterAt(letterIndex: Int, requestedSlotIndex: Int?) {
        val state = _uiState.value
        val letters = state.scrambledLetters
        if (letterIndex < 0 || letterIndex >= letters.size) return
        if (letterIndex in state.usedSlots) return

        val slots = state.placedLetters.toMutableList()
        val indices = state.placedLetterIndices.toMutableList()
        val emptySlot = slots.indexOfFirst { it == null }
        if (emptySlot == -1) return
        val targetSlot = (requestedSlotIndex ?: emptySlot).coerceIn(0, emptySlot)

        for (position in emptySlot downTo targetSlot + 1) {
            slots[position] = slots[position - 1]
            indices[position] = indices[position - 1]
        }

        slots[targetSlot] = letters[letterIndex]
        indices[targetSlot] = letterIndex

        _uiState.value = state.copy(
            placedLetters = slots,
            placedLetterIndices = indices,
            usedSlots = indices.filterNotNull(),
            checkResult = CheckResult.NONE
        )
    }

    fun removePlacedLetter(slotIndex: Int) {
        val state = _uiState.value
        val slots = state.placedLetters.toMutableList()
        val indices = state.placedLetterIndices.toMutableList()
        if (slotIndex < 0 || slotIndex >= slots.size || slots[slotIndex] == null) return

        slots[slotIndex] = null
        indices[slotIndex] = null

        _uiState.value = state.copy(
            placedLetters = slots,
            placedLetterIndices = indices,
            usedSlots = indices.filterNotNull(),
            checkResult = CheckResult.NONE
        )
    }

    fun movePlacedLetter(fromSlotIndex: Int, toSlotIndex: Int) {
        val state = _uiState.value
        val slots = state.placedLetters.toMutableList()
        val indices = state.placedLetterIndices.toMutableList()
        if (fromSlotIndex !in slots.indices || toSlotIndex !in slots.indices) return
        if (slots[fromSlotIndex] == null || fromSlotIndex == toSlotIndex) return

        val movedChar = slots.removeAt(fromSlotIndex)
        val movedIndex = indices.removeAt(fromSlotIndex)
        slots.add(toSlotIndex.coerceIn(0, slots.size), movedChar)
        indices.add(toSlotIndex.coerceIn(0, indices.size), movedIndex)

        _uiState.value = state.copy(
            placedLetters = slots,
            placedLetterIndices = indices,
            usedSlots = indices.filterNotNull(),
            checkResult = CheckResult.NONE
        )
    }

    fun checkAnswer() {
        val state = _uiState.value
        if (state.checkResult != CheckResult.NONE) return
        val word = state.currentWord ?: return
        val answer = state.placedLetters.joinToString("") { it?.toString() ?: "" }
        val target = word.getWordByLang(state.activeLang) ?: ""

        val isCorrect = answer.equals(target, ignoreCase = true)

        val newPlacedLetters = if (!isCorrect) target.map { it } else state.placedLetters
        val newUsedSlots = if (!isCorrect) state.scrambledLetters.indices.toList() else state.usedSlots
        val newPlacedLetterIndices = if (!isCorrect) {
            state.scrambledLetters.indices.map { it }
        } else state.placedLetterIndices

        val updatedWord = if (isCorrect && state.isChild) word.copy(
            practiceCount = word.practiceCount + 1,
            learned = word.practiceCount + 1 >= 10
        ) else word
        // A word that just crossed the mastery threshold no longer counts toward the
        // daily goal server-side, so it's highlighted blue instead of green.
        val result = when {
            !isCorrect -> CheckResult.WRONG
            state.isChild && updatedWord.learned -> CheckResult.MASTERED
            else -> CheckResult.CORRECT
        }
        val updatedWords = state.words.toMutableList().apply {
            this[state.currentIndex] = updatedWord
        }
        _uiState.value = state.copy(
            words = updatedWords,
            currentWord = updatedWord,
            checkResult = result,
            showResultDialog = false,
            placedLetters = newPlacedLetters,
            placedLetterIndices = newPlacedLetterIndices,
            usedSlots = newUsedSlots
        )
        if (isCorrect && state.isChild) {
            advanceChildGoalOptimistically()
        }

        viewModelScope.launch {
            val progressState = JSONObject().apply {
                put("word_id", word.id)
                put("lesson", lesson)
                put("index", state.currentIndex)
                put("total", state.words.size)
                put("passed", if (isCorrect) state.currentIndex + 1 else state.currentIndex)
                put("lang", state.activeLang)
                put("reason", if (isCorrect) "answer_ok" else "answer_fail")
                put("tz_offset", -(TimeZone.getDefault().getOffset(System.currentTimeMillis()) / 60000))
            }
            repo.queueProgress(
                scope = "learn",
                eventType = if (isCorrect) "word_correct" else "word_wrong",
                payloadJson = progressState.toString()
            )
            repo.syncPendingProgress()
            if (isCorrect) refreshLearningStatus()
        }
    }

    private suspend fun refreshLearningStatus() {
        if (!_uiState.value.isChild) return
        val requestId = ++childStatusRequestId
        val now = System.currentTimeMillis()
        val offset = -(TimeZone.getDefault().getOffset(now) / 60000)
        when (val result = repo.getChildLearningStatus(offset)) {
            is NetworkResult.Success -> if (requestId == childStatusRequestId) {
                _uiState.value = _uiState.value.copy(
                    todayCount = result.data.todayCount,
                    dailyGoal = result.data.dailyGoal,
                    statusMilestone = result.data.statusMilestone
                )
            }
            else -> Unit
        }
    }

    private fun advanceChildGoalOptimistically() {
        val state = _uiState.value
        if (!state.isChild || state.todayCount >= state.dailyGoal) return
        val todayCount = state.todayCount + 1
        val milestone = listOf(5, 10, 15, 20, 25).lastOrNull { todayCount >= it } ?: 0
        _uiState.value = state.copy(todayCount = todayCount, statusMilestone = milestone)
    }

    fun nextWord() {
        val state = _uiState.value
        if (state.currentWord?.learned == true) {
            val remaining = state.words.filterNot { it.id == state.currentWord.id }
            if (remaining.isEmpty()) {
                _uiState.value = state.copy(words = emptyList(), currentWord = null, isFinished = true)
            } else {
                _uiState.value = state.copy(words = remaining)
                showWord(state.currentIndex.coerceAtMost(remaining.lastIndex))
            }
            return
        }
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

    /** Перейти на следующий видимый урок (в режиме «сложные слова» недоступно). */
    fun goToNextLesson() {
        if (isDifficultMode) return
        viewModelScope.launch {
            val next = repo.getNextLessonTitle(lesson)
            if (next.isNullOrBlank() || next == lesson) {
                _uiState.value = _uiState.value.copy(error = app.getString(R.string.no_more_lessons))
            } else {
                _navigateToLesson.emit(next)
            }
        }
    }

    /** Перейти на предыдущий видимый урок (в режиме «сложные слова» недоступно). */
    fun goToPrevLesson() {
        if (isDifficultMode) return
        viewModelScope.launch {
            val prev = repo.getPrevLessonTitle(lesson)
            if (prev.isNullOrBlank() || prev == lesson) {
                _uiState.value = _uiState.value.copy(error = app.getString(R.string.no_prev_lessons))
            } else {
                _navigateToLesson.emit(prev)
            }
        }
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
                    val refreshed = if (isDifficultMode) {
                        repo.getDifficultWordsOnce()
                    } else {
                        repo.getCachedWordsForLesson(lesson)
                    }
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
                    _uiState.value = state.copy(error = app.getString(R.string.audio_prepare_failed))
                }
                else -> Unit
            }
        }
    }

    fun toggleDifficult() {
        val word = _uiState.value.currentWord ?: return
        val newDifficult = !word.difficult
        viewModelScope.launch {
            when (val result = repo.setDifficult(word.id, newDifficult)) {
                is NetworkResult.Success -> {
                    if (isDifficultMode && !newDifficult) {
                        removeCurrentWordFromSession(word.id)
                        return@launch
                    }

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
                is NetworkResult.Error -> {
                    _uiState.value = _uiState.value.copy(error = result.message)
                }
                else -> Unit
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
                        showWordsAfterRemoval(state, words)
                    }
                }
                is NetworkResult.Error -> {
                    _uiState.value = _uiState.value.copy(error = app.getString(R.string.word_delete_failed))
                }
                else -> {}
            }
        }
    }

    private fun removeCurrentWordFromSession(wordId: Int) {
        val state = _uiState.value
        val words = state.words.filter { it.id != wordId }
        if (words.isEmpty()) {
            _uiState.value = state.copy(words = emptyList(), isFinished = true)
            return
        }
        showWordsAfterRemoval(state, words)
    }

    private fun showWordsAfterRemoval(previousState: LearnUiState, words: List<WordDto>) {
        _uiState.value = previousState.copy(words = words)
        val newIndex = minOf(previousState.currentIndex, words.size - 1)
        showWord(newIndex)
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
                            placedLetterIndices = if (!isExample && lang == state.activeLang) {
                                List(cleaned.length) { null }
                            } else state.placedLetterIndices,
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
                    _uiState.value = state.copy(error = app.getString(R.string.changes_save_failed))
                }
                else -> Unit
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
