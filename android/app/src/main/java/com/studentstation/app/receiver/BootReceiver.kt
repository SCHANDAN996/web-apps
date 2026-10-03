package com.studentstation.app.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/**
 * Boot Receiver — डिवाइस रीस्टार्ट के बाद सर्विस ऑटो-स्टार्ट
 */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED ||
            intent.action == Intent.ACTION_MY_PACKAGE_REPLACED) {
            Log.d("BootReceiver", "Device booted / App updated — Service will be started by AccessibilityService auto-connect")
            // AccessibilityService automatically reconnects after boot if enabled
            // No manual start needed
        }
    }
}
