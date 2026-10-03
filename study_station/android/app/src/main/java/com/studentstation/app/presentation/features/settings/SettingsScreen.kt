package com.studentstation.app.presentation.features.settings

import android.content.Intent
import android.provider.Settings
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.studentstation.app.domain.model.BlockedApp
import com.studentstation.app.domain.model.TimerStrategy
import com.studentstation.app.presentation.theme.*
import com.studentstation.app.service.StudentStationAccessibilityService

@Composable
fun SettingsScreen(viewModel: SettingsViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val context = LocalContext.current
    var isPinVerified by remember { mutableStateOf(false) }
    var showVerifyDialog by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) { viewModel.initializeDefaultApps() }

    // अगर PIN सेट है और verify नहीं हुआ — तो सेटिंग्स मत दिखाओ
    if (uiState.parentPinEnabled && !isPinVerified) {
        // PIN Entry Gate Screen
        Column(
            modifier = Modifier.fillMaxSize().padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text("🔐", style = MaterialTheme.typography.displayLarge)
            Spacer(modifier = Modifier.height(16.dp))
            Text("सेटिंग्स लॉक हैं", style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            Text("सेटिंग्स बदलने के लिए अभिभावक PIN डालें",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = androidx.compose.ui.text.style.TextAlign.Center)
            Spacer(modifier = Modifier.height(24.dp))
            Button(
                onClick = { showVerifyDialog = true },
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth(0.7f).height(52.dp)
            ) {
                Icon(Icons.Filled.Lock, null)
                Spacer(Modifier.width(8.dp))
                Text("PIN डालें", fontWeight = FontWeight.Bold)
            }
        }

        if (showVerifyDialog) {
            PinVerifyDialog(
                onDismiss = { showVerifyDialog = false },
                onVerified = { pin ->
                    if (viewModel.verifyPin(pin)) {
                        isPinVerified = true
                        showVerifyDialog = false
                    }
                }
            )
        }
        return
    }

    // --- मुख्य सेटिंग्स (PIN verified या PIN सेट नहीं) ---
    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)
    ) {
        Text("⚙️ सेटिंग्स", style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 16.dp))

        // Service Status Card
        val isActive = StudentStationAccessibilityService.isServiceRunning
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(
                containerColor = if (isActive) Primary.copy(alpha = 0.15f)
                else ErrorRed.copy(alpha = 0.15f)
            )
        ) {
            Row(
                modifier = Modifier.padding(16.dp).fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text(
                        if (isActive) "✅ सर्विस चालू है" else "❌ सर्विस बंद है",
                        style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold
                    )
                    Text(
                        if (isActive) "ऐप्स ब्लॉक हो रहे हैं" else "Accessibility Settings में जाकर enable करें",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                if (!isActive) {
                    FilledTonalButton(
                        onClick = {
                            context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS).apply {
                                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                            })
                        },
                        shape = RoundedCornerShape(12.dp)
                    ) { Text("Enable") }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Blocked Apps Section
        Text("🚫 ब्लॉक किए गए ऐप्स", style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(bottom = 8.dp))
        Text("ऐप्स को चालू/बंद करें और प्रतीक्षा समय सेट करें",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(bottom = 12.dp))

        uiState.blockedApps.forEach { app ->
            BlockedAppCard(
                app = app,
                onToggle = { viewModel.toggleAppBlocking(app) },
                onWaitTimeChange = { viewModel.updateWaitTime(app, it) },
                onStrategyChange = { viewModel.updateTimerStrategy(app, it) },
                onToggleShorts = { viewModel.toggleBlockShorts(app) },
                onToggleReels = { viewModel.toggleBlockReels(app) }
            )
            Spacer(modifier = Modifier.height(8.dp))
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Parent PIN Section
        Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(20.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Filled.Lock, null, tint = Secondary)
                    Spacer(Modifier.width(8.dp))
                    Text("🔐 अभिभावक PIN", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                }
                Text(
                    if (uiState.parentPinEnabled) "PIN सक्रिय है — सेटिंग्स बदलने के लिए PIN आवश्यक"
                    else "PIN सेट करें ताकि बच्चा सेटिंग्स न बदल सके",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(top = 4.dp))
                Spacer(modifier = Modifier.height(12.dp))
                Button(onClick = { viewModel.togglePinDialog() }, shape = RoundedCornerShape(12.dp)) {
                    Text(if (uiState.parentPinEnabled) "PIN बदलें" else "PIN सेट करें")
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Overlay Permission
        Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text("🪟 ओवरले अनुमति", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                Text("ऐप को दूसरे ऐप्स के ऊपर दिखाने की अनुमति", style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 4.dp))
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedButton(onClick = {
                    context.startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION).apply {
                        flags = Intent.FLAG_ACTIVITY_NEW_TASK
                    })
                }, shape = RoundedCornerShape(12.dp)) { Text("ओवरले सेटिंग खोलें") }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Privacy Notice
        Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text("🔒 गोपनीयता", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                Spacer(modifier = Modifier.height(8.dp))
                Text("• सारा डेटा केवल आपके फ़ोन पर स्टोर होता है\n• कोई डेटा इंटरनेट पर नहीं भेजा जाता\n• हम केवल ऐप के नाम पढ़ते हैं, स्क्रीन कंटेंट नहीं\n• All data stays on your device — zero internet access",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }

        Spacer(modifier = Modifier.height(80.dp))
    }

    // Parent PIN Set Dialog
    if (uiState.showPinDialog) {
        ParentPinDialog(
            currentPin = uiState.parentPin,
            onDismiss = { viewModel.togglePinDialog() },
            onSavePin = { viewModel.saveParentPin(it) }
        )
    }
}

/**
 * PIN Verify Dialog — सेटिंग्स खोलने से पहले PIN पूछो
 */
@Composable
fun PinVerifyDialog(
    onDismiss: () -> Unit,
    onVerified: (String) -> Unit
) {
    var pin by remember { mutableStateOf("") }
    var error by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("🔐 अभिभावक PIN डालें") },
        text = {
            Column {
                Text("सेटिंग्स एक्सेस करने के लिए PIN डालें",
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(bottom = 12.dp))
                OutlinedTextField(
                    value = pin, onValueChange = { if (it.length <= 6) pin = it },
                    label = { Text("PIN") },
                    visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                if (error.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(error, color = ErrorRed, style = MaterialTheme.typography.bodySmall)
                }
            }
        },
        confirmButton = {
            Button(onClick = {
                if (pin.length < 4) {
                    error = "PIN कम से कम 4 अंकों का होना चाहिए"
                } else {
                    onVerified(pin)
                    if (pin.isNotEmpty()) error = "❌ गलत PIN! दोबारा कोशिश करें"
                }
            }) { Text("अनलॉक करें") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("रद्द करें") }
        }
    )
}

