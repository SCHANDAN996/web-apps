package com.studentstation.app.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.PrimaryKey

/**
 * Entity to store scheduled study sessions (Timetable)
 */
@Entity(
    tableName = "timetable_entry",
    foreignKeys = [
        ForeignKey(
            entity = SubjectEntity::class,
            parentColumns = ["id"],
            childColumns = ["subject_id"],
            onDelete = ForeignKey.CASCADE
        )
    ]
)
data class TimetableEntryEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    @ColumnInfo(name = "subject_id")
    val subjectId: Long,

    @ColumnInfo(name = "day_of_week")
    val dayOfWeek: Int, // 1 = Monday, 7 = Sunday (ISO-8601 standard)

    @ColumnInfo(name = "start_time_minutes")
    val startTimeMinutes: Int, // Minutes from midnight (e.g., 600 = 10:00 AM)

    @ColumnInfo(name = "duration_minutes")
    val durationMinutes: Int = 45 // Default session duration
)
