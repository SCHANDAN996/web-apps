package com.studentstation.app.data.local.dao

import androidx.room.*
import com.studentstation.app.data.local.entity.UsageLogEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface UsageLogDao {

    @Query("SELECT * FROM usage_log WHERE timestamp >= :startOfDay ORDER BY timestamp DESC")
    fun getLogsForDay(startOfDay: Long): Flow<List<UsageLogEntity>>

    @Query("SELECT COUNT(*) FROM usage_log WHERE action_taken = 'CLOSED' AND timestamp >= :startOfDay")
    suspend fun getBlocksResistedToday(startOfDay: Long): Int

    @Query("SELECT COUNT(*) FROM usage_log WHERE action_taken = 'WAITED' AND timestamp >= :startOfDay")
    suspend fun getTimesWaitedToday(startOfDay: Long): Int

    @Query("SELECT COUNT(*) FROM usage_log WHERE timestamp >= :startOfDay")
    suspend fun getTotalAttemptsToday(startOfDay: Long): Int

    @Query("SELECT COUNT(*) FROM usage_log WHERE action_taken = 'CLOSED'")
    suspend fun getTotalBlocksResisted(): Int

    @Insert
    suspend fun insertLog(log: UsageLogEntity): Long

    @Query("DELETE FROM usage_log WHERE timestamp < :beforeTimestamp")
    suspend fun deleteOldLogs(beforeTimestamp: Long)

    @Query("SELECT app_package, COUNT(*) as count FROM usage_log WHERE timestamp >= :startOfDay GROUP BY app_package ORDER BY count DESC")
    suspend fun getMostBlockedAppsToday(startOfDay: Long): List<AppBlockCount>
}

data class AppBlockCount(
    @ColumnInfo(name = "app_package") val appPackage: String,
    @ColumnInfo(name = "count") val count: Int
)
