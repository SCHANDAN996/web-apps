package com.studentstation.app.service

import android.content.Context
import android.graphics.PixelFormat
import android.os.Build
import android.os.SystemClock
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.Gravity
import android.view.LayoutInflater
import android.view.WindowManager
import android.widget.FrameLayout

import android.widget.ProgressBar
import android.widget.TextView
import com.studentstation.app.R
import java.util.Timer
import java.util.TimerTask

import kotlin.random.Random

/**
 * OverlayManager — माइंडफुल पॉज़ ओवरले प्रबंधक
 *
 * यह WindowManager का उपयोग करके एक पारभासी ओवरले प्रदर्शित करता है
 * जो शॉर्ट्स/रील्स प्लेयर को ढंक देता है
 */
class OverlayManager(private val context: Context) {

    private var windowManager: WindowManager =
        context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private var overlayView: FrameLayout? = null
    private var countdownTimer: Timer? = null
    private var isOverlayShowing = false

    // Tamper-proof timer base
    private var timerStartElapsed = 0L

    // Messages for mindful pause (Hindi + English)
    private val mindfulMessages = listOf(
        "अभी तुम्हारे पढ़ने का समय है।\nक्या यह वास्तव में महत्वपूर्ण है?",
        "एक पल रुको और सोचो...\nक्या तुम अपने लक्ष्य से भटक रहे हो?",
        "तुम्हारा भविष्य तुम्हारे हाथ में है।\nक्या अभी यह देखना ज़रूरी है?",
        "30 मिनट की पढ़ाई > 2 घंटे की स्क्रॉलिंग\nसमझदारी से चुनो!",
        "Is this really worth your time?\nYour goals are waiting for you!",
        "Take a deep breath.\nYou're stronger than this urge.",
        "Remember why you started.\nYour dreams need your focus!",
        "हर बार जब तुम यहाँ रुकते हो,\nतुम और मज़बूत बनते हो! 💪"
    )

    // Math problems for TASK_BASED timer
    private data class MathProblem(val question: String, val answer: Int)

    fun isShowing(): Boolean = isOverlayShowing

