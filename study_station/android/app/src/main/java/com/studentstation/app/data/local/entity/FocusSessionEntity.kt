package com.studentstation.app.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * छात्र के पढ़ाई सत्रों का रिकॉर्ड
 */
@Entity(tableName = "focus_session")
data class FocusSessionEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    @ColumnInfo(name = "start_time")
    val startTime: Long,

    @ColumnInfo(name = "end_time")
    val endTime: Long? = null,

    @ColumnInfo(name = "planned_duration_minutes")
    val plannedDurationMinutes: Int = 25,

    @ColumnInfo(name = "is_successful")
    val isSuccessful: Boolean = false,

    @ColumnInfo(name = "session_type")
    val sessionType: String = "POMODORO", // POMODORO, DEEP_WORK, CUSTOM

    @ColumnInfo(name = "interruptions")
    val interruptions: Int = 0,

    @ColumnInfo(name = "interrupted_apps")
    val interruptedApps: String = "", // comma-separated package names

    @ColumnInfo(name = "xp_earned")
    val xpEarned: Int = 0,

    @ColumnInfo(name = "subject_id")
    val subjectId: Long? = null
)
