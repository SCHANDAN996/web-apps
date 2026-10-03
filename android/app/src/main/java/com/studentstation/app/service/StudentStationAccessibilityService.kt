package com.studentstation.app.service

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.Toast
import com.studentstation.app.data.local.AppDatabase
import com.studentstation.app.data.local.entity.UsageLogEntity
import kotlinx.coroutines.*

/**
 * Student Station Accessibility Service — कोर इंजन
 *
 * यह सर्विस वास्तविक समय में पहचानती है कि छात्र
 * YouTube Shorts, Instagram Reels, या Facebook Reels देख रहा है
 * और माइंडफुल पॉज़ ओवरले दिखाती है
 */
class StudentStationAccessibilityService : AccessibilityService() {

    companion object {
        private const val TAG = "SSAccessibility"

        // Target packages
        const val PKG_YOUTUBE = "com.google.android.youtube"
        const val PKG_INSTAGRAM = "com.instagram.android"
        const val PKG_FACEBOOK = "com.facebook.katana"
        const val PKG_FB_LITE = "com.facebook.lite"
        const val PKG_SNAPCHAT = "com.snapchat.android"
        const val PKG_TWITTER = "com.twitter.android"
        const val PKG_TWITTER_X = "com.twitter.android" // X app uses same package
        const val PKG_THREADS = "com.instagram.barcelona"

        // All supported packages for full-app blocking
        val ALL_SUPPORTED_PACKAGES = listOf(
            PKG_YOUTUBE, PKG_INSTAGRAM, PKG_FACEBOOK, PKG_FB_LITE,
            PKG_SNAPCHAT, PKG_TWITTER, PKG_THREADS
        )

        // YouTube Shorts view IDs (multi-indicator strategy)
        private val YOUTUBE_SHORTS_IDS = listOf(
            "com.google.android.youtube:id/reel_watch_fragment_root",
            "com.google.android.youtube:id/reel_recycler",
            "com.google.android.youtube:id/reel_player_page_container",
            "com.google.android.youtube:id/shorts_player_controls",
            "com.google.android.youtube:id/reel_progress_bar"
        )

        // Instagram Reels indicators
        private val INSTAGRAM_REELS_IDS = listOf(
            "com.instagram.android:id/clips_viewer_view_pager",
            "com.instagram.android:id/clips_tab",
            "com.instagram.android:id/reels_tray_container"
        )

        // Instagram Reels content descriptions
        private val INSTAGRAM_REELS_DESCRIPTIONS = listOf(
            "Reels", "रील्स", "reels_tab"
        )

        // Instagram Explore indicators
        private val INSTAGRAM_EXPLORE_IDS = listOf(
            "com.instagram.android:id/explore_grid",
            "com.instagram.android:id/explore_tab"
        )

        // Instagram Stories indicators
        private val INSTAGRAM_STORIES_IDS = listOf(
            "com.instagram.android:id/reel_viewer_root",
            "com.instagram.android:id/reel_viewer_image_view",
            "com.instagram.android:id/reel_viewer_video_view"
        )

        // Facebook Reels/Watch indicators
        private val FACEBOOK_REELS_IDS = listOf(
            "com.facebook.katana:id/video_player_surface",
            "com.facebook.katana:id/reels_viewer_fragment",
            "com.facebook.katana:id/watch_tab"
        )

        // Facebook Stories indicators
        private val FACEBOOK_STORIES_IDS = listOf(
            "com.facebook.katana:id/story_viewer_root",
            "com.facebook.katana:id/viewer_container"
        )

        // Snapchat Spotlight/Stories indicators
        private val SNAPCHAT_IDS = listOf(
            "com.snapchat.android:id/spotlight_feed",
            "com.snapchat.android:id/spotlight_content",
            "com.snapchat.android:id/stories_content"
        )

        // Cooldown to prevent overlay spam
        private const val OVERLAY_COOLDOWN_MS = 3000L

        var isServiceRunning = false
            private set
    }

    private var overlayManager: OverlayManager? = null
    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var database: AppDatabase? = null
    private var lastOverlayTimestamp = 0L
    private var currentBlockedPackage: String? = null

    override fun onServiceConnected() {
        super.onServiceConnected()
        isServiceRunning = true

        // Configure service
        serviceInfo = serviceInfo?.apply {
            eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or
                    AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                    AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
            notificationTimeout = 200L
        }

        overlayManager = OverlayManager(this)
        database = AppDatabase.buildDatabase(this)

        Log.d(TAG, "Student Station Accessibility Service connected")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return

        val packageName = event.packageName?.toString() ?: return

        // Only process target apps
        when (packageName) {
            PKG_YOUTUBE -> handleYouTubeEvent(event)
            PKG_INSTAGRAM -> handleInstagramEvent(event)
            PKG_FACEBOOK, PKG_FB_LITE -> handleFacebookEvent(event)
            PKG_SNAPCHAT -> handleFullAppOrFeature(event, packageName)
            PKG_TWITTER -> handleFullAppOrFeature(event, packageName)
            PKG_THREADS -> handleFullAppOrFeature(event, packageName)
        }
    }

