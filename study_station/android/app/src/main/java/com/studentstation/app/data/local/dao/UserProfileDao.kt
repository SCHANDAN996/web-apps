package com.studentstation.app.data.local.dao

import androidx.room.*
import com.studentstation.app.data.local.entity.UserProfileEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface UserProfileDao {

    @Query("SELECT * FROM user_profile WHERE id = 1")
    fun getProfile(): Flow<UserProfileEntity?>

    @Query("SELECT * FROM user_profile WHERE id = 1")
    suspend fun getProfileSync(): UserProfileEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertProfile(profile: UserProfileEntity)

    @Query("UPDATE user_profile SET is_profile_complete = 1 WHERE id = 1")
    suspend fun markProfileComplete()

    @Query("UPDATE user_profile SET class_level = :classLevel, board = :board, stream = :stream, target_exam = :targetExam, language = :language WHERE id = 1")
    suspend fun updateProfile(classLevel: Int, board: String, stream: String, targetExam: String, language: String)
}
