package com.learnwords.app.ui.parent

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.data.api.ChildDashboardDto
import com.learnwords.app.utils.NetworkResult
import java.util.TimeZone
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class ParentDashboardUiState(
    val isLoading: Boolean = false,
    val days: Int = 30,
    val children: List<ChildDashboardDto> = emptyList(),
    val selectedChildId: String = "",
    val error: String? = null,
    val accessRevoked: Boolean = false
)

class ParentDashboardViewModel : ViewModel() {
    private val repository = LearnWordsApp.instance.repository
    private val _uiState = MutableStateFlow(ParentDashboardUiState())
    val uiState: StateFlow<ParentDashboardUiState> = _uiState
    private var loadRequestId = 0

    init {
        load()
    }

    fun refresh() = load(_uiState.value.days)

    fun setDays(days: Int) {
        if (days !in setOf(7, 30, 90) || days == _uiState.value.days) return
        load(days)
    }

    fun selectChild(childId: String) {
        if (_uiState.value.children.none { it.userId == childId }) return
        _uiState.value = _uiState.value.copy(selectedChildId = childId)
    }

    fun setPriorityLesson(lesson: String) {
        val state = _uiState.value
        val childId = state.selectedChildId
        if (childId.isBlank() || state.isLoading) return
        viewModelScope.launch {
            _uiState.value = state.copy(isLoading = true, error = null)
            when (val result = repository.setPriorityLesson(childId, lesson)) {
                is NetworkResult.Success -> {
                    _uiState.value = state.copy(
                        isLoading = false,
                        children = state.children.map { child ->
                            if (child.userId == childId) {
                                child.copy(priorityLesson = result.data.priorityLesson)
                            } else child
                        }
                    )
                    load(state.days)
                }
                is NetworkResult.Error -> _uiState.value = state.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> Unit
            }
        }
    }

    fun unlinkChild(childId: String) {
        val state = _uiState.value
        if (childId.isBlank() || state.isLoading) return
        viewModelScope.launch {
            _uiState.value = state.copy(isLoading = true, error = null)
            when (val result = repository.unlinkChild(childId)) {
                is NetworkResult.Success -> {
                    val remaining = state.children.filterNot { it.userId == childId }
                    if (remaining.isEmpty()) {
                        _uiState.value = state.copy(
                            isLoading = false,
                            children = emptyList(),
                            selectedChildId = "",
                            accessRevoked = true
                        )
                    } else {
                        _uiState.value = state.copy(
                            children = remaining,
                            selectedChildId = remaining.first().userId
                        )
                        load(state.days)
                    }
                }
                is NetworkResult.Error -> _uiState.value = state.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> Unit
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    private fun load(days: Int = _uiState.value.days) {
        val requestId = ++loadRequestId
        viewModelScope.launch {
            val previous = _uiState.value
            _uiState.value = previous.copy(isLoading = true, days = days, error = null)
            val now = System.currentTimeMillis()
            val timezoneOffsetMinutes = TimeZone.getDefault().getOffset(now) / 60_000
            val result = repository.getFamilyDashboard(days, timezoneOffsetMinutes)
            if (requestId != loadRequestId) return@launch // a newer request already resolved
            when (result) {
                is NetworkResult.Success -> {
                    val children = result.data.children
                    val selectedId = previous.selectedChildId
                        .takeIf { id -> children.any { it.userId == id } }
                        ?: children.firstOrNull()?.userId.orEmpty()
                    _uiState.value = ParentDashboardUiState(
                        isLoading = false,
                        days = days,
                        children = children,
                        selectedChildId = selectedId,
                        accessRevoked = children.isEmpty()
                    )
                }
                is NetworkResult.Error -> _uiState.value = previous.copy(
                    isLoading = false,
                    days = days,
                    error = if (result.code == 403) null else result.message,
                    accessRevoked = result.code == 403
                )
                else -> Unit
            }
        }
    }
}