    /**
     * Full app blocking — पूरा ऐप ब्लॉक करें (Snapchat, Twitter, Threads, etc.)
     */
    private fun handleFullAppOrFeature(event: AccessibilityEvent, pkg: String) {
        serviceScope.launch {
            val config = database?.appConfigDao()?.getConfigByPackage(pkg)
            if (config == null || !config.isBlocked) return@launch

            // For Snapchat, try to detect Spotlight specifically
            if (pkg == PKG_SNAPCHAT && !config.blockShorts) {
                val rootNode = try { rootInActiveWindow } catch (_: Exception) { null }
                if (rootNode != null) {
                    val isSpotlight = SNAPCHAT_IDS.any { id ->
                        val nodes = rootNode.findAccessibilityNodeInfosByViewId(id)
                        val found = !nodes.isNullOrEmpty()
                        nodes?.forEach { it.recycle() }
                        found
                    }
                    rootNode.recycle()
                    if (!isSpotlight) return@launch
                }
            }

            // Block the entire app
            showBlockingOverlay(pkg, "app", config.waitTimeSeconds, config.timerStrategy)
            logUsageAttempt(pkg, "app")
        }
    }

    /**
     * YouTube शॉर्ट्स पहचान — Multi-indicator strategy
     */
    private fun handleYouTubeEvent(event: AccessibilityEvent) {
        serviceScope.launch {
            val config = database?.appConfigDao()?.getConfigByPackage(PKG_YOUTUBE)
            if (config == null || !config.isBlocked) return@launch

            // Check if Shorts is playing
            val rootNode = try { rootInActiveWindow } catch (e: Exception) { null }
            if (rootNode == null) return@launch

            val isShortsView = if (config.blockShorts) {
                detectYouTubeShorts(rootNode)
            } else false

            if (isShortsView) {
                // YouTube Shorts: सीधे Home पर भेजो (overlay नहीं)
                // ताकि user YouTube दोबारा खोलकर normal videos देख सके
                redirectToHomeWithToast(PKG_YOUTUBE, "shorts")
                logUsageAttempt(PKG_YOUTUBE, "shorts")
            }

            rootNode.recycle()
        }
    }

    /**
     * Instagram रील्स और एक्सप्लोर/स्टोरीज़ पहचान
     */
    private fun handleInstagramEvent(event: AccessibilityEvent) {
        serviceScope.launch {
            val config = database?.appConfigDao()?.getConfigByPackage(PKG_INSTAGRAM)
            if (config == null || !config.isBlocked) return@launch

            val rootNode = try { rootInActiveWindow } catch (e: Exception) { null }
            if (rootNode == null) return@launch

            val isReelsView = if (config.blockReels) detectInstagramReels(rootNode) else false
            val isExploreView = if (config.blockReels) detectInstagramExplore(rootNode) else false
            val isStoryView = if (config.blockReels) detectInstagramStories(rootNode) else false

            // If entire app is blocked (reusing blockShorts flag)
            val isFullAppBlocked = config.blockShorts

            val shouldBlock = isFullAppBlocked || isReelsView || isExploreView || isStoryView
            
            val featureName = when {
                isFullAppBlocked -> "app"
                isReelsView -> "reels"
                isExploreView -> "explore"
                isStoryView -> "story"
                else -> ""
            }

            if (shouldBlock && featureName.isNotEmpty()) {
                showBlockingOverlay(PKG_INSTAGRAM, featureName, config.waitTimeSeconds, config.timerStrategy)
                logUsageAttempt(PKG_INSTAGRAM, featureName)
            }

            rootNode.recycle()
        }
    }

