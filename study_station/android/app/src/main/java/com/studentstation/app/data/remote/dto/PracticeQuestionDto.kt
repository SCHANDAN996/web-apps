package com.studentstation.app.data.remote.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class PracticeQuestionDto(
    val id: Long,
    val questionText: String,
    val options: Map<String, String?>,
    val correctAnswer: String,
    val explanation: String?,
    val subject: String,
    val examName: String?
)
