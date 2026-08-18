package com.jsps.parentapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.jsps.parentapp.ui.viewmodels.ParentViewModel
import com.jsps.parentapp.data.remote.Result

@Composable
fun ResultScreen(viewModel: ParentViewModel, studentId: Int, onBack: () -> Unit) {
    var results by remember { mutableStateOf<List<Result>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(studentId) {
        results = viewModel.fetchResults(studentId)
        isLoading = false
    }

    Column(modifier = Modifier.padding(16.dp)) {
        Button(onClick = onBack) { Text("Back") }
        Spacer(modifier = Modifier.height(16.dp))
        Text(text = "Academic Results", style = MaterialTheme.typography.headlineSmall)
        Spacer(modifier = Modifier.height(16.dp))

        if (isLoading) {
            CircularProgressIndicator()
        } else if (results.isEmpty()) {
            Text("No results published yet.")
        } else {
            LazyColumn {
                items(results) { result ->
                    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(result.term, style = MaterialTheme.typography.titleMedium)
                            Spacer(modifier = Modifier.height(4.dp))
                            Text("Percentage: ${result.percentage}% | Grade: ${result.grade}")
                            if (!result.remarks.isNullOrEmpty()) {
                                Spacer(modifier = Modifier.height(4.dp))
                                Text("Remarks: ${result.remarks}")
                            }
                        }
                    }
                }
            }
        }
    }
}
