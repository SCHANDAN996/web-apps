package com.studystation.app

import java.security.KeyFactory
import java.security.Signature
import java.security.spec.X509EncodedKeySpec
import java.util.Base64

/** Cryptographic and monotonic-time checks; device wall time never extends a lease. */
object MembershipPolicy {
    data class Claims(val issuer: String, val audience: String, val namespace: String, val issued: Long, val expires: Long, val id: String)
    data class Envelope(val algorithm: String, val claims: Claims)
    data class Anchor(val issued: Long, val expires: Long, val elapsed: Long, val boot: Int, val namespace: String)
    fun verify(token: String, publicKey: String, elapsed: Long, boot: Int, decode: (String, String) -> Envelope): Anchor? = runCatching {
        require(token.length in 64..32768 && boot >= 0 && elapsed >= 0)
        val parts = token.split('.')
        require(parts.size == 3 && parts.all { Regex("[A-Za-z0-9_-]+").matches(it) })
        val decoder = Base64.getUrlDecoder()
        val envelope = decode(String(decoder.decode(parts[0]), Charsets.UTF_8), String(decoder.decode(parts[1]), Charsets.UTF_8))
        require(envelope.algorithm == "RS256")
        val key = KeyFactory.getInstance("RSA").generatePublic(X509EncodedKeySpec(Base64.getDecoder().decode(publicKey)))
        require((key as java.security.interfaces.RSAPublicKey).modulus.bitLength() >= 2048)
        require(Signature.getInstance("SHA256withRSA").run { initVerify(key); update((parts[0]+"."+parts[1]).toByteArray(Charsets.US_ASCII)); verify(decoder.decode(parts[2])) })
        val c = envelope.claims
        require(c.issuer == "StudyStation" && c.audience == "com.studystation.app")
        require(Regex("[a-f0-9]{48}").matches(c.namespace) && c.id.length in 16..128)
        require(c.issued > 0 && c.expires > c.issued && c.expires - c.issued <= 86400)
        Anchor(c.issued, c.expires, elapsed, boot, c.namespace)
    }.getOrNull()
    fun accept(next: Anchor?, previous: Anchor?, highestIssued: Long, elapsed: Long, boot: Int, wallSeconds: Long): Anchor? {
        if (next == null) return null
        if (next.issued > highestIssued && wallSeconds >= next.issued - 300 && wallSeconds <= next.issued + 300) return next
        // Re-login within the same second can reuse the original anchor, never restart it.
        if (previous != null && next.issued == previous.issued && next.namespace == previous.namespace && remaining(previous, elapsed, boot) > 0) return previous
        return null
    }
    fun remaining(anchor: Anchor, elapsed: Long, boot: Int): Long {
        if (boot < 0 || boot != anchor.boot || elapsed < anchor.elapsed) return 0
        return ((anchor.expires-anchor.issued)*1000 - (elapsed-anchor.elapsed)).coerceAtLeast(0)
    }
}
