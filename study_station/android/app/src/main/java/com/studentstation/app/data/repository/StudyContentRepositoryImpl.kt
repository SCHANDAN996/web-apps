package com.studentstation.app.data.repository

import com.studentstation.app.data.local.dao.StudyContentDao
import com.studentstation.app.data.local.dao.SubjectInfo
import com.studentstation.app.data.local.entity.StudyContentEntity
import com.studentstation.app.data.remote.api.StudentStationApi
import com.studentstation.app.data.remote.dto.toEntity
import com.studentstation.app.domain.repository.StudyContentRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import android.util.Log

class StudyContentRepositoryImpl @Inject constructor(
    private val studyContentDao: StudyContentDao,
    private val api: StudentStationApi
) : StudyContentRepository {

    override fun getContentBySubject(classLevel: Int, subject: String): Flow<List<StudyContentEntity>> {
        return studyContentDao.getContentBySubject(classLevel, subject)
    }

    override fun getContentByClass(classLevel: Int): Flow<List<StudyContentEntity>> {
        return studyContentDao.getContentByClass(classLevel)
    }

    override suspend fun getContentById(id: Long): StudyContentEntity? {
        return studyContentDao.getContentById(id)
    }

    override fun getBookmarkedContent(): Flow<List<StudyContentEntity>> {
        return studyContentDao.getBookmarkedContent()
    }

    override fun searchContent(query: String): Flow<List<StudyContentEntity>> {
        return studyContentDao.searchContent(query)
    }

    override suspend fun getSubjectsForClass(classLevel: Int): List<SubjectInfo> {
        return studyContentDao.getSubjectsForClass(classLevel)
    }

    override suspend fun insertContent(content: StudyContentEntity): Long {
        return studyContentDao.insertContent(content)
    }

    override suspend fun toggleBookmark(id: Long, bookmarked: Boolean) {
        studyContentDao.toggleBookmark(id, bookmarked)
    }

    override suspend fun updateProgress(id: Long, progress: Int) {
        studyContentDao.updateProgress(id, System.currentTimeMillis(), progress)
    }

    override suspend fun preloadDefaultContent(classLevel: Int) {
        // Try to fetch from remote API first
        try {
            val response = api.getStudyContent(classLevel, null)
            if (response.success && response.data.isNotEmpty()) {
                val entities = response.data.map { it.toEntity() }
                studyContentDao.insertAll(entities)
                Log.d("StudyRepository", "Synced ${entities.size} items from API")
                return
            }
        } catch (e: Exception) {
            Log.e("StudyRepository", "Failed to fetch from API: ${e.message}")
        }

        // Fallback to default local data if DB is empty and API fails
        if (studyContentDao.getContentCount(classLevel) > 0) return

        if (classLevel == 10) {
            val sampleContent = listOf(
                StudyContentEntity(
                    title = "Chemical Reactions and Equations",
                    description = "NCERT Chapter 1 Notes",
                    category = "NOTES",
                    classLevel = 10,
                    subject = "Science",
                    subjectIcon = "🔬",
                    chapterNumber = 1,
                    chapterName = "Chemical Reactions",
                    contentText = "# Chapter 1: Chemical Reactions and Equations\n\nFallback content from local DB.",
                    difficulty = "MEDIUM"
                ),
                StudyContentEntity(
                    title = "Real Numbers",
                    description = "NCERT Chapter 1 Notes",
                    category = "NOTES",
                    classLevel = 10,
                    subject = "Maths",
                    subjectIcon = "📐",
                    chapterNumber = 1,
                    chapterName = "Real Numbers",
                    contentText = "# Chapter 1: Real Numbers\n\nFallback content from local DB.",
                    difficulty = "EASY"
                )
            )
            studyContentDao.insertAll(sampleContent)
        }
    }
}
