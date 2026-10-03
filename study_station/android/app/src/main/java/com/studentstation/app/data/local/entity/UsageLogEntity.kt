package com.studentstation.app.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * उपयोग प्रयास लॉग — कितनी बार छात्र ने ब्लॉक स्क्रीन देखी
 */
@Entity(tableName = "usage_log")
data class UsageLogEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    @ColumnInfo(name = "timestamp")
    val timestamp: Long,

    @ColumnInfo(name = "app_package")
    val appPackage: String,

    @ColumnInfo(name = "feature")
    val feature: String = "app", // "shorts", "reels", "app"

    @ColumnInfo(name = "action_taken")
    val actionTaken: String = "BLOCKED", // "BLOCKED", "WAITED", "CLOSED", "BYPASSED"

    @ColumnInfo(name = "wait_completed")
    val waitCompleted: Boolean = false,

    @ColumnInfo(name = "wait_duration_seconds")
    val waitDurationSeconds: Int = 0
)
