package com.studentstation.app.data.repository

import com.studentstation.app.data.local.dao.TimetableDao
import com.studentstation.app.data.local.entity.TimetableEntryEntity
import com.studentstation.app.domain.repository.TimetableRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TimetableRepositoryImpl @Inject constructor(
    private val timetableDao: TimetableDao
) : TimetableRepository {

    override fun getAllEntries(): Flow<List<TimetableEntryEntity>> {
        return timetableDao.getAllEntries()
    }

    override fun getEntriesForDay(dayOfWeek: Int): Flow<List<TimetableEntryEntity>> {
        return timetableDao.getEntriesForDay(dayOfWeek)
    }

    override suspend fun addEntry(entry: TimetableEntryEntity): Long {
        return timetableDao.insertEntry(entry)
    }

    override suspend fun addEntries(entries: List<TimetableEntryEntity>) {
        timetableDao.insertEntries(entries)
    }

    override suspend fun updateEntry(entry: TimetableEntryEntity) {
        timetableDao.updateEntry(entry)
    }

    override suspend fun deleteEntry(entry: TimetableEntryEntity) {
        timetableDao.deleteEntry(entry)
    }

    override suspend fun clearTimetable() {
        timetableDao.deleteAllEntries()
    }
}
