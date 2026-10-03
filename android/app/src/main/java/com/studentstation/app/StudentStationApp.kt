package com.studentstation.app

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import dagger.hilt.android.HiltAndroidApp

/**
 * Student Station Application Class
 * Hilt entry point and notification channel setup
 */
@HiltAndroidApp
class StudentStationApp : Application() {

    companion object {
        const val CHANNEL_POMODORO = "pomodoro_channel"
        const val CHANNEL_BLOCKING = "blocking_channel"
        const val CHANNEL_STREAK = "streak_channel"
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }

    private fun createNotificationChannels() {
        val pomodoroChannel = NotificationChannel(
            CHANNEL_POMODORO,
            getString(R.string.channel_pomodoro),
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = getString(R.string.channel_pomodoro_desc)
            setShowBadge(false)
        }

        val blockingChannel = NotificationChannel(
            CHANNEL_BLOCKING,
            getString(R.string.channel_blocking),
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = getString(R.string.channel_blocking_desc)
        }

        val streakChannel = NotificationChannel(
            CHANNEL_STREAK,
            getString(R.string.channel_streak),
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = getString(R.string.channel_streak_desc)
        }

        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(pomodoroChannel)
        manager.createNotificationChannel(blockingChannel)
        manager.createNotificationChannel(streakChannel)
    }
}
