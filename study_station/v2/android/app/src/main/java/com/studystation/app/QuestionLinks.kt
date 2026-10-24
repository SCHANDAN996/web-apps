package com.studystation.app

import java.net.URI

/** Public share protocol: never accepts solution, answer, user state or a caller-controlled URL. */
object QuestionLinks {
    const val HOST = "studystation.ebookcart.in"
    data class Target(val id: Long, val lang: String) {
        val publicUrl get() = "https://$HOST/q/$id?lang=$lang"
        fun destination(base: String, offline: Boolean) = if (offline)
            "$base/offline-study?lang=$lang#shared/$id" else publicUrl
    }
    fun parse(url: String?): Target? {
        if (url == null || url.length > 256) return null
        val u = try { URI(url) } catch (_: Exception) { return null }
        if (u.scheme != "https" || u.host != HOST || u.port !in listOf(-1, 443) ||
            u.rawUserInfo != null || u.rawFragment != null) return null
        val match = Regex("^/q/([1-9][0-9]{0,14})$").matchEntire(u.rawPath ?: "") ?: return null
        val id = match.groupValues[1].toLongOrNull() ?: return null
        val lang = when (u.rawQuery) { null, "lang=hi" -> "hi"; "lang=en" -> "en"; else -> return null }
        return Target(id, lang)
    }
    fun target(id: Long, lang: String): Target? =
        if (id in 1..999999999999999L && lang in setOf("hi", "en")) Target(id, lang) else null
    fun text(target: Target, question: String, options: List<String>): String? {
        if (question.isBlank() || question.length > 6000 || options.size !in 2..10 ||
            options.any { it.isBlank() || it.length > 2000 }) return null
        fun clean(s: String) = s.replace(Regex("[\\p{Cc}&&[^\\n\\t]]"), "").trim()
        return buildString {
            append(clean(question)); append("\n\n")
            options.forEachIndexed { i, option -> append(('A'.code + i).toChar()); append(") "); append(clean(option)); append('\n') }
            append('\n')
            append(if (target.lang == "hi") "उत्तर और समाधान Study Station ऐप में देखें।" else "See the answer and solution in the Study Station app.")
            append('\n'); append(target.publicUrl)
        }
    }
}