    /**
     * Facebook रील्स/वॉच और स्टोरीज़ पहचान
     */
    private fun handleFacebookEvent(event: AccessibilityEvent) {
        serviceScope.launch {
            val pkg = event.packageName?.toString() ?: return@launch
            val config = database?.appConfigDao()?.getConfigByPackage(pkg)
                ?: database?.appConfigDao()?.getConfigByPackage(PKG_FACEBOOK)
            if (config == null || !config.isBlocked) return@launch

            val rootNode = try { rootInActiveWindow } catch (e: Exception) { null }
            if (rootNode == null) return@launch

            val isReelsView = if (config.blockReels) detectFacebookReels(rootNode) else false
            val isStoryView = if (config.blockReels) detectFacebookStories(rootNode) else false
            
            // If entire app is blocked (reusing blockShorts flag)
            val isFullAppBlocked = config.blockShorts

            val shouldBlock = isFullAppBlocked || isReelsView || isStoryView
            
            val featureName = when {
                isFullAppBlocked -> "app"
                isReelsView -> "reels"
                isStoryView -> "story"
                else -> ""
            }

            if (shouldBlock && featureName.isNotEmpty()) {
                showBlockingOverlay(pkg, featureName, config.waitTimeSeconds, config.timerStrategy)
                logUsageAttempt(pkg, featureName)
            }

            rootNode.recycle()
        }
    }

    // ==================== DETECTION ALGORITHMS ====================

    /**
     * YouTube Shorts detection — checks multiple view IDs
     */
    private fun detectYouTubeShorts(rootNode: AccessibilityNodeInfo): Boolean {
        for (viewId in YOUTUBE_SHORTS_IDS) {
            val nodes = rootNode.findAccessibilityNodeInfosByViewId(viewId)
            if (!nodes.isNullOrEmpty()) {
                nodes.forEach { it.recycle() }
                Log.d(TAG, "YouTube Shorts detected via: $viewId")
                return true
            }
        }

        // Fallback: Check content description for "Shorts" text
        val allNodes = mutableListOf<AccessibilityNodeInfo>()
        findNodesByText(rootNode, "Shorts", allNodes)
        val found = allNodes.any { node ->
            node.className?.toString()?.contains("Tab") == true ||
            node.viewIdResourceName?.contains("pivot_bar") == true
        }
        allNodes.forEach { it.recycle() }

        return found
    }

    /**
     * Instagram Reels detection
     */
    private fun detectInstagramReels(rootNode: AccessibilityNodeInfo): Boolean {
        // Check view IDs
        for (viewId in INSTAGRAM_REELS_IDS) {
            val nodes = rootNode.findAccessibilityNodeInfosByViewId(viewId)
            if (!nodes.isNullOrEmpty()) {
                nodes.forEach { it.recycle() }
                Log.d(TAG, "Instagram Reels detected via: $viewId")
                return true
            }
        }

        // Fallback: Check content descriptions
        for (desc in INSTAGRAM_REELS_DESCRIPTIONS) {
            val nodes = rootNode.findAccessibilityNodeInfosByText(desc)
            if (!nodes.isNullOrEmpty()) {
                val isReelsTab = nodes.any { node ->
                    node.isSelected || node.className?.toString()?.contains("Tab") == true
                }
                nodes.forEach { it.recycle() }
                if (isReelsTab) {
                    Log.d(TAG, "Instagram Reels detected via text: $desc")
                    return true
                }
            }
        }

        return false
    }

    /**
     * Instagram Explore detection
     */
    private fun detectInstagramExplore(rootNode: AccessibilityNodeInfo): Boolean {
        for (viewId in INSTAGRAM_EXPLORE_IDS) {
            val nodes = rootNode.findAccessibilityNodeInfosByViewId(viewId)
            if (!nodes.isNullOrEmpty()) {
                nodes.forEach { it.recycle() }
                Log.d(TAG, "Instagram Explore detected via: $viewId")
                return true
            }
        }
        return false
    }

    /**
     * Instagram Stories detection
     */
    private fun detectInstagramStories(rootNode: AccessibilityNodeInfo): Boolean {
        for (viewId in INSTAGRAM_STORIES_IDS) {
            val nodes = rootNode.findAccessibilityNodeInfosByViewId(viewId)
            if (!nodes.isNullOrEmpty()) {
                nodes.forEach { it.recycle() }
                Log.d(TAG, "Instagram Story detected via: $viewId")
                return true
            }
        }
        return false
    }

    /**
     * Facebook Reels detection
     */
    private fun detectFacebookReels(rootNode: AccessibilityNodeInfo): Boolean {
        for (viewId in FACEBOOK_REELS_IDS) {
            val nodes = rootNode.findAccessibilityNodeInfosByViewId(viewId)
            if (!nodes.isNullOrEmpty()) {
                nodes.forEach { it.recycle() }
                Log.d(TAG, "Facebook Reels detected via: $viewId")
                return true
            }
        }

        // Check for "Reels" or "Watch" text in tabs
        val reelsNodes = rootNode.findAccessibilityNodeInfosByText("Reels")
        val watchNodes = rootNode.findAccessibilityNodeInfosByText("Watch")
        val found = listOf(reelsNodes, watchNodes).any { nodes ->
            nodes?.any { it.isSelected } == true
        }
        reelsNodes?.forEach { it.recycle() }
        watchNodes?.forEach { it.recycle() }

        return found
    }

