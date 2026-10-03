package com.studentstation.app.presentation.features.onboarding

import android.content.Intent
import android.provider.Settings
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.studentstation.app.presentation.theme.*
import com.studentstation.app.service.StudentStationAccessibilityService
import kotlinx.coroutines.launch

data class OnboardingPage(
    val emoji: String,
    val title: String,
    val description: String,
    val buttonText: String,
    val action: OnboardingAction
)

enum class OnboardingAction {
    NEXT, ACCESSIBILITY, OVERLAY, FINISH
}

@Composable
fun OnboardingScreen(onComplete: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    val pages = listOf(
        OnboardingPage(
            emoji = "🎯",
            title = "Student Station में\nस्वागत है!",
            description = "यह ऐप तुम्हें YouTube Shorts, Instagram Reels, और Facebook से बचाकर पढ़ाई पर फोकस रखने में मदद करेगा।\n\nतुम्हारा सारा डेटा सिर्फ तुम्हारे फ़ोन पर रहता है।\n🔒 कोई इंटरनेट नहीं — पूरी गोपनीयता!",
            buttonText = "शुरू करें 🚀",
            action = OnboardingAction.NEXT
        ),
        OnboardingPage(
            emoji = "♿",
            title = "Accessibility\nService चालू करें",
            description = "Student Station को शॉर्ट्स और रील्स पहचानने के लिए Accessibility Service की ज़रूरत है।\n\n⚠️ हम सिर्फ ऐप के नाम पढ़ते हैं — तुम्हारा कोई पर्सनल डेटा नहीं।\n\nSettings में जाकर Student Station को enable करो।",
            buttonText = "Accessibility Settings खोलें",
            action = OnboardingAction.ACCESSIBILITY
        ),
        OnboardingPage(
            emoji = "🪟",
            title = "ओवरले अनुमति\nदें",
            description = "जब शॉर्ट्स या रील्स चलेगा, तब ऐप एक 'माइंडफुल पॉज़' स्क्रीन दिखाएगा।\n\nइसके लिए 'Display over other apps' परमिशन चाहिए।",
            buttonText = "ओवरले Settings खोलें",
            action = OnboardingAction.OVERLAY
        ),
        OnboardingPage(
            emoji = "🌳",
            title = "तैयार हो!\nअब पढ़ाई शुरू करो!",
            description = "🎬 YouTube Shorts — ब्लॉक ✅\n📸 Instagram Reels — ब्लॉक ✅\n📘 Facebook Reels — ब्लॉक ✅\n👻 Snapchat — ब्लॉक ✅\n\nजितना फोकस करोगे, उतने पेड़ उगेंगे! 🌲\nहर दिन XP कमाओ और लेवल बढ़ाओ! ⭐",
            buttonText = "Dashboard पर जाओ! 🎉",
            action = OnboardingAction.FINISH
        )
    )

    val pagerState = rememberPagerState(pageCount = { pages.size })

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(DarkBackground, DarkSurface)
                )
            )
    ) {
        HorizontalPager(
            state = pagerState,
            modifier = Modifier.fillMaxSize(),
            userScrollEnabled = false // Force using buttons
        ) { page ->
            OnboardingPageContent(
                page = pages[page],
                onAction = {
                    when (pages[page].action) {
                        OnboardingAction.NEXT -> {
                            scope.launch { pagerState.animateScrollToPage(page + 1) }
                        }
                        OnboardingAction.ACCESSIBILITY -> {
                            context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS).apply {
                                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                            })
                            scope.launch { pagerState.animateScrollToPage(page + 1) }
                        }
                        OnboardingAction.OVERLAY -> {
                            context.startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION).apply {
                                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                            })
                            scope.launch { pagerState.animateScrollToPage(page + 1) }
                        }
                        OnboardingAction.FINISH -> {
                            onComplete()
                        }
                    }
                },
                onSkip = {
                    if (page < pages.size - 1) {
                        scope.launch { pagerState.animateScrollToPage(page + 1) }
                    }
                },
                showSkip = page in 1..2
            )
        }

        // Page Indicators
        Row(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 32.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            repeat(pages.size) { index ->
                Box(
                    modifier = Modifier
                        .size(if (pagerState.currentPage == index) 24.dp else 8.dp, 8.dp)
                        .clip(CircleShape)
                        .background(
                            if (pagerState.currentPage == index) Primary
                            else Primary.copy(alpha = 0.3f)
                        )
                )
            }
        }
    }
}

@Composable
fun OnboardingPageContent(
    page: OnboardingPage,
    onAction: () -> Unit,
    onSkip: () -> Unit,
    showSkip: Boolean
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Spacer(modifier = Modifier.weight(0.2f))

        // Big emoji
        Text(
            text = page.emoji,
            fontSize = 80.sp,
            modifier = Modifier.padding(bottom = 24.dp)
        )

        // Title
        Text(
            text = page.title,
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = DarkOnBackground,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        // Description
        Text(
            text = page.description,
            style = MaterialTheme.typography.bodyLarge,
            color = DarkOnSurface,
            textAlign = TextAlign.Center,
            lineHeight = 24.sp,
            modifier = Modifier.padding(horizontal = 8.dp)
        )

        Spacer(modifier = Modifier.weight(0.3f))

        // Action button
        Button(
            onClick = onAction,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            shape = RoundedCornerShape(28.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Primary)
        ) {
            Text(page.buttonText, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        }

        if (showSkip) {
            TextButton(onClick = onSkip, modifier = Modifier.padding(top = 8.dp)) {
                Text("बाद में करें →", color = DarkOnSurfaceVariant)
            }
        }

        Spacer(modifier = Modifier.height(48.dp))
    }
}
