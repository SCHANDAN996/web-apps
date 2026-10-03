package com.studentstation.app.domain.repository

import com.studentstation.app.domain.model.BlockedApp
import kotlinx.coroutines.flow.Flow

interface AppConfigRepository {
    fun getAllConfigs(): Flow<List<BlockedApp>>
    fun getBlockedApps(): Flow<List<BlockedApp>>
    suspend fun getConfigByPackage(packageName: String): BlockedApp?
    suspend fun saveConfig(app: BlockedApp)
    suspend fun updateConfig(app: BlockedApp)
    suspend fun deleteConfig(app: BlockedApp)
    suspend fun updateUsage(packageName: String, minutes: Int, date: Long)
    suspend fun resetDailyUsage()
}
