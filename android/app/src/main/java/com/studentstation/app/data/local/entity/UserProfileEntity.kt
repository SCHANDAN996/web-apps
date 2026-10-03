package com.studentstation.app.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * छात्र प्रोफ़ाइल — कक्षा, बोर्ड, और लक्ष्य
 */
@Entity(tableName = "user_profile")
data class UserProfileEntity(
    @PrimaryKey
    val id: Int = 1, // Single user

    @ColumnInfo(name = "student_name")
    val studentName: String = "",

    @ColumnInfo(name = "class_level")
    val classLevel: Int = 10, // 1-12, 13=UG, 14=PG

    @ColumnInfo(name = "board")
    val board: String = "CBSE", // CBSE, ICSE, UP, BIHAR, MP, RAJASTHAN

    @ColumnInfo(name = "stream")
    val stream: String = "SCIENCE", // SCIENCE, COMMERCE, ARTS (for 11-12)

    @ColumnInfo(name = "target_exam")
    val targetExam: String = "BOARD", // BOARD, JEE, NEET, UPSC, SSC, BANKING

    @ColumnInfo(name = "language")
    val language: String = "HINDI", // HINDI, ENGLISH, BOTH

    @ColumnInfo(name = "is_profile_complete")
    val isProfileComplete: Boolean = false
)
