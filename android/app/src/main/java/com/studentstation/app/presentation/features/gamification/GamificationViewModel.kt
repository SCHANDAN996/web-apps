package com.studentstation.app.presentation.features.gamification

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.studentstation.app.data.local.dao.StreakDao
import com.studentstation.app.data.local.dao.UsageLogDao
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class GamificationUiState(
    val treesGrown: Int = 0,
    val treesWithered: Int = 0,
    val currentStreak: Int = 0,
    val longestStreak: Int = 0,
    val totalXp: Int = 0,
    val level: Int = 1,
    val xpProgress: Float = 0f,
    val xpForNextLevel: Int = 1000,
    val totalBlocksResisted: Int = 0,
    val totalFocusMinutes: Int = 0
)

@HiltViewModel
class GamificationViewModel @Inject constructor(
    private val streakDao: StreakDao,
    private val usageLogDao: UsageLogDao
) : ViewModel() {
    private val _uiState = MutableStateFlow(GamificationUiState())
    val uiState: StateFlow<GamificationUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            streakDao.getStreak().collect { entity ->
                if (entity != null) {
                    _uiState.update {
                        it.copy(
                            treesGrown = entity.treesGrown,
                            treesWithered = entity.treesWithered,
                            currentStreak = entity.currentStreak,
                            longestStreak = entity.longestStreak,
                            totalXp = entity.totalXp,
                            level = entity.level,
                            xpProgress = (entity.totalXp % 1000).toFloat() / 1000f,
                            xpForNextLevel = entity.level * 1000,
                            totalBlocksResisted = entity.totalBlocksResisted,
                            totalFocusMinutes = entity.totalFocusMinutes
                        )
                    }
                }
            }
        }
    }
}
