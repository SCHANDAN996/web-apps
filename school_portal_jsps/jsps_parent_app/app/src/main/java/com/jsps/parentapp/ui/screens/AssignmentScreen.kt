package com.jsps.parentapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.jsps.parentapp.ui.viewmodels.ParentViewModel
import com.jsps.parentapp.data.remote.Assignment

@Composable
fun AssignmentScreen(viewModel: ParentViewModel, className: String, onBack: () -> Unit) {
    var assignments by remember { mutableStateOf<List<Assignment>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(className) {
        assignments = viewModel.fetchAssignments(className)
        isLoading = false
    }

    Column(modifier = Modifier.padding(16.dp)) {
        Button(onClick = onBack) { Text("Back") }
        Spacer(modifier = Modifier.height(16.dp))
        Text(text = "Class $className Assignments", style = MaterialTheme.typography.headlineSmall)
        Spacer(modifier = Modifier.height(16.dp))

        if (isLoading) {
            CircularProgressIndicator()
        } else if (assignments.isEmpty()) {
            Text("No homework or assignments posted yet.")
        } else {
            LazyColumn {
                items(assignments) { assignment ->
                    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(assignment.title, style = MaterialTheme.typography.titleMedium)
                            Text("Subject: ${assignment.subject}", style = MaterialTheme.typography.bodyMedium)
                            if (assignment.due_date != null) {
                                Spacer(modifier = Modifier.height(4.dp))
                                Text("Due Date: ${assignment.due_date}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error)
                            }
                        }
                    }
                }
            }
        }
    }
}
