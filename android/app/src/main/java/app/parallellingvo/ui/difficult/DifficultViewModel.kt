package app.parallellingvo.ui.difficult

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import app.parallellingvo.ParallelLingvoApp
import app.parallellingvo.data.api.WordDto
import app.parallellingvo.data.db.WordEntity
import app.parallellingvo.utils.NetworkResult
import app.parallellingvo.utils.toDto
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class DifficultUiState(
    val isLoading: Boolean = false,
    val error: String? = null
)

class DifficultViewModel : ViewModel() {

    private val repo = ParallelLingvoApp.instance.repository

    private val _uiState = MutableStateFlow(DifficultUiState())
    val uiState: StateFlow<DifficultUiState> = _uiState

    val words: StateFlow<List<WordEntity>> = repo.getDifficultWordsFlow()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            when (val result = repo.refreshDifficultWords()) {
                is NetworkResult.Error -> _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = result.message
                )
                else -> _uiState.value = _uiState.value.copy(isLoading = false)
            }
        }
    }

    fun unmarkDifficult(wordId: Int) {
        viewModelScope.launch {
            repo.setDifficult(wordId, false)
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
