package com.studentstation.app.data.local.dao

import androidx.room.*
import com.studentstation.app.data.local.entity.StudyContentEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface StudyContentDao {

    @Query("SELECT * FROM study_content WHERE class_level = :classLevel AND subject = :subject ORDER BY chapter_number ASC")
    fun getContentBySubject(classLevel: Int, subject: String): Flow<List<StudyContentEntity>>

    @Query("SELECT * FROM study_content WHERE class_level = :classLevel ORDER BY subject ASC, chapter_number ASC")
    fun getContentByClass(classLevel: Int): Flow<List<StudyContentEntity>>

    @Query("SELECT * FROM study_content WHERE id = :id")
    suspend fun getContentById(id: Long): StudyContentEntity?

    @Query("SELECT * FROM study_content WHERE is_bookmarked = 1 ORDER BY last_accessed DESC")
    fun getBookmarkedContent(): Flow<List<StudyContentEntity>>

    @Query("SELECT * FROM study_content WHERE title LIKE '%' || :query || '%' OR chapter_name LIKE '%' || :query || '%' OR content_text LIKE '%' || :query || '%'")
    fun searchContent(query: String): Flow<List<StudyContentEntity>>

    @Query("SELECT DISTINCT subject, subject_icon FROM study_content WHERE class_level = :classLevel ORDER BY subject ASC")
    suspend fun getSubjectsForClass(classLevel: Int): List<SubjectInfo>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertContent(content: StudyContentEntity): Long

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(contents: List<StudyContentEntity>)

    @Query("UPDATE study_content SET is_bookmarked = :bookmarked WHERE id = :id")
    suspend fun toggleBookmark(id: Long, bookmarked: Boolean)

    @Query("UPDATE study_content SET last_accessed = :timestamp, read_progress = :progress WHERE id = :id")
    suspend fun updateProgress(id: Long, timestamp: Long, progress: Int)

    @Query("SELECT COUNT(*) FROM study_content WHERE class_level = :classLevel")
    suspend fun getContentCount(classLevel: Int): Int
}

data class SubjectInfo(
    val subject: String,
    @androidx.room.ColumnInfo(name = "subject_icon")
    val subjectIcon: String
)
