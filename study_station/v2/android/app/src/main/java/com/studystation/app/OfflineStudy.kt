package com.studystation.app

import java.net.URI

/** Strict, Android-independent route policy for the public study pack bundled in the APK. */
object OfflineStudy {
    fun asset(method: String, url: String, base: String, language: String = "hi"): String? {
        if (!method.equals("GET", true) || !Links.isInApp(url, base)) return null
        val uri = try { URI(url) } catch (_: Exception) { return null }
        val path = uri.rawPath ?: return null
        if (path == "/offline-study" || path == "/offline-study/") {
            val requested = uri.rawQuery?.split('&')?.firstOrNull { it.startsWith("lang=") }?.substring(5)
            val lang = if ((requested ?: language) == "en") "en" else "hi"
            return "offline/$lang.html"
        }
        if (!path.startsWith("/offline-content/")) return null
        val name = path.removePrefix("/offline-content/")
        if (!name.matches(Regex("[A-Za-z0-9_./-]+")) ||
            name.split('/').any { it.isEmpty() || it == "." || it == ".." }) return null
        if (mime(name) == null) return null
        return "study/$name"
    }

    fun mime(name: String): String? = when (name.substringAfterLast('.').lowercase()) {
        "html" -> "text/html"
        "txt", "md" -> "text/plain"
        else -> Links.mime(name)
    }
}
