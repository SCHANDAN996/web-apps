package com.studentstation.app.presentation.features.focus

import androidx.compose.animation.core.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.studentstation.app.presentation.theme.*

@Composable
fun FocusScreen(viewModel: FocusViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        if (uiState.subjectName != null) {
            Text("🎯 फोकस: ${uiState.subjectName}", style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 4.dp), color = Primary)
            TextButton(onClick = { viewModel.clearSubject() }) {
                Text("विषय हटाएं")
            }
        } else {
            Text("🎯 फोकस सत्र", style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 8.dp))
        }
        Text(
            text = when (uiState.sessionState) {
                SessionState.IDLE -> "एक सत्र शुरू करो और ध्यान लगाओ!"
                SessionState.WORKING -> "📚 पढ़ाई जारी है... बहुत अच्छे!"
                SessionState.BREAK -> "☕ ब्रेक टाइम! आराम करो"
                SessionState.PAUSED -> "⏸ रुका हुआ"
            },
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center, modifier = Modifier.padding(bottom = 32.dp)
        )
        // Timer Circle
        Card(modifier = Modifier.size(260.dp), shape = CircleShape,
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            elevation = CardDefaults.cardElevation(8.dp)) {
            Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
                CircularProgressIndicator(
                    progress = { uiState.progress }, modifier = Modifier.size(240.dp),
                    color = when (uiState.sessionState) {
                        SessionState.WORKING -> Primary; SessionState.BREAK -> Tertiary
                        else -> MaterialTheme.colorScheme.surfaceVariant
                    },
                    trackColor = MaterialTheme.colorScheme.surfaceVariant, strokeWidth = 8.dp
                )
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(String.format("%02d:%02d", uiState.remainingSeconds / 60, uiState.remainingSeconds % 60),
                        style = MaterialTheme.typography.displayLarge, fontWeight = FontWeight.Bold)
                    Text(when (uiState.sessionState) { SessionState.WORKING -> "फोकस"; SessionState.BREAK -> "ब्रेक"; else -> "तैयार" },
                        style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
        Spacer(modifier = Modifier.height(32.dp))
        // Type selector (only when idle)
        if (uiState.sessionState == SessionState.IDLE) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("POMODORO" to "पोमोडोरो\n25 मिनट", "DEEP_WORK" to "डीप वर्क\n90 मिनट", "CUSTOM" to "कस्टम\n${uiState.customMinutes} मिनट").forEach { (type, label) ->
                    Card(onClick = { viewModel.selectType(type) }, modifier = Modifier.weight(1f), shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(containerColor = if (uiState.selectedType == type) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surface)) {
                        Text(label, modifier = Modifier.padding(12.dp).fillMaxWidth(), textAlign = TextAlign.Center,
                            style = MaterialTheme.typography.labelLarge, fontWeight = if (uiState.selectedType == type) FontWeight.Bold else FontWeight.Normal)
                    }
                }
            }
            if (uiState.selectedType == "CUSTOM") {
                Spacer(modifier = Modifier.height(16.dp))
                Slider(value = uiState.customMinutes.toFloat(), onValueChange = { viewModel.setCustomMinutes(it.toInt()) },
                    valueRange = 5f..120f, steps = 22, colors = SliderDefaults.colors(thumbColor = Primary, activeTrackColor = Primary))
            }
        }
        Spacer(modifier = Modifier.height(24.dp))
        // Control buttons
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            when (uiState.sessionState) {
                SessionState.IDLE -> Button(onClick = { viewModel.startSession() }, modifier = Modifier.height(56.dp),
                    shape = RoundedCornerShape(28.dp), colors = ButtonDefaults.buttonColors(containerColor = Primary)) {
                    Icon(Icons.Filled.PlayArrow, null); Spacer(Modifier.width(8.dp)); Text("सत्र शुरू करो")
                }
                SessionState.WORKING, SessionState.BREAK -> {
                    FilledTonalButton(onClick = { viewModel.pauseSession() }, modifier = Modifier.height(56.dp), shape = RoundedCornerShape(28.dp)) {
                        Icon(Icons.Filled.Pause, null); Spacer(Modifier.width(4.dp)); Text("रोको")
                    }
                    OutlinedButton(onClick = { viewModel.stopSession() }, modifier = Modifier.height(56.dp), shape = RoundedCornerShape(28.dp)) {
                        Icon(Icons.Filled.Stop, null); Spacer(Modifier.width(4.dp)); Text("बंद करो")
                    }
                }
                SessionState.PAUSED -> {
                    Button(onClick = { viewModel.resumeSession() }, modifier = Modifier.height(56.dp), shape = RoundedCornerShape(28.dp)) {
                        Icon(Icons.Filled.PlayArrow, null); Spacer(Modifier.width(4.dp)); Text("जारी रखो")
                    }
                    OutlinedButton(onClick = { viewModel.stopSession() }, modifier = Modifier.height(56.dp), shape = RoundedCornerShape(28.dp)) {
                        Icon(Icons.Filled.Stop, null); Spacer(Modifier.width(4.dp)); Text("बंद करो")
                    }
                }
            }
        }
    }
}
