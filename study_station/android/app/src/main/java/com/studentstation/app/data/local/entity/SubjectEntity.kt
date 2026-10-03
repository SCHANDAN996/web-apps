package com.studentstation.app.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Entity to track subjects and their syllabus progress for the Study Plan
 */
@Entity(tableName = "subject_entity")
data class SubjectEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    @ColumnInfo(name = "name")
    val name: String,

    @ColumnInfo(name = "total_chapters")
    val totalChapters: Int = 0,

    @ColumnInfo(name = "completed_chapters")
    val completedChapters: Int = 0,

    @ColumnInfo(name = "target_exam_date")
    val targetExamDate: Long? = null,
    
    @ColumnInfo(name = "color_hex")
    val colorHex: String? = null
)
