package com.studentstation.app.service

import android.app.*
import android.content.Context
import android.content.Intent
import android.os.IBinder
import android.os.SystemClock
import androidx.core.app.NotificationCompat
import com.studentstation.app.MainActivity
import com.studentstation.app.R
import com.studentstation.app.StudentStationApp
import java.util.Timer
import java.util.TimerTask

/**
 * Pomodoro Foreground Service
 * 25 मिनट पढ़ाई + 5 मिनट ब्रेक
 */
class PomodoroService : Service() {

    companion object {
        const val ACTION_START = "com.studentstation.app.ACTION_START_POMODORO"
        const val ACTION_STOP = "com.studentstation.app.ACTION_STOP_POMODORO"
        const val ACTION_PAUSE = "com.studentstation.app.ACTION_PAUSE_POMODORO"
        const val ACTION_RESUME = "com.studentstation.app.ACTION_RESUME_POMODORO"

        const val EXTRA_WORK_MINUTES = "work_minutes"
        const val EXTRA_BREAK_MINUTES = "break_minutes"
        const val EXTRA_SESSION_TYPE = "session_type"

        private const val NOTIFICATION_ID = 1001

        var isRunning = false
            private set
        var currentState = PomodoroState.IDLE
            private set
        var remainingSeconds = 0
            private set
        var totalSeconds = 0
            private set

        // Callbacks for UI updates
        var onTickCallback: ((Int, Int, PomodoroState) -> Unit)? = null
        var onSessionCompleteCallback: (() -> Unit)? = null
    }

    private var timer: Timer? = null
    private var startElapsed = 0L
    private var pausedRemaining = 0
    private var workMinutes = 25
    private var breakMinutes = 5
    private var isWorkPhase = true

    enum class PomodoroState {
        IDLE, WORKING, BREAK, PAUSED
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                workMinutes = intent.getIntExtra(EXTRA_WORK_MINUTES, 25)
                breakMinutes = intent.getIntExtra(EXTRA_BREAK_MINUTES, 5)
                startWorkPhase()
            }
            ACTION_PAUSE -> pauseTimer()
            ACTION_RESUME -> resumeTimer()
            ACTION_STOP -> stopSelf()
        }
        return START_NOT_STICKY
    }

    private fun startWorkPhase() {
        isWorkPhase = true
        currentState = PomodoroState.WORKING
        totalSeconds = workMinutes * 60
        remainingSeconds = totalSeconds
        isRunning = true

        startForeground(NOTIFICATION_ID, buildNotification("📚 पढ़ाई का समय", totalSeconds))
        startTimer()
    }

    private fun startBreakPhase() {
        isWorkPhase = false
        currentState = PomodoroState.BREAK
        totalSeconds = breakMinutes * 60
        remainingSeconds = totalSeconds

        updateNotification("☕ ब्रेक टाइम!", totalSeconds)
        startTimer()
    }

    private fun startTimer() {
        startElapsed = SystemClock.elapsedRealtime()
        timer?.cancel()
        timer = Timer()
        timer?.scheduleAtFixedRate(object : TimerTask() {
            override fun run() {
                val elapsed = (SystemClock.elapsedRealtime() - startElapsed) / 1000
                remainingSeconds = totalSeconds - elapsed.toInt()

                if (remainingSeconds <= 0) {
                    timer?.cancel()
                    if (isWorkPhase) {
                        onSessionCompleteCallback?.invoke()
                        startBreakPhase()
                    } else {
                        // Break over, could start another work phase
                        currentState = PomodoroState.IDLE
                        stopSelf()
                    }
                } else {
                    onTickCallback?.invoke(remainingSeconds, totalSeconds, currentState)
                    updateNotification(
                        if (isWorkPhase) "📚 पढ़ाई जारी है" else "☕ ब्रेक",
                        remainingSeconds
                    )
                }
            }
        }, 0, 1000)
    }

    private fun pauseTimer() {
        timer?.cancel()
        pausedRemaining = remainingSeconds
        currentState = PomodoroState.PAUSED
        updateNotification("⏸ रुका हुआ", pausedRemaining)
    }

    private fun resumeTimer() {
        currentState = if (isWorkPhase) PomodoroState.WORKING else PomodoroState.BREAK
        totalSeconds = pausedRemaining
        remainingSeconds = pausedRemaining
        startTimer()
    }

    private fun buildNotification(title: String, seconds: Int): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val min = seconds / 60
        val sec = seconds % 60

        return NotificationCompat.Builder(this, StudentStationApp.CHANNEL_POMODORO)
            .setContentTitle(title)
            .setContentText("${String.format("%02d:%02d", min, sec)} शेष")
            .setSmallIcon(R.drawable.ic_focus)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setSilent(true)
            .build()
    }

    private fun updateNotification(title: String, seconds: Int) {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(NOTIFICATION_ID, buildNotification(title, seconds))
    }

    override fun onDestroy() {
        super.onDestroy()
        timer?.cancel()
        isRunning = false
        currentState = PomodoroState.IDLE
    }
}
