package com.studentstation.app.presentation.features.gamification

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.studentstation.app.presentation.theme.*

@Composable
fun GamificationScreen(viewModel: GamificationViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("🌳 मेरा जंगल", style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 16.dp))

        // Virtual Forest Card
        Card(modifier = Modifier.fillMaxWidth().height(220.dp), shape = RoundedCornerShape(24.dp),
            colors = CardDefaults.cardColors(containerColor = DarkSurface)) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                // Animated forest drawing
                val treesGrown = uiState.treesGrown
                val infiniteTransition = rememberInfiniteTransition(label = "tree")
                val sway by infiniteTransition.animateFloat(
                    initialValue = -3f, targetValue = 3f,
                    animationSpec = infiniteRepeatable(tween(2000), RepeatMode.Reverse), label = "sway"
                )
                Canvas(modifier = Modifier.fillMaxSize().padding(16.dp)) {
                    drawForest(treesGrown, sway)
                }
                if (treesGrown == 0) {
                    Text("अभी कोई पेड़ नहीं है\nपढ़ाई शुरू करो, पेड़ उगाओ! 🌱",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White.copy(alpha = 0.7f), textAlign = TextAlign.Center)
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Stats Row
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            StatBox(Modifier.weight(1f), "🌲", "${uiState.treesGrown}", "पेड़ उगे", TreeGreen)
            StatBox(Modifier.weight(1f), "🥀", "${uiState.treesWithered}", "पेड़ सूखे", ErrorRed)
            StatBox(Modifier.weight(1f), "🔥", "${uiState.currentStreak}", "दिन स्ट्रीक", StreakFlame)
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Level & XP Card
        Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(20.dp)) {
                Row(modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically) {
                    Column {
                        Text("🏆 Level ${uiState.level}", style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold, color = XpGold)
                        Text("${uiState.totalXp} XP total", style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    Icon(Icons.Filled.EmojiEvents, null, tint = XpGold, modifier = Modifier.size(48.dp))
                }
                Spacer(modifier = Modifier.height(12.dp))
                LinearProgressIndicator(
                    progress = { uiState.xpProgress },
                    modifier = Modifier.fillMaxWidth().height(12.dp)
                        .padding(vertical = 2.dp),
                    color = XpGold, trackColor = MaterialTheme.colorScheme.surfaceVariant
                )
                Text("Next level: ${uiState.xpForNextLevel} XP",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Achievements
        Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text("🏅 उपलब्धियाँ", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                Spacer(modifier = Modifier.height(12.dp))
                AchievementRow("🌱 पहला पेड़", "पहला फोकस सत्र पूरा करो", uiState.treesGrown >= 1)
                AchievementRow("🌳 छोटा बगीचा", "10 पेड़ उगाओ", uiState.treesGrown >= 10)
                AchievementRow("🔥 7 दिन स्ट्रीक", "लगातार 7 दिन पढ़ो", uiState.longestStreak >= 7)
                AchievementRow("💎 30 दिन स्ट्रीक", "लगातार 30 दिन पढ़ो", uiState.longestStreak >= 30)
                AchievementRow("🛡️ 100 प्रलोभन रोके", "100 बार शॉर्ट्स/रील्स बंद करो", uiState.totalBlocksResisted >= 100)
            }
        }

        Spacer(modifier = Modifier.height(80.dp))
    }
}

@Composable
fun StatBox(modifier: Modifier, emoji: String, value: String, label: String, color: Color) {
    Card(modifier = modifier, shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
        Column(modifier = Modifier.padding(12.dp).fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally) {
            Text(emoji, style = MaterialTheme.typography.headlineSmall)
            Text(value, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = color)
            Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
fun AchievementRow(title: String, desc: String, unlocked: Boolean) {
    Row(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically) {
        Text(if (unlocked) "✅" else "🔒", style = MaterialTheme.typography.titleMedium)
        Spacer(modifier = Modifier.width(12.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.SemiBold,
                color = if (unlocked) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant)
            Text(desc, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

fun DrawScope.drawForest(treeCount: Int, sway: Float) {
    val maxTrees = minOf(treeCount, 15)
    val groundY = size.height * 0.85f
    // Draw ground
    drawRect(color = Color(0xFF1B5E20).copy(alpha = 0.3f),
        topLeft = Offset(0f, groundY), size = androidx.compose.ui.geometry.Size(size.width, size.height - groundY))
    // Draw trees
    for (i in 0 until maxTrees) {
        val x = (size.width / (maxTrees + 1)) * (i + 1)
        val treeHeight = 40f + (i % 3) * 20f
        val trunkWidth = 8f
        // Trunk
        drawRect(Color(0xFF5D4037), topLeft = Offset(x - trunkWidth / 2 + sway, groundY - treeHeight),
            size = androidx.compose.ui.geometry.Size(trunkWidth, treeHeight))
        // Canopy
        drawCircle(Color(0xFF2E7D32), radius = 18f + (i % 2) * 6f,
            center = Offset(x + sway, groundY - treeHeight - 12f))
    }
}
