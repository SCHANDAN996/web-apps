package com.studentstation.app.domain.model

/**
 * ब्लॉक किए गए ऐप का डोमेन मॉडल
 */
data class BlockedApp(
    val id: Long = 0,
    val packageName: String,
    val displayName: String,
    val waitTimeSeconds: Int = 30,
    val isBlocked: Boolean = true,
    val dailyLimitMinutes: Int = 0,
    val blockShorts: Boolean = true,
    val blockReels: Boolean = true,
    val timerStrategy: TimerStrategy = TimerStrategy.FIXED,
    val todayUsageMinutes: Int = 0
)

enum class TimerStrategy {
    FIXED,           // हर बार निश्चित प्रतीक्षा
    PROGRESSIVE,     // हर बार बढ़ती प्रतीक्षा
    TASK_BASED,      // गणित का सवाल हल करें
    BREATHING        // श्वसन अभ्यास
}

/**
 * फोकस सत्र का डोमेन मॉडल
 */
data class FocusSession(
    val id: Long = 0,
    val startTime: Long,
    val endTime: Long? = null,
    val plannedDurationMinutes: Int = 25,
    val isSuccessful: Boolean = false,
    val sessionType: SessionType = SessionType.POMODORO,
    val interruptions: Int = 0,
    val xpEarned: Int = 0,
    val subjectId: Long? = null
)

enum class SessionType {
    POMODORO,    // 25 min work + 5 min break
    DEEP_WORK,   // 90 min focused work
    CUSTOM       // user-defined duration
}

/**
 * उपयोग प्रयास रिकॉर्ड
 */
data class UsageRecord(
    val id: Long = 0,
    val timestamp: Long,
    val appPackage: String,
    val feature: String = "app",
    val actionTaken: String = "BLOCKED",
    val waitCompleted: Boolean = false,
    val waitDurationSeconds: Int = 0
)

/**
 * स्ट्रीक और गेमिफिकेशन जानकारी
 */
data class StreakInfo(
    val currentStreak: Int = 0,
    val longestStreak: Int = 0,
    val totalFocusMinutes: Int = 0,
    val totalXp: Int = 0,
    val level: Int = 1,
    val treesGrown: Int = 0,
    val treesWithered: Int = 0,
    val totalBlocksResisted: Int = 0
) {
    val xpForNextLevel: Int get() = level * 1000
    val xpProgress: Float get() = (totalXp % 1000).toFloat() / 1000f
}

/**
 * दैनिक सांख्यिकी
 */
data class DailyStats(
    val focusMinutes: Int = 0,
    val successfulSessions: Int = 0,
    val blocksResisted: Int = 0,
    val timesWaited: Int = 0,
    val totalAttempts: Int = 0,
    val focusScore: Int = 0 // 0-100
)
