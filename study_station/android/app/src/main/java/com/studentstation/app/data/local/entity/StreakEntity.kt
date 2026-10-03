package com.studentstation.app.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * छात्र की निरंतरता (Streak) ट्रैकिंग
 */
@Entity(tableName = "streak")
data class StreakEntity(
    @PrimaryKey
    val id: Int = 1, // single row

    @ColumnInfo(name = "current_streak")
    val currentStreak: Int = 0,

    @ColumnInfo(name = "longest_streak")
    val longestStreak: Int = 0,

    @ColumnInfo(name = "last_updated")
    val lastUpdated: Long = 0,

    @ColumnInfo(name = "total_focus_minutes")
    val totalFocusMinutes: Int = 0,

    @ColumnInfo(name = "total_xp")
    val totalXp: Int = 0,

    @ColumnInfo(name = "level")
    val level: Int = 1,

    @ColumnInfo(name = "trees_grown")
    val treesGrown: Int = 0,

    @ColumnInfo(name = "trees_withered")
    val treesWithered: Int = 0,

    @ColumnInfo(name = "total_blocks_resisted")
    val totalBlocksResisted: Int = 0
)
