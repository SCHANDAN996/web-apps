package com.studentstation.app.data.local.dao

import androidx.room.*
import com.studentstation.app.data.local.entity.FocusSessionEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface FocusSessionDao {

    @Query("SELECT * FROM focus_session ORDER BY start_time DESC")
    fun getAllSessions(): Flow<List<FocusSessionEntity>>

    @Query("SELECT * FROM focus_session WHERE start_time >= :startOfDay AND start_time < :endOfDay ORDER BY start_time DESC")
    fun getSessionsForDay(startOfDay: Long, endOfDay: Long): Flow<List<FocusSessionEntity>>

    @Query("SELECT * FROM focus_session WHERE end_time IS NULL LIMIT 1")
    suspend fun getActiveSession(): FocusSessionEntity?

    @Query("SELECT SUM(CASE WHEN end_time IS NOT NULL THEN (end_time - start_time) / 60000 ELSE 0 END) FROM focus_session WHERE start_time >= :startOfDay")
    suspend fun getTotalFocusMinutesToday(startOfDay: Long): Int?

    @Query("SELECT COUNT(*) FROM focus_session WHERE is_successful = 1 AND start_time >= :startOfDay")
    suspend fun getSuccessfulSessionsToday(startOfDay: Long): Int

    @Insert
    suspend fun insertSession(session: FocusSessionEntity): Long

    @Update
    suspend fun updateSession(session: FocusSessionEntity)

    @Query("SELECT COUNT(*) FROM focus_session WHERE is_successful = 1")
    suspend fun getTotalSuccessfulSessions(): Int
}
