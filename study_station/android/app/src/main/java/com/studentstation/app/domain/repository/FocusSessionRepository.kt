package com.studentstation.app.domain.repository

import com.studentstation.app.domain.model.FocusSession
import kotlinx.coroutines.flow.Flow

interface FocusSessionRepository {
    fun getAllSessions(): Flow<List<FocusSession>>
    fun getSessionsForDay(startOfDay: Long, endOfDay: Long): Flow<List<FocusSession>>
    suspend fun getActiveSession(): FocusSession?
    suspend fun getTotalFocusMinutesToday(startOfDay: Long): Int
    suspend fun getSuccessfulSessionsToday(startOfDay: Long): Int
    suspend fun startSession(session: FocusSession): Long
    suspend fun updateSession(session: FocusSession)
    suspend fun getTotalSuccessfulSessions(): Int
}
