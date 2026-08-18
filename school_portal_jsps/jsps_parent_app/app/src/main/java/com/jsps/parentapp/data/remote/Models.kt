package com.jsps.parentapp.data.remote

data class LoginRequest(val username: String, val password: String, val role: String = "parent")
data class LoginResponse(val success: Boolean, val token: String?, val user: User?, val error: String?)
data class User(val id: Int, val name: String, val phone: String, val role: String)

data class ChildrenResponse(val children: List<Child>)
data class Child(
    val id: Int,
    val admission_no: String,
    val name: String,
    val class_name: String,
    val raw_class: String?,
    val section: String?
)

data class NoticesResponse(val notices: List<Notice>)
data class Notice(val id: Int, val title: String, val content: String, val date: String)

data class AssignmentsResponse(val assignments: List<Assignment>)
data class Assignment(
    val id: Int,
    val title: String,
    val description: String?,
    val subject: String,
    val target_class: String?,
    val due_date: String?,
    val file_path: String?
)

data class ResultsResponse(val results: List<Result>)
data class Result(
    val id: Int,
    val term: String,
    val subject_marks: Map<String, Double>?,
    val total_marks: Int?,
    val percentage: Double?,
    val grade: String?,
    val remarks: String?
)

data class AttendanceResponse(val attendance: List<AttendanceRecord>, val summary: Map<String, Int>)
data class AttendanceRecord(val id: Int, val date: String, val status: String, val remarks: String?)

data class FeesResponse(val invoices: List<FeeInvoice>, val payments: List<FeePaymentRecord>)
data class FeeInvoice(
    val id: Int,
    val title: String,
    val amount: Int,
    val paid_amount: Int,
    val due_date: String?,
    val status: String,
    val notes: String?
)
data class FeePaymentRecord(val id: Int, val amount_paid: Int, val status: String, val receipt: String?, val date: String)

data class LeaveRequest(val from_date: String, val to_date: String, val reason: String)
data class LeaveResponse(val success: Boolean, val id: Int?)
data class LeavesResponse(val leaves: List<LeaveApplication>)
data class LeaveApplication(
    val id: Int,
    val from_date: String,
    val to_date: String,
    val reason: String,
    val status: String,
    val admin_note: String?
)

data class TransportResponse(val transport: TransportInfo?)
data class TransportInfo(
    val route_name: String?,
    val vehicle_no: String?,
    val driver_name: String?,
    val driver_phone: String?,
    val attendant_phone: String?,
    val pickup_point: String?,
    val drop_point: String?,
    val pickup_time: String?,
    val drop_time: String?,
    val live_tracking_url: String?,
    val last_latitude: Double?,
    val last_longitude: Double?,
    val last_updated: String?
)

data class CalendarResponse(val events: List<SchoolEvent>, val timetable: List<TimetableEntry>)
data class SchoolEvent(
    val id: Int,
    val title: String,
    val description: String?,
    val date: String,
    val event_type: String,
    val target_class: String?
)
data class TimetableEntry(
    val id: Int,
    val weekday: String,
    val period_no: Int,
    val subject: String,
    val teacher_name: String?,
    val starts_at: String?,
    val ends_at: String?
)

data class MessagesResponse(val messages: List<ParentMessage>)
data class MessageRequest(val category: String, val message: String)
data class MessagePostResponse(val success: Boolean, val id: Int?)
data class ParentMessage(
    val id: Int,
    val sender_role: String,
    val category: String,
    val message: String,
    val status: String,
    val date: String
)

data class NotificationsResponse(val notifications: List<AppNotification>)
data class AppNotification(
    val id: Int,
    val title: String,
    val body: String?,
    val channel: String,
    val delivery_status: String,
    val date: String
)

data class AssistantRequest(val question: String)
data class AssistantResponse(val answer: String)
