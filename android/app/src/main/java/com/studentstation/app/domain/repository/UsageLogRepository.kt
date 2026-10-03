package com.studentstation.app.domain.repository

import com.studentstation.app.domain.model.UsageRecord
import kotlinx.coroutines.flow.Flow

interface UsageLogRepository {
    fun getLogsForDay(startOfDay: Long): Flow<List<UsageRecord>>
    suspend fun getBlocksResistedToday(startOfDay: Long): Int
    suspend fun getTimesWaitedToday(startOfDay: Long): Int
    suspend fun getTotalAttemptsToday(startOfDay: Long): Int
    suspend fun getTotalBlocksResisted(): Int
    suspend fun logUsage(record: UsageRecord)
    suspend fun deleteOldLogs(beforeTimestamp: Long)
}
