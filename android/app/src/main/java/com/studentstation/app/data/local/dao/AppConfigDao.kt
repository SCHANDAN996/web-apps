package com.studentstation.app.data.local.dao

import androidx.room.*
import com.studentstation.app.data.local.entity.AppConfigEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface AppConfigDao {

    @Query("SELECT * FROM app_config ORDER BY display_name ASC")
    fun getAllConfigs(): Flow<List<AppConfigEntity>>

    @Query("SELECT * FROM app_config WHERE is_blocked = 1")
    fun getBlockedApps(): Flow<List<AppConfigEntity>>

    @Query("SELECT * FROM app_config WHERE package_name = :packageName LIMIT 1")
    suspend fun getConfigByPackage(packageName: String): AppConfigEntity?

    @Query("SELECT * FROM app_config WHERE id = :id")
    suspend fun getConfigById(id: Long): AppConfigEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertConfig(config: AppConfigEntity): Long

    @Update
    suspend fun updateConfig(config: AppConfigEntity)

    @Delete
    suspend fun deleteConfig(config: AppConfigEntity)

    @Query("UPDATE app_config SET today_usage_minutes = :minutes, last_usage_date = :date WHERE package_name = :packageName")
    suspend fun updateUsage(packageName: String, minutes: Int, date: Long)

    @Query("UPDATE app_config SET today_usage_minutes = 0")
    suspend fun resetDailyUsage()
}
