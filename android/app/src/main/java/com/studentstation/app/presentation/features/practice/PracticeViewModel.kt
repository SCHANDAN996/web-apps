package com.studentstation.app.presentation.features.practice

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.studentstation.app.data.remote.api.StudentStationApi
import com.studentstation.app.data.remote.dto.PracticeQuestionDto
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class PracticeUiState(
    val questions: List<PracticeQuestionDto> = emptyList(),
    val currentQuestionIndex: Int = 0,
    val selectedOption: String? = null,
    val isSubmitted: Boolean = false,
    val score: Int = 0,
    val isFinished: Boolean = false,
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class PracticeViewModel @Inject constructor(
    private val api: StudentStationApi
) : ViewModel() {

    private val _uiState = MutableStateFlow(PracticeUiState())
    val uiState: StateFlow<PracticeUiState> = _uiState.asStateFlow()

    init {
        loadQuestions("Board Exam 2024")
    }

    fun loadQuestions(examName: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            try {
                val response = api.getPracticeQuestions(examName)
                if (response.success) {
                    _uiState.value = _uiState.value.copy(
                        questions = response.data,
                        isLoading = false
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        error = "Failed to load questions",
                        isLoading = false
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    error = e.message ?: "An error occurred",
                    isLoading = false
                )
            }
        }
    }

    fun selectOption(option: String) {
        if (!_uiState.value.isSubmitted) {
            _uiState.value = _uiState.value.copy(selectedOption = option)
        }
    }

    fun submitAnswer() {
        val currentState = _uiState.value
        if (currentState.selectedOption == null || currentState.isSubmitted) return

        val currentQuestion = currentState.questions[currentState.currentQuestionIndex]
        val isCorrect = currentState.selectedOption == currentQuestion.correctAnswer
        val newScore = if (isCorrect) currentState.score + 1 else currentState.score

        _uiState.value = currentState.copy(
            isSubmitted = true,
            score = newScore
        )
    }

    fun nextQuestion() {
        val currentState = _uiState.value
        if (currentState.currentQuestionIndex < currentState.questions.size - 1) {
            _uiState.value = currentState.copy(
                currentQuestionIndex = currentState.currentQuestionIndex + 1,
                selectedOption = null,
                isSubmitted = false
            )
        } else {
            _uiState.value = currentState.copy(isFinished = true)
        }
    }

    fun restartQuiz() {
        _uiState.value = _uiState.value.copy(
            currentQuestionIndex = 0,
            selectedOption = null,
            isSubmitted = false,
            score = 0,
            isFinished = false
        )
    }
}
