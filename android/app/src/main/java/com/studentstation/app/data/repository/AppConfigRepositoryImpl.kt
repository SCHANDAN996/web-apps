package com.studentstation.app.data.repository

import com.studentstation.app.data.local.dao.AppConfigDao
import com.studentstation.app.data.local.entity.AppConfigEntity
import com.studentstation.app.domain.model.BlockedApp
import com.studentstation.app.domain.model.TimerStrategy
import com.studentstation.app.domain.repository.AppConfigRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AppConfigRepositoryImpl @Inject constructor(
    private val dao: AppConfigDao
) : AppConfigRepository {

    override fun getAllConfigs(): Flow<List<BlockedApp>> =
        dao.getAllConfigs().map { list -> list.map { it.toDomain() } }

    override fun getBlockedApps(): Flow<List<BlockedApp>> =
        dao.getBlockedApps().map { list -> list.map { it.toDomain() } }

    override suspend fun getConfigByPackage(packageName: String): BlockedApp? =
        dao.getConfigByPackage(packageName)?.toDomain()

    override suspend fun saveConfig(app: BlockedApp) {
        dao.insertConfig(app.toEntity())
    }

    override suspend fun updateConfig(app: BlockedApp) {
        dao.updateConfig(app.toEntity())
    }

    override suspend fun deleteConfig(app: BlockedApp) {
        dao.deleteConfig(app.toEntity())
    }

    override suspend fun updateUsage(packageName: String, minutes: Int, date: Long) {
        dao.updateUsage(packageName, minutes, date)
    }

    override suspend fun resetDailyUsage() {
        dao.resetDailyUsage()
    }

    private fun AppConfigEntity.toDomain() = BlockedApp(
        id = id,
        packageName = packageName,
        displayName = displayName,
        waitTimeSeconds = waitTimeSeconds,
        isBlocked = isBlocked,
        dailyLimitMinutes = dailyLimitMinutes,
        blockShorts = blockShorts,
        blockReels = blockReels,
        timerStrategy = TimerStrategy.valueOf(timerStrategy),
        todayUsageMinutes = todayUsageMinutes
    )

    private fun BlockedApp.toEntity() = AppConfigEntity(
        id = id,
        packageName = packageName,
        displayName = displayName,
        waitTimeSeconds = waitTimeSeconds,
        isBlocked = isBlocked,
        dailyLimitMinutes = dailyLimitMinutes,
        blockShorts = blockShorts,
        blockReels = blockReels,
        timerStrategy = timerStrategy.name,
        todayUsageMinutes = todayUsageMinutes
    )
}
