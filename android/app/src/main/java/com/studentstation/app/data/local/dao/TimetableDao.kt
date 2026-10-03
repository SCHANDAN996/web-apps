package com.studentstation.app.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.studentstation.app.data.local.entity.TimetableEntryEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface TimetableDao {
    @Query("SELECT * FROM timetable_entry ORDER BY day_of_week ASC, start_time_minutes ASC")
    fun getAllEntries(): Flow<List<TimetableEntryEntity>>

    @Query("SELECT * FROM timetable_entry WHERE day_of_week = :dayOfWeek ORDER BY start_time_minutes ASC")
    fun getEntriesForDay(dayOfWeek: Int): Flow<List<TimetableEntryEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEntry(entry: TimetableEntryEntity): Long

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEntries(entries: List<TimetableEntryEntity>)

    @Update
    suspend fun updateEntry(entry: TimetableEntryEntity)

    @Delete
    suspend fun deleteEntry(entry: TimetableEntryEntity)

    @Query("DELETE FROM timetable_entry")
    suspend fun deleteAllEntries()
}
