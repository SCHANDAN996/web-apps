package com.jsps.parentapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.jsps.parentapp.data.remote.*
import com.jsps.parentapp.ui.viewmodels.ParentViewModel
import kotlinx.coroutines.launch

@Composable
private fun ScreenShell(title: String, onBack: () -> Unit, content: @Composable ColumnScope.() -> Unit) {
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        OutlinedButton(onClick = onBack) { Text("Back") }
        Spacer(modifier = Modifier.height(12.dp))
        Text(title, style = MaterialTheme.typography.headlineSmall)
        Spacer(modifier = Modifier.height(16.dp))
        content()
    }
}

@Composable
fun AttendanceScreen(viewModel: ParentViewModel, studentId: Int, onBack: () -> Unit) {
    var response by remember { mutableStateOf(AttendanceResponse(emptyList(), emptyMap())) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(studentId) {
        response = viewModel.fetchAttendance(studentId)
        isLoading = false
    }

    ScreenShell("Attendance", onBack) {
        if (isLoading) {
            CircularProgressIndicator()
        } else {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                response.summary.forEach { (status, count) ->
                    AssistChip(onClick = {}, label = { Text("$status $count") })
                }
            }
            Spacer(modifier = Modifier.height(12.dp))
            LazyColumn {
                items(response.attendance) { item ->
                    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Text(item.date, style = MaterialTheme.typography.titleMedium)
                            Text(item.status)
                            if (!item.remarks.isNullOrBlank()) Text(item.remarks)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun FeeScreen(viewModel: ParentViewModel, studentId: Int, onBack: () -> Unit) {
    var response by remember { mutableStateOf(FeesResponse(emptyList(), emptyList())) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(studentId) {
        response = viewModel.fetchFees(studentId)
        isLoading = false
    }

    ScreenShell("Fees", onBack) {
        if (isLoading) {
            CircularProgressIndicator()
        } else {
            LazyColumn {
                item { Text("Invoices", style = MaterialTheme.typography.titleLarge) }
                items(response.invoices) { invoice ->
                    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Text(invoice.title, style = MaterialTheme.typography.titleMedium)
                            Text("Paid Rs ${invoice.paid_amount} / Rs ${invoice.amount}")
                            Text("${invoice.status} | Due ${invoice.due_date ?: "-"}")
                        }
                    }
                }
                item {
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("Submitted Receipts", style = MaterialTheme.typography.titleLarge)
                }
                items(response.payments) { payment ->
                    ListItem(
                        headlineContent = { Text("Rs ${payment.amount_paid}") },
                        supportingContent = { Text("${payment.status} | ${payment.date}") }
                    )
                }
            }
        }
    }
}

@Composable
fun LeaveScreen(viewModel: ParentViewModel, studentId: Int, onBack: () -> Unit) {
    val scope = rememberCoroutineScope()
    var fromDate by remember { mutableStateOf("") }
    var toDate by remember { mutableStateOf("") }
    var reason by remember { mutableStateOf("") }
    var leaves by remember { mutableStateOf<List<LeaveApplication>>(emptyList()) }
    var message by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(studentId) {
        leaves = viewModel.fetchLeaves(studentId)
    }

    ScreenShell("Leave Application", onBack) {
        OutlinedTextField(value = fromDate, onValueChange = { fromDate = it }, label = { Text("From date YYYY-MM-DD") }, modifier = Modifier.fillMaxWidth())
        Spacer(modifier = Modifier.height(8.dp))
        OutlinedTextField(value = toDate, onValueChange = { toDate = it }, label = { Text("To date YYYY-MM-DD") }, modifier = Modifier.fillMaxWidth())
        Spacer(modifier = Modifier.height(8.dp))
        OutlinedTextField(value = reason, onValueChange = { reason = it }, label = { Text("Reason") }, modifier = Modifier.fillMaxWidth(), minLines = 3)
        Spacer(modifier = Modifier.height(8.dp))
        Button(onClick = {
            scope.launch {
                val ok = viewModel.submitLeave(studentId, fromDate, toDate, reason)
                message = if (ok) "Leave submitted" else "Could not submit leave"
                leaves = viewModel.fetchLeaves(studentId)
            }
        }, modifier = Modifier.fillMaxWidth()) {
            Text("Submit Leave")
        }
        message?.let { Text(it, color = MaterialTheme.colorScheme.primary) }
        Spacer(modifier = Modifier.height(16.dp))
        LazyColumn {
            items(leaves) { item ->
                Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text("${item.from_date} to ${item.to_date}", style = MaterialTheme.typography.titleMedium)
                        Text(item.status)
                        Text(item.reason)
                    }
                }
            }
        }
    }
}

@Composable
fun TransportScreen(viewModel: ParentViewModel, studentId: Int, onBack: () -> Unit) {
    var transport by remember { mutableStateOf<TransportInfo?>(null) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(studentId) {
        transport = viewModel.fetchTransport(studentId)
        isLoading = false
    }

    ScreenShell("Transport", onBack) {
        if (isLoading) {
            CircularProgressIndicator()
        } else if (transport == null) {
            Text("No transport assigned yet.")
        } else {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(transport?.route_name ?: "Route", style = MaterialTheme.typography.titleLarge)
                    Text("Vehicle: ${transport?.vehicle_no ?: "-"}")
                    Text("Driver: ${transport?.driver_name ?: "-"} (${transport?.driver_phone ?: "-"})")
                    Text("Pickup: ${transport?.pickup_point ?: "-"} at ${transport?.pickup_time ?: "-"}")
                    Text("Drop: ${transport?.drop_point ?: "-"} at ${transport?.drop_time ?: "-"}")
                    if (transport?.last_latitude != null && transport?.last_longitude != null) {
                        Text("Last GPS: ${transport?.last_latitude}, ${transport?.last_longitude}")
                        Text("Updated: ${transport?.last_updated ?: "-"}")
                    }
                    if (!transport?.live_tracking_url.isNullOrBlank()) {
                        Text("Live tracking ready")
                    }
                }
            }
        }
    }
}

@Composable
fun CalendarScreen(viewModel: ParentViewModel, studentId: Int, onBack: () -> Unit) {
    var response by remember { mutableStateOf(CalendarResponse(emptyList(), emptyList())) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(studentId) {
        response = viewModel.fetchCalendar(studentId)
        isLoading = false
    }

    ScreenShell("Calendar & Timetable", onBack) {
        if (isLoading) {
            CircularProgressIndicator()
        } else {
            LazyColumn {
                item { Text("Events", style = MaterialTheme.typography.titleLarge) }
                items(response.events) { event ->
                    ListItem(
                        headlineContent = { Text(event.title) },
                        supportingContent = { Text("${event.date} | ${event.event_type}") }
                    )
                }
                item {
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("Timetable", style = MaterialTheme.typography.titleLarge)
                }
                items(response.timetable) { entry ->
                    ListItem(
                        headlineContent = { Text("${entry.weekday} - Period ${entry.period_no}") },
                        supportingContent = { Text("${entry.subject} | ${entry.teacher_name ?: "-"} | ${entry.starts_at ?: ""}-${entry.ends_at ?: ""}") }
                    )
                }
            }
        }
    }
}

@Composable
fun MessageScreen(viewModel: ParentViewModel, studentId: Int, onBack: () -> Unit) {
    val scope = rememberCoroutineScope()
    var category by remember { mutableStateOf("General") }
    var text by remember { mutableStateOf("") }
    var messages by remember { mutableStateOf<List<ParentMessage>>(emptyList()) }

    LaunchedEffect(studentId) {
        messages = viewModel.fetchMessages(studentId)
    }

    ScreenShell("Message School", onBack) {
        OutlinedTextField(value = category, onValueChange = { category = it }, label = { Text("Category") }, modifier = Modifier.fillMaxWidth())
        Spacer(modifier = Modifier.height(8.dp))
        OutlinedTextField(value = text, onValueChange = { text = it }, label = { Text("Message") }, modifier = Modifier.fillMaxWidth(), minLines = 3)
        Spacer(modifier = Modifier.height(8.dp))
        Button(onClick = {
            scope.launch {
                if (viewModel.sendMessage(studentId, category, text)) {
                    text = ""
                    messages = viewModel.fetchMessages(studentId)
                }
            }
        }, modifier = Modifier.fillMaxWidth()) {
            Text("Send")
        }
        Spacer(modifier = Modifier.height(16.dp))
        LazyColumn {
            items(messages) { item ->
                Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text("${item.sender_role.uppercase()} - ${item.category}", style = MaterialTheme.typography.titleMedium)
                        Text(item.message)
                        Text("${item.date} | ${item.status}", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}

@Composable
fun NotificationScreen(viewModel: ParentViewModel, onBack: () -> Unit) {
    var notifications by remember { mutableStateOf<List<AppNotification>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(Unit) {
        notifications = viewModel.fetchNotifications()
        isLoading = false
    }

    ScreenShell("Alerts", onBack) {
        if (isLoading) {
            CircularProgressIndicator()
        } else {
            LazyColumn {
                items(notifications) { item ->
                    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Text(item.title, style = MaterialTheme.typography.titleMedium)
                            if (!item.body.isNullOrBlank()) Text(item.body)
                            Text(item.date, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun AssistantScreen(viewModel: ParentViewModel, onBack: () -> Unit) {
    val scope = rememberCoroutineScope()
    var question by remember { mutableStateOf("") }
    var answer by remember { mutableStateOf("Ask about fees, attendance, homework, transport, or school help.") }

    ScreenShell("Ask JSPS", onBack) {
        OutlinedTextField(value = question, onValueChange = { question = it }, label = { Text("Your question") }, modifier = Modifier.fillMaxWidth(), minLines = 3)
        Spacer(modifier = Modifier.height(8.dp))
        Button(onClick = {
            scope.launch {
                answer = viewModel.askAssistant(question)
            }
        }, modifier = Modifier.fillMaxWidth()) {
            Text("Ask")
        }
        Spacer(modifier = Modifier.height(16.dp))
        Card(modifier = Modifier.fillMaxWidth()) {
            Text(answer, modifier = Modifier.padding(16.dp))
        }
    }
}
