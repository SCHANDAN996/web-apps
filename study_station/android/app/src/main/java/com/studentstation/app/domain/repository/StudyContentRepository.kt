package com.studentstation.app.domain.repository

import com.studentstation.app.data.local.dao.SubjectInfo
import com.studentstation.app.data.local.entity.StudyContentEntity
import kotlinx.coroutines.flow.Flow

interface StudyContentRepository {
    fun getContentBySubject(classLevel: Int, subject: String): Flow<List<StudyContentEntity>>
    fun getContentByClass(classLevel: Int): Flow<List<StudyContentEntity>>
    suspend fun getContentById(id: Long): StudyContentEntity?
    fun getBookmarkedContent(): Flow<List<StudyContentEntity>>
    fun searchContent(query: String): Flow<List<StudyContentEntity>>
    suspend fun getSubjectsForClass(classLevel: Int): List<SubjectInfo>
    suspend fun insertContent(content: StudyContentEntity): Long
    suspend fun toggleBookmark(id: Long, bookmarked: Boolean)
    suspend fun updateProgress(id: Long, progress: Int)
    suspend fun preloadDefaultContent(classLevel: Int)
}
