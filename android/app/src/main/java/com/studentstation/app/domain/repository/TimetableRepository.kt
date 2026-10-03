package com.studentstation.app.domain.repository

import com.studentstation.app.data.local.entity.TimetableEntryEntity
import kotlinx.coroutines.flow.Flow

interface TimetableRepository {
    fun getAllEntries(): Flow<List<TimetableEntryEntity>>
    fun getEntriesForDay(dayOfWeek: Int): Flow<List<TimetableEntryEntity>>
    suspend fun addEntry(entry: TimetableEntryEntity): Long
    suspend fun addEntries(entries: List<TimetableEntryEntity>)
    suspend fun updateEntry(entry: TimetableEntryEntity)
    suspend fun deleteEntry(entry: TimetableEntryEntity)
    suspend fun clearTimetable()
}
