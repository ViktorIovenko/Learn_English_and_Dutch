package com.learnwords.app.ui.lessons

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.data.db.LessonCacheEntity
import com.learnwords.app.utils.NetworkResult
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.TimeZone

data class LessonsUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val selectedForDelete: Set<String> = emptySet(),
    val isDeleteMode: Boolean = false,
    val learningStreakDays: Int = 0,
    val isChild: Boolean = false,
    val todayCorrectWords: Int = 0,
    val todayGoal: Int = 25,
    val dailyGoalMinutes: Int = 10
)

class LessonsViewModel : ViewModel() {

    private val repo = LearnWordsApp.instance.repository

    private val _uiState = MutableStateFlow(LessonsUiState())
    val uiState: StateFlow<LessonsUiState> = _uiState

    val lessons: StateFlow<List<LessonCacheEntity>> = repo.getLessonsFlow()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            val now = System.currentTimeMillis()
            val timezoneOffsetMinutes = TimeZone.getDefault().getOffset(now) / 60_000
            val streak = repo.getLearningStreak(timezoneOffsetMinutes)
            if (streak is NetworkResult.Success) {
                _uiState.value = _uiState.value.copy(learningStreakDays = streak.data.learningStreakDays)
            }
            val childStatus = repo.getChildLearningStatus(timezoneOffsetMinutes)
            if (childStatus is NetworkResult.Success) {
                _uiState.value = _uiState.value.copy(
                    isChild = childStatus.data.isChild,
                    todayCorrectWords = childStatus.data.todayCount,
                    todayGoal = childStatus.data.dailyGoal
                )
            }
            if (!_uiState.value.isChild) {
                val goalResult = repo.getDailyGoal()
                if (goalResult is NetworkResult.Success && goalResult.data.goalType == "minutes") {
                    _uiState.value = _uiState.value.copy(dailyGoalMinutes = goalResult.data.goalValue)
                }
            }
            when (val result = repo.refreshLessons()) {
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> _uiState.value = _uiState.value.copy(isLoading = false)
            }
        }
    }

    fun toggleHidden(lesson: String, currentlyHidden: Boolean) {
        viewModelScope.launch {
            repo.setLessonHidden(lesson, !currentlyHidden)
        }
    }

    fun markLessonOpened(lesson: String) {
        viewModelScope.launch {
            repo.markLessonOpened(lesson)
        }
    }

    fun toggleDeleteSelection(lesson: String) {
        val current = _uiState.value.selectedForDelete.toMutableSet()
        if (lesson in current) current.remove(lesson) else current.add(lesson)
        _uiState.value = _uiState.value.copy(selectedForDelete = current)
    }

    fun enterDeleteMode() {
        _uiState.value = _uiState.value.copy(isDeleteMode = true, selectedForDelete = emptySet())
    }

    fun exitDeleteMode() {
        _uiState.value = _uiState.value.copy(isDeleteMode = false, selectedForDelete = emptySet())
    }

    fun deleteSelected() {
        val toDelete = _uiState.value.selectedForDelete.toList()
        if (toDelete.isEmpty()) return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            when (val result = repo.deleteLessons(toDelete)) {
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false, isDeleteMode = false,
                    error = result.message
                )
                else -> _uiState.value = _uiState.value.copy(
                    isLoading = false, isDeleteMode = false,
                    selectedForDelete = emptySet()
                )
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