    /**
     * माइंडफुल पॉज़ ओवरले दिखाएं
     */
    fun showMindfulPause(
        packageName: String,
        feature: String,
        waitTimeSeconds: Int,
        timerStrategy: String,
        onWaitCompleted: () -> Unit,
        onDismissed: () -> Unit
    ) {
        if (isOverlayShowing) return

        val overlayType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_SYSTEM_ALERT
        }

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            overlayType,
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or
                    WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.CENTER
        }

        try {
            overlayView = FrameLayout(context).apply {
                // Set semi-transparent dark background
                setBackgroundColor(0xE6121218.toInt())

                val inflater = LayoutInflater.from(context)
                val contentView = inflater.inflate(R.layout.overlay_mindful_pause, this, false)
                addView(contentView)

                // Setup UI elements
                val tvMessage = contentView.findViewById<TextView>(R.id.tv_overlay_message)
                val tvTimer = contentView.findViewById<TextView>(R.id.tv_overlay_timer)
                val tvFeature = contentView.findViewById<TextView>(R.id.tv_overlay_feature)
                val progressBar = contentView.findViewById<ProgressBar>(R.id.progress_overlay_timer)
                val btnGoBack = contentView.findViewById<TextView>(R.id.btn_go_back)
                val btnProceed = contentView.findViewById<TextView>(R.id.btn_proceed)
                val tvMathQuestion = contentView.findViewById<TextView>(R.id.tv_math_question)
                val etMathAnswer = contentView.findViewById<android.widget.EditText>(R.id.et_math_answer)

                // Set random mindful message
                tvMessage.text = mindfulMessages.random()

                // Set feature info
                val featureText = when (feature) {
                    "shorts" -> "🎬 YouTube Shorts"
                    "reels" -> when {
                        packageName.contains("instagram") -> "📸 Instagram Reels"
                        packageName.contains("facebook") -> "📘 Facebook Reels"
                        else -> "📱 Reels"
                    }
                    "explore" -> "🔍 Instagram Explore"
                    "story" -> "📖 Stories"
                    "app" -> when {
                        packageName.contains("snapchat") -> "👻 Snapchat"
                        packageName.contains("twitter") -> "🐦 Twitter / X"
                        packageName.contains("barcelona") -> "🧵 Threads"
                        else -> "📱 ${getAppName(packageName)}"
                    }
                    else -> "📱 ${getAppName(packageName)}"
                }
                tvFeature.text = featureText

                // Go Back button — always available
                btnGoBack.setOnClickListener {
                    dismiss()
                    onDismissed()
                    vibrateLight()
                }

                // Handle timer strategy
                when (timerStrategy) {
                    "TASK_BASED" -> {
                        // Show math problem instead of timer
                        tvTimer.visibility = android.view.View.GONE
                        progressBar.visibility = android.view.View.GONE
                        tvMathQuestion?.visibility = android.view.View.VISIBLE
                        etMathAnswer?.visibility = android.view.View.VISIBLE

                        val problem = generateMathProblem()
                        tvMathQuestion?.text = "🧮 इसे हल करो: ${problem.question}"

                        btnProceed.text = context.getString(R.string.check_answer)
                        btnProceed.isEnabled = true
                        btnProceed.alpha = 1f
                        btnProceed.setOnClickListener {
                            val userAnswer = etMathAnswer?.text?.toString()?.toIntOrNull()
                            if (userAnswer == problem.answer) {
                                dismiss()
                                onWaitCompleted()
                            } else {
                                etMathAnswer?.setText("")
                                tvMathQuestion?.text = "❌ गलत! फिर कोशिश करो: ${problem.question}"
                                vibrateLight()
                            }
                        }
                    }
                    "BREATHING" -> {
                        // Show breathing animation text
                        tvTimer.text = "🧘 गहरी सांस लो..."
                        progressBar.max = waitTimeSeconds
                        progressBar.progress = waitTimeSeconds
                        btnProceed.isEnabled = false
                        btnProceed.alpha = 0.4f
                        startBreathingTimer(waitTimeSeconds, tvTimer, progressBar, btnProceed, onWaitCompleted)
                    }
                    else -> {
                        // FIXED or PROGRESSIVE
                        progressBar.max = waitTimeSeconds
                        progressBar.progress = waitTimeSeconds
                        btnProceed.isEnabled = false
                        btnProceed.alpha = 0.4f
                        startCountdownTimer(waitTimeSeconds, tvTimer, progressBar, btnProceed, onWaitCompleted)
                    }
                }
            }

            windowManager.addView(overlayView, params)
            isOverlayShowing = true

        } catch (e: Exception) {
            android.util.Log.e("OverlayManager", "Failed to show overlay", e)
        }
    }

    /**
     * काउंटडाउन टाइमर — SystemClock.elapsedRealtime() based (tamper-proof)
     */
    private fun startCountdownTimer(
        totalSeconds: Int,
        tvTimer: TextView,
        progressBar: ProgressBar,
        btnProceed: TextView,
        onCompleted: () -> Unit
    ) {
        timerStartElapsed = SystemClock.elapsedRealtime()
        countdownTimer?.cancel()
        countdownTimer = Timer()

        countdownTimer?.scheduleAtFixedRate(object : TimerTask() {
            override fun run() {
                val elapsed = (SystemClock.elapsedRealtime() - timerStartElapsed) / 1000
                val remaining = totalSeconds - elapsed.toInt()

                overlayView?.post {
                    if (remaining > 0) {
                        tvTimer.text = "⏳ ${remaining}s"
                        progressBar.progress = remaining
                    } else {
                        tvTimer.text = "✅ आगे बढ़ सकते हो!"
                        progressBar.progress = 0
                        btnProceed.isEnabled = true
                        btnProceed.alpha = 1f
                        btnProceed.setOnClickListener {
                            dismiss()
                            onCompleted()
                        }
                        countdownTimer?.cancel()
                        vibrateLight()
                    }
                }
            }
        }, 0, 1000)
    }

    /**
     * श्वसन अभ्यास टाइमर — breathing animation
     */
    private fun startBreathingTimer(
        totalSeconds: Int,
        tvTimer: TextView,
        progressBar: ProgressBar,
        btnProceed: TextView,
        onCompleted: () -> Unit
    ) {
        timerStartElapsed = SystemClock.elapsedRealtime()
        countdownTimer?.cancel()
        countdownTimer = Timer()

        val breathCycle = 8 // 4s inhale + 4s exhale
        countdownTimer?.scheduleAtFixedRate(object : TimerTask() {
            override fun run() {
                val elapsed = (SystemClock.elapsedRealtime() - timerStartElapsed) / 1000
                val remaining = totalSeconds - elapsed.toInt()
                val phase = (elapsed % breathCycle).toInt()

                overlayView?.post {
                    if (remaining > 0) {
                        val breathText = when {
                            phase < 4 -> "🫁 सांस अंदर लो... (${4 - phase}s)"
                            else -> "💨 सांस बाहर छोड़ो... (${8 - phase}s)"
                        }
                        tvTimer.text = "$breathText\n⏳ ${remaining}s शेष"
                        progressBar.progress = remaining
                    } else {
                        tvTimer.text = "✅ बहुत अच्छे! आगे बढ़ सकते हो!"
                        progressBar.progress = 0
                        btnProceed.isEnabled = true
                        btnProceed.alpha = 1f
                        btnProceed.setOnClickListener {
                            dismiss()
                            onCompleted()
                        }
                        countdownTimer?.cancel()
                        vibrateLight()
                    }
                }
            }
        }, 0, 1000)
    }

    /**
     * गणित का सवाल जेनरेट करें
     */
    private fun generateMathProblem(): MathProblem {
        val a = Random.nextInt(10, 99)
        val b = Random.nextInt(2, 20)
        return when (Random.nextInt(3)) {
            0 -> MathProblem("$a + $b = ?", a + b)
            1 -> {
                val multiplier = Random.nextInt(2, 9)
                MathProblem("$a × $multiplier = ?", a * multiplier)
            }
            else -> {
                val big = maxOf(a, b)
                val small = minOf(a, b)
                MathProblem("$big - $small = ?", big - small)
            }
        }
    }

    private fun getAppName(packageName: String): String = when (packageName) {
        StudentStationAccessibilityService.PKG_YOUTUBE -> "YouTube"
        StudentStationAccessibilityService.PKG_INSTAGRAM -> "Instagram"
        StudentStationAccessibilityService.PKG_FACEBOOK -> "Facebook"
        StudentStationAccessibilityService.PKG_FB_LITE -> "Facebook Lite"
        StudentStationAccessibilityService.PKG_SNAPCHAT -> "Snapchat"
        StudentStationAccessibilityService.PKG_TWITTER -> "Twitter / X"
        StudentStationAccessibilityService.PKG_THREADS -> "Threads"
        else -> packageName.substringAfterLast(".")
    }

    private fun vibrateLight() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vm = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                vm.defaultVibrator.vibrate(VibrationEffect.createOneShot(50, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                val v = context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
                v.vibrate(VibrationEffect.createOneShot(50, VibrationEffect.DEFAULT_AMPLITUDE))
            }
        } catch (_: Exception) {}
    }

    fun dismiss() {
        countdownTimer?.cancel()
        countdownTimer = null
        try {
            if (isOverlayShowing && overlayView != null) {
                windowManager.removeView(overlayView)
            }
        } catch (_: Exception) {}
        overlayView = null
        isOverlayShowing = false
    }
}
