package com.studentstation.app.presentation.features.practice

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PracticeScreen(
    viewModel: PracticeViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("🎯 Practice Sets", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background
                )
            )
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            if (uiState.isLoading) {
                CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
            } else if (uiState.error != null) {
                Text(
                    text = "Error: ${uiState.error}",
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.align(Alignment.Center)
                )
            } else if (uiState.questions.isEmpty()) {
                Text(
                    text = "No questions available for this exam.",
                    modifier = Modifier.align(Alignment.Center)
                )
            } else if (uiState.isFinished) {
                QuizResultScreen(
                    score = uiState.score,
                    total = uiState.questions.size,
                    onRestart = { viewModel.restartQuiz() }
                )
            } else {
                QuizContent(
                    uiState = uiState,
                    onOptionSelected = { viewModel.selectOption(it) },
                    onSubmit = { viewModel.submitAnswer() },
                    onNext = { viewModel.nextQuestion() }
                )
            }
        }
    }
}

@Composable
fun QuizContent(
    uiState: PracticeUiState,
    onOptionSelected: (String) -> Unit,
    onSubmit: () -> Unit,
    onNext: () -> Unit
) {
    val currentQuestion = uiState.questions[uiState.currentQuestionIndex]

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        // Progress Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Question ${uiState.currentQuestionIndex + 1} / ${uiState.questions.size}",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary
            )
            Text(
                text = "Score: ${uiState.score}",
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.Bold
            )
        }
        
        LinearProgressIndicator(
            progress = { (uiState.currentQuestionIndex + 1) / uiState.questions.size.toFloat() },
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp)
                .height(8.dp),
            strokeCap = StrokeCap.Round
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Question Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
        ) {
            Text(
                text = currentQuestion.questionText,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.padding(16.dp)
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Options
        val optionsMap = currentQuestion.options.filterValues { !it.isNullOrEmpty() }
        optionsMap.forEach { (key, value) ->
            val isSelected = uiState.selectedOption == key
            val isCorrectAnswer = currentQuestion.correctAnswer == key

            val containerColor = when {
                !uiState.isSubmitted && isSelected -> MaterialTheme.colorScheme.primaryContainer
                uiState.isSubmitted && isCorrectAnswer -> Color(0xFF4CAF50).copy(alpha = 0.2f) // Green
                uiState.isSubmitted && isSelected && !isCorrectAnswer -> MaterialTheme.colorScheme.errorContainer // Red
                else -> MaterialTheme.colorScheme.surface
            }

            val borderColor = when {
                !uiState.isSubmitted && isSelected -> MaterialTheme.colorScheme.primary
                uiState.isSubmitted && isCorrectAnswer -> Color(0xFF4CAF50)
                uiState.isSubmitted && isSelected && !isCorrectAnswer -> MaterialTheme.colorScheme.error
                else -> MaterialTheme.colorScheme.outlineVariant
            }

            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 6.dp),
                border = BorderStroke(if (isSelected || (uiState.isSubmitted && isCorrectAnswer)) 2.dp else 1.dp, borderColor),
                colors = CardDefaults.cardColors(containerColor = containerColor),
                onClick = { if (!uiState.isSubmitted) onOptionSelected(key) }
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "$key.",
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(end = 12.dp)
                    )
                    Text(
                        text = value ?: "",
                        style = MaterialTheme.typography.bodyLarge,
                        modifier = Modifier.weight(1f)
                    )
                    
                    if (uiState.isSubmitted && isCorrectAnswer) {
                        Icon(Icons.Default.CheckCircle, contentDescription = "Correct", tint = Color(0xFF4CAF50))
                    } else if (uiState.isSubmitted && isSelected && !isCorrectAnswer) {
                        Icon(Icons.Default.Warning, contentDescription = "Wrong", tint = MaterialTheme.colorScheme.error)
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Explanation Box
        if (uiState.isSubmitted && !currentQuestion.explanation.isNullOrEmpty()) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.5f))
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Solution / Explanation:", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.secondary)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(currentQuestion.explanation)
                }
            }
            Spacer(modifier = Modifier.height(24.dp))
        }

        // Action Button
        Button(
            onClick = {
                if (uiState.isSubmitted) onNext() else onSubmit()
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            enabled = uiState.selectedOption != null,
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(
                text = if (uiState.isSubmitted) "Next Question" else "Check Answer",
                fontSize = MaterialTheme.typography.titleMedium.fontSize
            )
        }
    }
}

@Composable
fun QuizResultScreen(score: Int, total: Int, onRestart: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            imageVector = Icons.Default.CheckCircle,
            contentDescription = "Completed",
            modifier = Modifier.size(100.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Text(
            text = "Test Completed!",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "You scored",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Text(
            text = "$score / $total",
            style = MaterialTheme.typography.displayMedium,
            fontWeight = FontWeight.ExtraBold,
            color = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(48.dp))
        
        Button(
            onClick = onRestart,
            modifier = Modifier.fillMaxWidth().height(56.dp)
        ) {
            Text("Restart Practice Set")
        }
    }
}
