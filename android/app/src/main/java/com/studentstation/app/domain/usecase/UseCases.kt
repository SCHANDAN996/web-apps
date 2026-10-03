package com.studentstation.app.domain.usecase

import com.studentstation.app.domain.model.BlockedApp
import com.studentstation.app.domain.model.DailyStats
import com.studentstation.app.domain.model.FocusSession
import com.studentstation.app.domain.model.UsageRecord
import com.studentstation.app.domain.repository.AppConfigRepository
import com.studentstation.app.domain.repository.FocusSessionRepository
import com.studentstation.app.domain.repository.UsageLogRepository
import java.util.Calendar
import javax.inject.Inject

/**
 * जांच करें कि वर्तमान ऐप/फीचर ब्लॉक है या नहीं
 */
class CheckIfBlockedUseCase @Inject constructor(
    private val appConfigRepo: AppConfigRepository
) {
    suspend operator fun invoke(packageName: String, feature: String = "app"): BlockedApp? {
        val config = appConfigRepo.getConfigByPackage(packageName) ?: return null
        if (!config.isBlocked) return null

        // Sub-component level check
        return when {
            feature == "shorts" && config.blockShorts -> config
            feature == "reels" && config.blockReels -> config
            feature == "app" -> config
            else -> null
        }
    }
}

/**
 * पोमोडोरो/डीप वर्क सत्र प्रारंभ करें
 */
class StartFocusSessionUseCase @Inject constructor(
    private val focusSessionRepo: FocusSessionRepository
) {
    suspend operator fun invoke(session: FocusSession): Long {
        return focusSessionRepo.startSession(session)
    }
}

/**
 * फोकस सत्र समाप्त करें
 */
class EndFocusSessionUseCase @Inject constructor(
    private val focusSessionRepo: FocusSessionRepository
) {
    suspend operator fun invoke(session: FocusSession) {
        focusSessionRepo.updateSession(session)
    }
}

/**
 * उपयोग प्रयास लॉग करें
 */
class LogUsageAttemptUseCase @Inject constructor(
    private val usageLogRepo: UsageLogRepository
) {
    suspend operator fun invoke(
        appPackage: String,
        feature: String = "app",
        actionTaken: String = "BLOCKED",
        waitCompleted: Boolean = false,
        waitDurationSeconds: Int = 0
    ) {
        usageLogRepo.logUsage(
            UsageRecord(
                timestamp = System.currentTimeMillis(),
                appPackage = appPackage,
                feature = feature,
                actionTaken = actionTaken,
                waitCompleted = waitCompleted,
                waitDurationSeconds = waitDurationSeconds
            )
        )
    }
}

/**
 * दैनिक आंकड़े प्राप्त करें
 */
class GetDailyStatsUseCase @Inject constructor(
    private val focusSessionRepo: FocusSessionRepository,
    private val usageLogRepo: UsageLogRepository
) {
    suspend operator fun invoke(): DailyStats {
        val startOfDay = getStartOfDay()
        val focusMinutes = focusSessionRepo.getTotalFocusMinutesToday(startOfDay)
        val successfulSessions = focusSessionRepo.getSuccessfulSessionsToday(startOfDay)
        val blocksResisted = usageLogRepo.getBlocksResistedToday(startOfDay)
        val timesWaited = usageLogRepo.getTimesWaitedToday(startOfDay)
        val totalAttempts = usageLogRepo.getTotalAttemptsToday(startOfDay)

        // Focus Score calculation (0-100)
        val focusScore = calculateFocusScore(
            focusMinutes, successfulSessions, blocksResisted, totalAttempts
        )

        return DailyStats(
            focusMinutes = focusMinutes,
            successfulSessions = successfulSessions,
            blocksResisted = blocksResisted,
            timesWaited = timesWaited,
            totalAttempts = totalAttempts,
            focusScore = focusScore
        )
    }

    private fun calculateFocusScore(
        focusMin: Int, sessions: Int, resisted: Int, attempts: Int
    ): Int {
        var score = 0
        // Focus time contribution (max 40 points)
        score += minOf(40, focusMin * 40 / 120)
        // Successful sessions (max 30 points)
        score += minOf(30, sessions * 10)
        // Resistance ratio (max 30 points)
        if (attempts > 0) {
            score += (resisted.toFloat() / attempts * 30).toInt()
        } else {
            score += 30 // No distractions = perfect
        }
        return minOf(100, score)
    }

    private fun getStartOfDay(): Long {
        val cal = Calendar.getInstance()
        cal.set(Calendar.HOUR_OF_DAY, 0)
        cal.set(Calendar.MINUTE, 0)
        cal.set(Calendar.SECOND, 0)
        cal.set(Calendar.MILLISECOND, 0)
        return cal.timeInMillis
    }
}
