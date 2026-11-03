package com.studystation.app

import java.net.URI

/** Where a URL may go. Free of Android classes so it runs in plain unit tests. */
object Links {
    private val OUTSIDE_SCHEMES = setOf("http", "https", "mailto", "tel", "whatsapp", "tg")
    private val MIME = mapOf(
        "css" to "text/css", "js" to "text/javascript", "svg" to "image/svg+xml",
        "webmanifest" to "application/manifest+json", "json" to "application/json",
        "png" to "image/png", "webp" to "image/webp", "woff2" to "font/woff2",
    )

    private fun parse(url: String): URI? = try { URI(url) } catch (e: Exception) { null }

    private fun origin(u: URI): String? {
        val scheme = u.scheme?.lowercase() ?: return null
        if (scheme != "http" && scheme != "https") return null
        val host = u.host?.lowercase() ?: return null
        val port = if (u.port != -1) u.port else if (scheme == "https") 443 else 80
        return "$scheme://$host:$port"
    }

    /** Only our own server is shown inside the app. */
    fun isInApp(url: String, base: String): Boolean {
        val o = parse(url)?.let(::origin) ?: return false
        return o == parse(base)?.let(::origin)
    }

    /** Other links (official notices, PDFs, phone, mail) are handed to the phone's own apps. */
    fun opensOutside(url: String): Boolean = parse(url)?.scheme?.lowercase() in OUTSIDE_SCHEMES

    /** Asset path inside the APK for /static/<path>?v=<assetV> on our server, else null (→ network). */
    fun bundledAsset(url: String, base: String, assetV: String): String? {
        if (assetV.isEmpty() || !isInApp(url, base)) return null
        val u = parse(url) ?: return null
        val path = u.path ?: return null
        if (!path.startsWith("/static/")) return null
        val name = path.removePrefix("/static/")
        if ('\\' in name || name.split('/').any { it.isEmpty() || it == "." || it == ".." }) return null
        val v = u.rawQuery?.split('&')?.firstOrNull { it.startsWith("v=") }?.substring(2)
        if (v != assetV || mime(name) == null) return null
        return name
    }

    fun mime(name: String): String? = MIME[name.substringAfterLast('.', "").lowercase()]

    // First path segment of every screen (same list as SCREEN in static/js/app.js).
    private val SCREENS = setOf("", "settings", "practice", "mock", "attempt", "result", "revise", "progress",
        "current-affairs", "jobs", "books")

    /** One of our screens is being opened as a page: the APK answers with its own frame, and app.js then
     *  fetches the content (those fetches carry X-SS-Nav and go to the server). */
    fun wantsFrame(method: String, url: String, headers: Map<String, String>, base: String, mainFrame: Boolean): Boolean {
        if (!method.equals("GET", ignoreCase = true) || !isInApp(url, base)) return false
        val h = headers.entries.associate { it.key.lowercase() to it.value }
        if ("x-ss-nav" in h) return false
        if (!mainFrame && h["accept"]?.contains("text/html") != true) return false
        val path = parse(url)?.path ?: return false
        return path.removePrefix("/").substringBefore('/') in SCREENS
    }

    /** Value of one cookie in a "a=1; b=2" header, or null. */
    fun cookie(header: String?, name: String): String? =
        header?.split(';')?.map { it.trim() }?.firstOrNull { it.startsWith("$name=") }?.substring(name.length + 1)
}
