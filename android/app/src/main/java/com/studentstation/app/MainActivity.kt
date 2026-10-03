package com.studentstation.app

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.*
import com.studentstation.app.presentation.navigation.StudentStationNavHost
import com.studentstation.app.presentation.theme.StudentStationTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    companion object {
        private const val PREFS_NAME = "student_station_prefs"
        private const val KEY_ONBOARDING_DONE = "onboarding_completed"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            var showOnboarding by remember {
                mutableStateOf(!prefs.getBoolean(KEY_ONBOARDING_DONE, false))
            }

            StudentStationTheme {
                StudentStationNavHost(
                    showOnboarding = showOnboarding,
                    onOnboardingComplete = {
                        prefs.edit().putBoolean(KEY_ONBOARDING_DONE, true).apply()
                        showOnboarding = false
                    }
                )
            }
        }
    }
}