@Composable
fun ParentPinDialog(
    currentPin: String,
    onDismiss: () -> Unit,
    onSavePin: (String) -> Unit
) {
    var pin by remember { mutableStateOf("") }
    var confirmPin by remember { mutableStateOf("") }
    var error by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("🔐 अभिभावक PIN सेट करें") },
        text = {
            Column {
                Text("4-6 अंकों का PIN डालें", style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(bottom = 12.dp))
                OutlinedTextField(
                    value = pin, onValueChange = { if (it.length <= 6) pin = it },
                    label = { Text("नया PIN") },
                    visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = confirmPin, onValueChange = { if (it.length <= 6) confirmPin = it },
                    label = { Text("PIN पुष्टि करें") },
                    visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                if (error.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(error, color = ErrorRed, style = MaterialTheme.typography.bodySmall)
                }
            }
        },
        confirmButton = {
            Button(onClick = {
                when {
                    pin.length < 4 -> error = "PIN कम से कम 4 अंकों का होना चाहिए"
                    pin != confirmPin -> error = "PIN मिलता नहीं है!"
                    else -> onSavePin(pin)
                }
            }) { Text("सेव करें") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("रद्द करें") }
        }
    )
}

@Composable
fun BlockedAppCard(
    app: BlockedApp,
    onToggle: () -> Unit,
    onWaitTimeChange: (Int) -> Unit,
    onStrategyChange: (TimerStrategy) -> Unit,
    onToggleShorts: () -> Unit,
    onToggleReels: () -> Unit
) {
    var expanded by remember { mutableStateOf(false) }
    val icon = when {
        app.packageName.contains("youtube") -> "🎬"
        app.packageName.contains("instagram.android") -> "📸"
        app.packageName.contains("facebook") -> "📘"
        app.packageName.contains("snapchat") -> "👻"
        app.packageName.contains("twitter") -> "🐦"
        app.packageName.contains("barcelona") -> "🧵"
        else -> "📱"
    }

    Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                Text(icon, style = MaterialTheme.typography.headlineSmall)
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(app.displayName, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                    Text("⏳ ${app.waitTimeSeconds}s • ${strategyLabel(app.timerStrategy)}",
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Switch(checked = app.isBlocked, onCheckedChange = { onToggle() },
                    colors = SwitchDefaults.colors(checkedTrackColor = Primary))
            }

            if (expanded) {
                Spacer(modifier = Modifier.height(12.dp))
                HorizontalDivider()
                Spacer(modifier = Modifier.height(12.dp))

                // Sub-component toggles
                if (app.packageName.contains("youtube")) {
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                        Text("🎬 Shorts ब्लॉक करें", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                        Switch(checked = app.blockShorts, onCheckedChange = { onToggleShorts() }, modifier = Modifier.height(32.dp))
                    }
                }
                if (app.packageName.contains("instagram") || app.packageName.contains("facebook")) {
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                        Text("📱 Reels ब्लॉक करें", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                        Switch(checked = app.blockReels, onCheckedChange = { onToggleReels() }, modifier = Modifier.height(32.dp))
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))
                Text("⏳ प्रतीक्षा समय: ${app.waitTimeSeconds} सेकंड", style = MaterialTheme.typography.bodyMedium)
                Slider(value = app.waitTimeSeconds.toFloat(), onValueChange = { onWaitTimeChange(it.toInt()) },
                    valueRange = 10f..120f, steps = 10,
                    colors = SliderDefaults.colors(thumbColor = Primary, activeTrackColor = Primary))

                Text("🎯 टाइमर रणनीति", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 4.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(4.dp), modifier = Modifier.padding(top = 4.dp)) {
                    TimerStrategy.entries.forEach { strategy ->
                        FilterChip(selected = app.timerStrategy == strategy,
                            onClick = { onStrategyChange(strategy) },
                            label = { Text(strategyLabel(strategy), style = MaterialTheme.typography.labelSmall) })
                    }
                }
            }

            TextButton(onClick = { expanded = !expanded }, modifier = Modifier.align(Alignment.End)) {
                Text(if (expanded) "कम देखें ▲" else "और देखें ▼")
            }
        }
    }
}

fun strategyLabel(strategy: TimerStrategy): String = when(strategy) {
    TimerStrategy.FIXED -> "निश्चित"
    TimerStrategy.PROGRESSIVE -> "बढ़ता"
    TimerStrategy.TASK_BASED -> "सवाल"
    TimerStrategy.BREATHING -> "श्वसन"
}
