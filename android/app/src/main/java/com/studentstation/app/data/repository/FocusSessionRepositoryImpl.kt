package com.studentstation.app.data.repository

import com.studentstation.app.data.local.dao.FocusSessionDao
import com.studentstation.app.data.local.entity.FocusSessionEntity
import com.studentstation.app.domain.model.FocusSession
import com.studentstation.app.domain.model.SessionType
import com.studentstation.app.domain.repository.FocusSessionRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class FocusSessionRepositoryImpl @Inject constructor(
    private val dao: FocusSessionDao
) : FocusSessionRepository {

    override fun getAllSessions(): Flow<List<FocusSession>> =
        dao.getAllSessions().map { list -> list.map { it.toDomain() } }

    override fun getSessionsForDay(startOfDay: Long, endOfDay: Long): Flow<List<FocusSession>> =
        dao.getSessionsForDay(startOfDay, endOfDay).map { list -> list.map { it.toDomain() } }

    override suspend fun getActiveSession(): FocusSession? =
        dao.getActiveSession()?.toDomain()

    override suspend fun getTotalFocusMinutesToday(startOfDay: Long): Int =
        dao.getTotalFocusMinutesToday(startOfDay) ?: 0

    override suspend fun getSuccessfulSessionsToday(startOfDay: Long): Int =
        dao.getSuccessfulSessionsToday(startOfDay)

    override suspend fun startSession(session: FocusSession): Long =
        dao.insertSession(session.toEntity())

    override suspend fun updateSession(session: FocusSession) =
        dao.updateSession(session.toEntity())

    override suspend fun getTotalSuccessfulSessions(): Int =
        dao.getTotalSuccessfulSessions()

    private fun FocusSessionEntity.toDomain() = FocusSession(
        id = id, startTime = startTime, endTime = endTime,
        plannedDurationMinutes = plannedDurationMinutes,
        isSuccessful = isSuccessful,
        sessionType = SessionType.valueOf(sessionType),
        interruptions = interruptions, xpEarned = xpEarned,
        subjectId = subjectId
    )

    private fun FocusSession.toEntity() = FocusSessionEntity(
        id = id, startTime = startTime, endTime = endTime,
        plannedDurationMinutes = plannedDurationMinutes,
        isSuccessful = isSuccessful,
        sessionType = sessionType.name,
        interruptions = interruptions, xpEarned = xpEarned,
        subjectId = subjectId
    )
}
