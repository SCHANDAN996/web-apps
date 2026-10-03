package com.studentstation.app.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.studentstation.app.data.local.dao.*
import com.studentstation.app.data.local.entity.*

/**
 * Student Station Room Database
 * सभी छात्र डेटा यहाँ स्टोर होता है — पूर्णतः ऑन-डिवाइस
 */
@Database(
    entities = [
        AppConfigEntity::class,
        FocusSessionEntity::class,
        UsageLogEntity::class,
        StreakEntity::class,
        UserProfileEntity::class,
        StudyContentEntity::class,
        SubjectEntity::class,
        TimetableEntryEntity::class
    ],
    version = 5,
    exportSchema = true
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun appConfigDao(): AppConfigDao
    abstract fun focusSessionDao(): FocusSessionDao
    abstract fun usageLogDao(): UsageLogDao
    abstract fun streakDao(): StreakDao
    abstract fun userProfileDao(): UserProfileDao
    abstract fun studyContentDao(): StudyContentDao
    abstract fun subjectDao(): SubjectDao
    abstract fun timetableDao(): TimetableDao

    companion object {
        const val DATABASE_NAME = "student_station_db"

        @Volatile
        private var INSTANCE: AppDatabase? = null

        /**
         * Used by AccessibilityService (cannot use Hilt injection)
         */
        fun buildDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    DATABASE_NAME
                ).fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
