package com.studentstation.app.presentation.features.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.studentstation.app.data.local.dao.StreakDao
import com.studentstation.app.data.local.entity.StreakEntity
import com.studentstation.app.domain.model.DailyStats
import com.studentstation.app.domain.model.StreakInfo
import com.studentstation.app.domain.usecase.GetDailyStatsUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DashboardUiState(
    val dailyStats: DailyStats = DailyStats(),
    val streakInfo: StreakInfo = StreakInfo(),
    val isLoading: Boolean = true,
    val greeting: String = ""
)

@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val getDailyStats: GetDailyStatsUseCase,
    private val streakDao: StreakDao
) : ViewModel() {

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        loadDashboard()
        observeStreak()
    }

    private fun loadDashboard() {
        viewModelScope.launch {
            try {
                val stats = getDailyStats()
                val greeting = getGreeting()
                _uiState.update {
                    it.copy(dailyStats = stats, isLoading = false, greeting = greeting)
                }
            } catch (e: Exception) {
                _uiState.update { it.copy(isLoading = false) }
            }
        }
    }

    private fun observeStreak() {
        viewModelScope.launch {
            streakDao.getStreak().collect { entity ->
                val info = entity?.let {
                    StreakInfo(
                        currentStreak = it.currentStreak,
                        longestStreak = it.longestStreak,
                        totalFocusMinutes = it.totalFocusMinutes,
                        totalXp = it.totalXp,
                        level = it.level,
                        treesGrown = it.treesGrown,
                        treesWithered = it.treesWithered,
                        totalBlocksResisted = it.totalBlocksResisted
                    )
                } ?: StreakInfo()
                _uiState.update { it.copy(streakInfo = info) }
            }
        }
    }

    fun refresh() = loadDashboard()

    private fun getGreeting(): String {
        val hour = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY)
        return when {
            hour < 6 -> "🌙 रात को भी पढ़ रहे हो? वाह!"
            hour < 12 -> "🌅 सुप्रभात! आज का दिन शानदार रहेगा"
            hour < 17 -> "☀️ दोपहर की पढ़ाई जारी रखो!"
            hour < 21 -> "🌆 शाम हो गई, अभी और फोकस करो!"
            else -> "🌙 देर रात की पढ़ाई, बहुत अच्छे!"
        }
    }
}
