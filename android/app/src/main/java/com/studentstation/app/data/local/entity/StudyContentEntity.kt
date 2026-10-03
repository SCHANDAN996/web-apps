package com.studentstation.app.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * स्टडी कंटेंट — NCERT नोट्स, फॉर्मूला, सारांश
 */
@Entity(tableName = "study_content")
data class StudyContentEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    @ColumnInfo(name = "title")
    val title: String,

    @ColumnInfo(name = "description")
    val description: String = "",

    @ColumnInfo(name = "category")
    val category: String = "NOTES", // NOTES, FORMULA, SUMMARY, IMPORTANT_QUESTIONS

    @ColumnInfo(name = "class_level")
    val classLevel: Int = 10,

    @ColumnInfo(name = "board")
    val board: String = "CBSE",

    @ColumnInfo(name = "subject")
    val subject: String, // MATH, SCIENCE, HINDI, ENGLISH, SST

    @ColumnInfo(name = "subject_icon")
    val subjectIcon: String = "📚",

    @ColumnInfo(name = "chapter_number")
    val chapterNumber: Int = 1,

    @ColumnInfo(name = "chapter_name")
    val chapterName: String = "",

    @ColumnInfo(name = "content_text")
    val contentText: String = "", // Markdown format

    @ColumnInfo(name = "content_url")
    val contentUrl: String = "", // PDF or external link

    @ColumnInfo(name = "difficulty")
    val difficulty: String = "MEDIUM", // EASY, MEDIUM, HARD

    @ColumnInfo(name = "is_bookmarked")
    val isBookmarked: Boolean = false,

    @ColumnInfo(name = "last_accessed")
    val lastAccessed: Long = 0,

    @ColumnInfo(name = "read_progress")
    val readProgress: Int = 0 // 0-100
)
