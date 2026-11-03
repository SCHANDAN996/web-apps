package com.studystation.app

import java.net.URI

/** Pure validation, also used before every asynchronous credential result is released. */
object GoogleAuthPolicy {
    fun validNonce(nonce: String) = Regex("[A-Za-z0-9_-]{32,128}").matches(nonce)
    fun allowed(origin: String, page: String?, base: String, top: Boolean): Boolean = runCatching {
        val trusted = URI(base)
        fun matches(value: String?): Boolean {
            if (value == null) return false
            val candidate = URI(value)
            return trusted.scheme == "https" && trusted.host != null && candidate.scheme == trusted.scheme &&
                candidate.host == trusted.host && candidate.port == trusted.port && candidate.userInfo == null
        }
        top && matches(origin) && matches(page)
    }.getOrDefault(false)
}
