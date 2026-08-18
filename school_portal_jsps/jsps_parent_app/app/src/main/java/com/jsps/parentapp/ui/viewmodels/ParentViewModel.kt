package com.jsps.parentapp.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.jsps.parentapp.data.remote.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class ParentViewModel(private val api: JspsApi) : ViewModel() {

    private var authToken: String? = null

    private fun authHeader(): String = "Bearer ${authToken.orEmpty()}"

    private val _user = MutableStateFlow<User?>(null)
    val user: StateFlow<User?> = _user.asStateFlow()

    private val _children = MutableStateFlow<List<Child>>(emptyList())
    val children: StateFlow<List<Child>> = _children.asStateFlow()

    private val _notices = MutableStateFlow<List<Notice>>(emptyList())
    val notices: StateFlow<List<Notice>> = _notices.asStateFlow()

    private val _loginError = MutableStateFlow<String?>(null)
    val loginError: StateFlow<String?> = _loginError.asStateFlow()

    fun login(phone: String, pass: String, onSuccess: () -> Unit) {
        viewModelScope.launch {
            try {
                val response = api.login(LoginRequest(phone, pass))
                if (response.success && response.user != null) {
                    authToken = response.token
                    _user.value = response.user
                    _loginError.value = null
                    onSuccess()
                    fetchChildren(response.user.id)
                    fetchNotices()
                } else {
                    _loginError.value = response.error ?: "Invalid credentials"
                }
            } catch (e: Exception) {
                _loginError.value = "Network error: ${e.message}"
            }
        }
    }

    private fun fetchChildren(userId: Int) {
        viewModelScope.launch {
            try {
                val response = api.getChildren(authHeader(), userId)
                _children.value = response.children
            } catch (e: Exception) {
                // handle error
            }
        }
    }

    private fun fetchNotices() {
        viewModelScope.launch {
            try {
                val response = api.getNotices(authHeader())
                _notices.value = response.notices
            } catch (e: Exception) {
                // handle error
            }
        }
    }

    // A generic function to fetch results for UI
    suspend fun fetchResults(studentId: Int): List<Result> {
        return try {
            api.getResults(authHeader(), studentId).results
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun fetchAssignments(className: String): List<Assignment> {
        return try {
            api.getAssignments(authHeader(), className).assignments
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun fetchAttendance(studentId: Int): AttendanceResponse {
        return try {
            api.getAttendance(authHeader(), studentId)
        } catch (e: Exception) {
            AttendanceResponse(emptyList(), emptyMap())
        }
    }

    suspend fun fetchFees(studentId: Int): FeesResponse {
        return try {
            api.getFees(authHeader(), studentId)
        } catch (e: Exception) {
            FeesResponse(emptyList(), emptyList())
        }
    }

    suspend fun fetchLeaves(studentId: Int): List<LeaveApplication> {
        return try {
            api.getLeaves(authHeader(), studentId).leaves
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun submitLeave(studentId: Int, fromDate: String, toDate: String, reason: String): Boolean {
        return try {
            api.submitLeave(authHeader(), studentId, LeaveRequest(fromDate, toDate, reason)).success
        } catch (e: Exception) {
            false
        }
    }

    suspend fun fetchTransport(studentId: Int): TransportInfo? {
        return try {
            api.getTransport(authHeader(), studentId).transport
        } catch (e: Exception) {
            null
        }
    }

    suspend fun fetchCalendar(studentId: Int): CalendarResponse {
        return try {
            api.getCalendar(authHeader(), studentId)
        } catch (e: Exception) {
            CalendarResponse(emptyList(), emptyList())
        }
    }

    suspend fun fetchMessages(studentId: Int): List<ParentMessage> {
        return try {
            api.getMessages(authHeader(), studentId).messages
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun sendMessage(studentId: Int, category: String, message: String): Boolean {
        return try {
            api.sendMessage(authHeader(), studentId, MessageRequest(category, message)).success
        } catch (e: Exception) {
            false
        }
    }

    suspend fun fetchNotifications(): List<AppNotification> {
        return try {
            api.getNotifications(authHeader()).notifications
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun askAssistant(question: String): String {
        return try {
            api.askAssistant(authHeader(), AssistantRequest(question)).answer
        } catch (e: Exception) {
            "I could not reach the school server right now."
        }
    }
}
