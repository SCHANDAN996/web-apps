package com.studystation.app

import org.junit.Assert.*
import org.junit.Test

class BackupPolicyTest {
    private val base = "https://studystation.ebookcart.in"
    @Test fun trustedMainDocumentOnly() {
        assertTrue(BackupPolicy.allowed(base, "$base/settings", base, true))
        assertFalse(BackupPolicy.allowed(base, "$base/settings", base, false))
        assertFalse(BackupPolicy.allowed("https://evil.example", "$base/settings", base, true))
        assertFalse(BackupPolicy.allowed(base, "https://evil.example", base, true))
        assertFalse(BackupPolicy.allowed(base, null, base, true))
        assertFalse(BackupPolicy.allowed("http://studystation.ebookcart.in", base, base, true))
        assertFalse(BackupPolicy.allowed("$base:444", base, base, true))
        assertFalse(BackupPolicy.allowed("https://studystation.ebookcart.in.evil.example", base, base, true))
    }
    @Test fun boundedPayload() {
        assertFalse(BackupPolicy.allowedSize(0))
        assertTrue(BackupPolicy.allowedSize(BackupPolicy.MAX_BYTES))
        assertFalse(BackupPolicy.allowedSize(BackupPolicy.MAX_BYTES + 1))
        assertFalse(BackupPolicy.allowedSize(-1))
    }
}
