package com.studentstation.app.data.local.dao

import androidx.room.*
import com.studentstation.app.data.local.entity.StreakEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface StreakDao {

    @Query("SELECT * FROM streak WHERE id = 1")
    fun getStreak(): Flow<StreakEntity?>

    @Query("SELECT * FROM streak WHERE id = 1")
    suspend fun getStreakSync(): StreakEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertStreak(streak: StreakEntity)

    @Query("UPDATE streak SET current_streak = current_streak + 1, longest_streak = MAX(longest_streak, current_streak + 1), last_updated = :timestamp WHERE id = 1")
    suspend fun incrementStreak(timestamp: Long)

    @Query("UPDATE streak SET current_streak = 0, last_updated = :timestamp WHERE id = 1")
    suspend fun resetStreak(timestamp: Long)

    @Query("UPDATE streak SET total_focus_minutes = total_focus_minutes + :minutes, total_xp = total_xp + :xp WHERE id = 1")
    suspend fun addFocusStats(minutes: Int, xp: Int)

    @Query("UPDATE streak SET trees_grown = trees_grown + 1 WHERE id = 1")
    suspend fun incrementTreesGrown()

    @Query("UPDATE streak SET trees_withered = trees_withered + 1 WHERE id = 1")
    suspend fun incrementTreesWithered()

    @Query("UPDATE streak SET level = :level WHERE id = 1")
    suspend fun updateLevel(level: Int)

    @Query("UPDATE streak SET total_blocks_resisted = total_blocks_resisted + 1 WHERE id = 1")
    suspend fun incrementBlocksResisted()
}
