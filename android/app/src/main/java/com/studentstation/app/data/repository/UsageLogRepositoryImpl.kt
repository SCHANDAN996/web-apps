package com.studentstation.app.data.repository

import com.studentstation.app.data.local.dao.UsageLogDao
import com.studentstation.app.data.local.entity.UsageLogEntity
import com.studentstation.app.domain.model.UsageRecord
import com.studentstation.app.domain.repository.UsageLogRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class UsageLogRepositoryImpl @Inject constructor(
    private val dao: UsageLogDao
) : UsageLogRepository {

    override fun getLogsForDay(startOfDay: Long): Flow<List<UsageRecord>> =
        dao.getLogsForDay(startOfDay).map { list ->
            list.map {
                UsageRecord(
                    id = it.id, timestamp = it.timestamp,
                    appPackage = it.appPackage, feature = it.feature,
                    actionTaken = it.actionTaken, waitCompleted = it.waitCompleted,
                    waitDurationSeconds = it.waitDurationSeconds
                )
            }
        }

    override suspend fun getBlocksResistedToday(startOfDay: Long): Int =
        dao.getBlocksResistedToday(startOfDay)

    override suspend fun getTimesWaitedToday(startOfDay: Long): Int =
        dao.getTimesWaitedToday(startOfDay)

    override suspend fun getTotalAttemptsToday(startOfDay: Long): Int =
        dao.getTotalAttemptsToday(startOfDay)

    override suspend fun getTotalBlocksResisted(): Int =
        dao.getTotalBlocksResisted()

    override suspend fun logUsage(record: UsageRecord) {
        dao.insertLog(
            UsageLogEntity(
                timestamp = record.timestamp, appPackage = record.appPackage,
                feature = record.feature, actionTaken = record.actionTaken,
                waitCompleted = record.waitCompleted,
                waitDurationSeconds = record.waitDurationSeconds
            )
        )
    }

    override suspend fun deleteOldLogs(beforeTimestamp: Long) {
        dao.deleteOldLogs(beforeTimestamp)
    }
}
