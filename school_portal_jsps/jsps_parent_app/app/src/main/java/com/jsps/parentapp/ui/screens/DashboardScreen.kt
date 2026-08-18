package com.jsps.parentapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.jsps.parentapp.ui.viewmodels.ParentViewModel

@Composable
fun DashboardScreen(
    viewModel: ParentViewModel,
    onViewResults: (Int) -> Unit,
    onViewAssignments: (String) -> Unit,
    onViewAttendance: (Int) -> Unit,
    onViewFees: (Int) -> Unit,
    onViewLeave: (Int) -> Unit,
    onViewTransport: (Int) -> Unit,
    onViewCalendar: (Int) -> Unit,
    onViewMessages: (Int) -> Unit,
    onViewNotifications: () -> Unit,
    onAskAssistant: () -> Unit
) {
    val user by viewModel.user.collectAsState()
    val children by viewModel.children.collectAsState()
    val notices by viewModel.notices.collectAsState()

    LazyColumn(modifier = Modifier.padding(16.dp)) {
        item {
            Text(text = "Welcome, ${user?.name ?: "Parent"}", style = MaterialTheme.typography.headlineSmall)
            Spacer(modifier = Modifier.height(8.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = onViewNotifications, modifier = Modifier.weight(1f)) {
                    Text("Alerts")
                }
                OutlinedButton(onClick = onAskAssistant, modifier = Modifier.weight(1f)) {
                    Text("Ask JSPS")
                }
            }
            Spacer(modifier = Modifier.height(16.dp))
        }

        item {
            Text("Linked Students", style = MaterialTheme.typography.titleLarge)
            Spacer(modifier = Modifier.height(8.dp))
        }
        
        items(children) { child ->
            Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(child.name, style = MaterialTheme.typography.titleMedium)
                    Text("Class: ${child.class_name} | Adm No: ${child.admission_no}")
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = { onViewResults(child.id) }) {
                            Text("Results")
                        }
                        OutlinedButton(onClick = { onViewAssignments(child.class_name.split(" ")[0]) }) {
                            Text("Homework")
                        }
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(onClick = { onViewAttendance(child.id) }) { Text("Attendance") }
                        OutlinedButton(onClick = { onViewFees(child.id) }) { Text("Fees") }
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(onClick = { onViewLeave(child.id) }) { Text("Leave") }
                        OutlinedButton(onClick = { onViewTransport(child.id) }) { Text("Transport") }
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedButton(onClick = { onViewCalendar(child.id) }, modifier = Modifier.fillMaxWidth()) {
                        Text("Calendar, Timetable & Messages")
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedButton(onClick = { onViewMessages(child.id) }, modifier = Modifier.fillMaxWidth()) {
                        Text("Message School")
                    }
                }
            }
        }

        item {
            Spacer(modifier = Modifier.height(24.dp))
            Text("School Notices", style = MaterialTheme.typography.titleLarge)
            Spacer(modifier = Modifier.height(8.dp))
        }

        items(notices) { notice ->
            Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(notice.title, style = MaterialTheme.typography.titleMedium)
                    Text(notice.date, style = MaterialTheme.typography.bodySmall)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(notice.content, style = MaterialTheme.typography.bodyMedium)
                }
            }
        }
    }
}
