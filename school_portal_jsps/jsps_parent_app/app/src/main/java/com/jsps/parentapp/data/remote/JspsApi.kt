package com.jsps.parentapp.data.remote

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path

interface JspsApi {
    @POST("api/v1/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @GET("api/v1/parent/{userId}/children")
    suspend fun getChildren(@Header("Authorization") auth: String, @Path("userId") userId: Int): ChildrenResponse
    
    @GET("api/v1/notices")
    suspend fun getNotices(@Header("Authorization") auth: String): NoticesResponse

    @GET("api/v1/assignments/{targetClass}")
    suspend fun getAssignments(@Header("Authorization") auth: String, @Path("targetClass") targetClass: String): AssignmentsResponse

    @GET("api/v1/student/{studentId}/results")
    suspend fun getResults(@Header("Authorization") auth: String, @Path("studentId") studentId: Int): ResultsResponse

    @GET("api/v1/student/{studentId}/attendance")
    suspend fun getAttendance(@Header("Authorization") auth: String, @Path("studentId") studentId: Int): AttendanceResponse

    @GET("api/v1/student/{studentId}/fees")
    suspend fun getFees(@Header("Authorization") auth: String, @Path("studentId") studentId: Int): FeesResponse

    @GET("api/v1/student/{studentId}/leave")
    suspend fun getLeaves(@Header("Authorization") auth: String, @Path("studentId") studentId: Int): LeavesResponse

    @POST("api/v1/student/{studentId}/leave")
    suspend fun submitLeave(@Header("Authorization") auth: String, @Path("studentId") studentId: Int, @Body request: LeaveRequest): LeaveResponse

    @GET("api/v1/student/{studentId}/transport")
    suspend fun getTransport(@Header("Authorization") auth: String, @Path("studentId") studentId: Int): TransportResponse

    @GET("api/v1/student/{studentId}/calendar")
    suspend fun getCalendar(@Header("Authorization") auth: String, @Path("studentId") studentId: Int): CalendarResponse

    @GET("api/v1/student/{studentId}/messages")
    suspend fun getMessages(@Header("Authorization") auth: String, @Path("studentId") studentId: Int): MessagesResponse

    @POST("api/v1/student/{studentId}/messages")
    suspend fun sendMessage(@Header("Authorization") auth: String, @Path("studentId") studentId: Int, @Body request: MessageRequest): MessagePostResponse

    @GET("api/v1/notifications")
    suspend fun getNotifications(@Header("Authorization") auth: String): NotificationsResponse

    @POST("api/v1/assistant/ask")
    suspend fun askAssistant(@Header("Authorization") auth: String, @Body request: AssistantRequest): AssistantResponse
}
