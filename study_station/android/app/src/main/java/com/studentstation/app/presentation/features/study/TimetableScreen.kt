package com.studentstation.app.presentation.features.study

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.studentstation.app.data.local.entity.SubjectEntity
import com.studentstation.app.data.local.entity.TimetableEntryEntity

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TimetableScreen(
    viewModel: TimetableViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit,
    onStartFocusSession: (Long, String) -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    val selectedDay by viewModel.selectedDay.collectAsState()
    val days = listOf("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Smart Timetable") },
                actions = {
                    IconButton(onClick = { viewModel.autoGenerateTimetable() }) {
                        Icon(Icons.Default.AutoAwesome, contentDescription = "Auto Generate")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Day selector
            LazyRow(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 12.dp),
                horizontalArrangement = Arrangement.SpaceEvenly,
                contentPadding = PaddingValues(horizontal = 8.dp)
            ) {
                items(7) { index ->
                    val dayNum = index + 1
                    FilterChip(
                        selected = selectedDay == dayNum,
                        onClick = { viewModel.selectDay(dayNum) },
                        label = { Text(days[index]) },
                        modifier = Modifier.padding(horizontal = 4.dp)
                    )
                }
            }

            if (uiState.subjects.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(
                        "Please add subjects in the Study Plan first.",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            } else if (uiState.entries.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            "No sessions scheduled for today.",
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(onClick = { viewModel.autoGenerateTimetable() }) {
                            Icon(Icons.Default.AutoAwesome, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Auto-Generate Weekly Plan")
                        }
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(uiState.entries) { entry ->
                        val subject = uiState.subjects.find { it.id == entry.subjectId }
                        if (subject != null) {
                            TimetableEntryCard(
                                entry = entry,
                                subject = subject,
                                onDelete = { viewModel.deleteEntry(entry) },
                                onStartSession = { onStartFocusSession(subject.id, subject.name) }
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun TimetableEntryCard(
    entry: TimetableEntryEntity,
    subject: SubjectEntity,
    onDelete: () -> Unit,
    onStartSession: () -> Unit
) {
    val startHour = entry.startTimeMinutes / 60
    val startMin = entry.startTimeMinutes % 60
    val endMinutes = entry.startTimeMinutes + entry.durationMinutes
    val endHour = endMinutes / 60
    val endMin = endMinutes % 60

    val timeString = String.format("%02d:%02d - %02d:%02d", startHour, startMin, endHour, endMin)

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = timeString,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.primary
                )
                Text(
                    text = subject.name,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "${entry.durationMinutes} mins Focus Session",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            IconButton(onClick = onStartSession) {
                Icon(
                    Icons.Default.PlayArrow,
                    contentDescription = "Start Focus",
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier
                        .size(48.dp)
                        .background(MaterialTheme.colorScheme.primaryContainer, RoundedCornerShape(24.dp))
                        .padding(8.dp)
                )
            }
            
            IconButton(onClick = onDelete) {
                Icon(Icons.Default.Delete, contentDescription = "Delete", tint = MaterialTheme.colorScheme.error)
            }
        }
    }
}
