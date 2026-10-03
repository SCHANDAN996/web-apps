package com.studentstation.app.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * ब्लॉक किए गए ऐप्स की सेटिंग्स
 * Each row = one app/feature configuration
 */
@Entity(tableName = "app_config")
data class AppConfigEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    @ColumnInfo(name = "package_name")
    val packageName: String,

    @ColumnInfo(name = "display_name")
    val displayName: String,

    @ColumnInfo(name = "wait_time_seconds")
    val waitTimeSeconds: Int = 30,

    @ColumnInfo(name = "is_blocked")
    val isBlocked: Boolean = true,

    @ColumnInfo(name = "daily_limit_minutes")
    val dailyLimitMinutes: Int = 0,

    @ColumnInfo(name = "block_shorts")
    val blockShorts: Boolean = true,

    @ColumnInfo(name = "block_reels")
    val blockReels: Boolean = true,

    @ColumnInfo(name = "timer_strategy")
    val timerStrategy: String = "FIXED", // FIXED, PROGRESSIVE, TASK_BASED, BREATHING

    @ColumnInfo(name = "today_usage_minutes")
    val todayUsageMinutes: Int = 0,

    @ColumnInfo(name = "last_usage_date")
    val lastUsageDate: Long = 0
)
