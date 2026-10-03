package com.studentstation.app.data.remote.api

import com.studentstation.app.data.remote.dto.ApiResponse
import com.studentstation.app.data.remote.dto.StudyContentDto
import com.studentstation.app.data.remote.dto.PracticeQuestionDto
import com.studentstation.app.data.remote.dto.JobAlertDto
import retrofit2.http.GET
import retrofit2.http.Query

interface StudentStationApi {

    @GET("study/content")
    suspend fun getStudyContent(
        @Query("class") classLevel: Int?,
        @Query("subject") subject: String?
    ): ApiResponse<List<StudyContentDto>>

    @GET("practice/questions")
    suspend fun getPracticeQuestions(
        @Query("exam") examName: String?
    ): ApiResponse<List<PracticeQuestionDto>>

    @GET("jobs/latest")
    suspend fun getLatestJobs(): ApiResponse<List<JobAlertDto>>

    @retrofit2.http.POST("api/chat")
    suspend fun sendChatMessage(
        @retrofit2.http.Body request: com.studentstation.app.data.remote.dto.ChatRequestDto
    ): com.studentstation.app.data.remote.dto.ChatResponseDto
}
