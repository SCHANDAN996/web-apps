package com.studentstation.app.data.remote.dto

import com.squareup.moshi.JsonClass
import com.studentstation.app.data.local.entity.StudyContentEntity

@JsonClass(generateAdapter = true)
data class StudyContentDto(
    val id: Long,
    val title: String,
    val description: String?,
    val category: String,
    val classLevel: Int,
    val board: String,
    val subject: String,
    val subjectIcon: String,
    val chapterNumber: Int,
    val chapterName: String,
    val contentText: String,
    val pdfUrl: String?,
    val difficulty: String
)

fun StudyContentDto.toEntity() = StudyContentEntity(
    id = id,
    title = title,
    description = description ?: "",
    category = category,
    classLevel = classLevel,
    board = board,
    subject = subject,
    subjectIcon = subjectIcon,
    chapterNumber = chapterNumber,
    chapterName = chapterName,
    contentText = contentText,
    contentUrl = pdfUrl ?: "",
    difficulty = difficulty,
    isBookmarked = false, // Defaults when fetching from remote
    lastAccessed = 0L,
    readProgress = 0
)
