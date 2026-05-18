package com.learnwords.app.ui.lessons

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.data.db.LessonCacheEntity
import com.learnwords.app.utils.NetworkResult
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class LessonsUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val selectedForDelete: Set<String> = emptySet(),
    val isDeleteMode: Boolean = false
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
