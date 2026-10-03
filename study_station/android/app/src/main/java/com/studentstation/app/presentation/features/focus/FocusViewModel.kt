package com.studentstation.app.presentation.features.focus

import android.content.Context
import android.content.Intent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.studentstation.app.domain.model.FocusSession
import com.studentstation.app.domain.model.SessionType
import com.studentstation.app.domain.usecase.EndFocusSessionUseCase
import com.studentstation.app.domain.usecase.StartFocusSessionUseCase
import com.studentstation.app.service.PomodoroService
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

enum class SessionState { IDLE, WORKING, BREAK, PAUSED }

data class FocusUiState(
    val sessionState: SessionState = SessionState.IDLE,
    val remainingSeconds: Int = 25 * 60,
    val totalSeconds: Int = 25 * 60,
    val progress: Float = 1f,
    val selectedType: String = "POMODORO",
    val customMinutes: Int = 30,
    val currentSessionId: Long = 0,
    val subjectId: Long? = null,
    val subjectName: String? = null
)

@HiltViewModel
class FocusViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val startFocusSession: StartFocusSessionUseCase,
    private val endFocusSession: EndFocusSessionUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(FocusUiState())
    val uiState: StateFlow<FocusUiState> = _uiState.asStateFlow()

    fun selectType(type: String) {
        val minutes = when (type) {
            "POMODORO" -> 25
            "DEEP_WORK" -> 90
            else -> _uiState.value.customMinutes
        }
        _uiState.update {
            it.copy(
                selectedType = type,
                remainingSeconds = minutes * 60,
                totalSeconds = minutes * 60
            )
        }
    }

    fun setCustomMinutes(minutes: Int) {
        _uiState.update {
            it.copy(customMinutes = minutes, remainingSeconds = minutes * 60, totalSeconds = minutes * 60)
        }
    }

    fun setSubject(id: Long, name: String) {
        _uiState.update {
            it.copy(subjectId = id, subjectName = name)
        }
    }

    fun clearSubject() {
        _uiState.update {
            it.copy(subjectId = null, subjectName = null)
        }
    }

    fun startSession() {
        viewModelScope.launch {
            val minutes = when (_uiState.value.selectedType) {
                "POMODORO" -> 25
                "DEEP_WORK" -> 90
                else -> _uiState.value.customMinutes
            }
            val session = FocusSession(
                startTime = System.currentTimeMillis(),
                plannedDurationMinutes = minutes,
                sessionType = SessionType.valueOf(_uiState.value.selectedType),
                subjectId = _uiState.value.subjectId
            )
            val id = startFocusSession(session)

            _uiState.update {
                it.copy(
                    sessionState = SessionState.WORKING,
                    totalSeconds = minutes * 60,
                    remainingSeconds = minutes * 60,
                    currentSessionId = id
                )
            }

            // Start Pomodoro service
            val intent = Intent(context, PomodoroService::class.java).apply {
                action = PomodoroService.ACTION_START
                putExtra(PomodoroService.EXTRA_WORK_MINUTES, minutes)
            }
            context.startForegroundService(intent)

            // Update UI from service
            PomodoroService.onTickCallback = { remaining, total, state ->
                _uiState.update {
                    it.copy(
                        remainingSeconds = remaining,
                        totalSeconds = total,
                        progress = remaining.toFloat() / total,
                        sessionState = when (state) {
                            PomodoroService.PomodoroState.WORKING -> SessionState.WORKING
                            PomodoroService.PomodoroState.BREAK -> SessionState.BREAK
                            PomodoroService.PomodoroState.PAUSED -> SessionState.PAUSED
                            else -> SessionState.IDLE
                        }
                    )
                }
            }
        }
    }

    fun pauseSession() {
        val intent = Intent(context, PomodoroService::class.java).apply {
            action = PomodoroService.ACTION_PAUSE
        }
        context.startService(intent)
        _uiState.update { it.copy(sessionState = SessionState.PAUSED) }
    }

    fun resumeSession() {
        val intent = Intent(context, PomodoroService::class.java).apply {
            action = PomodoroService.ACTION_RESUME
        }
        context.startService(intent)
        _uiState.update { it.copy(sessionState = SessionState.WORKING) }
    }

    fun stopSession() {
        viewModelScope.launch {
            val state = _uiState.value
            val session = FocusSession(
                id = state.currentSessionId,
                startTime = System.currentTimeMillis() - ((state.totalSeconds - state.remainingSeconds) * 1000L),
                endTime = System.currentTimeMillis(),
                isSuccessful = state.remainingSeconds <= 0,
                sessionType = SessionType.valueOf(state.selectedType),
                subjectId = state.subjectId
            )
            endFocusSession(session)
        }
        context.stopService(Intent(context, PomodoroService::class.java))
        PomodoroService.onTickCallback = null
        _uiState.update {
            FocusUiState(
                selectedType = it.selectedType, 
                customMinutes = it.customMinutes,
                subjectId = it.subjectId,
                subjectName = it.subjectName
            )
        }
    }
}