    /**
     * Facebook Stories detection
     */
    private fun detectFacebookStories(rootNode: AccessibilityNodeInfo): Boolean {
        for (viewId in FACEBOOK_STORIES_IDS) {
            val nodes = rootNode.findAccessibilityNodeInfosByViewId(viewId)
            if (!nodes.isNullOrEmpty()) {
                nodes.forEach { it.recycle() }
                Log.d(TAG, "Facebook Story detected via: $viewId")
                return true
            }
        }
        return false
    }

    /**
     * Helper: Find nodes containing specific text
     */
    private fun findNodesByText(
        node: AccessibilityNodeInfo,
        text: String,
        results: MutableList<AccessibilityNodeInfo>
    ) {
        if (node.text?.toString()?.contains(text, ignoreCase = true) == true ||
            node.contentDescription?.toString()?.contains(text, ignoreCase = true) == true) {
            results.add(AccessibilityNodeInfo.obtain(node))
        }
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            findNodesByText(child, text, results)
            child.recycle()
        }
    }

    // ==================== OVERLAY & LOGGING ====================

    /**
     * ब्लॉकिंग ओवरले दिखाएं — with cooldown to prevent spam
     */
    private fun showBlockingOverlay(
        packageName: String,
        feature: String,
        waitTimeSeconds: Int,
        timerStrategy: String
    ) {
        val now = SystemClock.elapsedRealtime()
        if (now - lastOverlayTimestamp < OVERLAY_COOLDOWN_MS) return
        if (currentBlockedPackage == packageName && overlayManager?.isShowing() == true) return

        lastOverlayTimestamp = now
        currentBlockedPackage = packageName

        MainScope().launch {
            overlayManager?.showMindfulPause(
                packageName = packageName,
                feature = feature,
                waitTimeSeconds = waitTimeSeconds,
                timerStrategy = timerStrategy,
                onWaitCompleted = {
                    currentBlockedPackage = null
                    serviceScope.launch {
                        logUsageAction(packageName, feature, "WAITED", true, waitTimeSeconds)
                    }
                },
                onDismissed = {
                    currentBlockedPackage = null
                    // Navigate user back to home
                    performGlobalAction(GLOBAL_ACTION_HOME)
                    serviceScope.launch {
                        logUsageAction(packageName, feature, "CLOSED", false, 0)
                        database?.streakDao()?.incrementBlocksResisted()
                    }
                }
            )
        }
    }

    /**
     * YouTube Shorts के लिए — सीधे Home पर भेजो + Toast दिखाओ
     * ताकि user YouTube दोबारा खोलकर normal videos देख सके
     */
    private fun redirectToHomeWithToast(packageName: String, feature: String) {
        val now = SystemClock.elapsedRealtime()
        if (now - lastOverlayTimestamp < OVERLAY_COOLDOWN_MS) return
        lastOverlayTimestamp = now

        // सीधे Home पर भेजो
        performGlobalAction(GLOBAL_ACTION_HOME)

        // Toast दिखाओ
        Handler(Looper.getMainLooper()).post {
            Toast.makeText(
                this,
                "🎯 Shorts ब्लॉक! YouTube खोलकर normal videos देखो",
                Toast.LENGTH_LONG
            ).show()
        }

        // Stats update
        serviceScope.launch {
            logUsageAction(packageName, feature, "REDIRECTED", false, 0)
            database?.streakDao()?.incrementBlocksResisted()
        }
    }

    private suspend fun logUsageAttempt(packageName: String, feature: String) {
        database?.usageLogDao()?.insertLog(
            UsageLogEntity(
                timestamp = System.currentTimeMillis(),
                appPackage = packageName,
                feature = feature,
                actionTaken = "BLOCKED"
            )
        )
    }

    private suspend fun logUsageAction(
        packageName: String, feature: String,
        action: String, waitCompleted: Boolean, waitDuration: Int
    ) {
        database?.usageLogDao()?.insertLog(
            UsageLogEntity(
                timestamp = System.currentTimeMillis(),
                appPackage = packageName,
                feature = feature,
                actionTaken = action,
                waitCompleted = waitCompleted,
                waitDurationSeconds = waitDuration
            )
        )
    }

    override fun onInterrupt() {
        Log.d(TAG, "Accessibility service interrupted")
    }

    override fun onDestroy() {
        super.onDestroy()
        isServiceRunning = false
        overlayManager?.dismiss()
        serviceScope.cancel()
        Log.d(TAG, "Accessibility service destroyed")
    }
}
