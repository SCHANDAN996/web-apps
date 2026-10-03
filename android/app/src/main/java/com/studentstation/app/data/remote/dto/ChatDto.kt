package com.studentstation.app.data.remote.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ChatRequestDto(
    val chapterId: Long,
    val message: String
)

@JsonClass(generateAdapter = true)
data class ChatResponseDto(
    val success: Boolean,
    val reply: String?,
    val error: String?
)
