package com.studystation.app

import org.junit.Assert.*
import org.junit.Test

class GoogleAuthPolicyTest {
    private val base = "https://studystation.ebookcart.in"
    @Test fun onlyTrustedMainFrameCanReceiveTokens() {
        assertTrue(GoogleAuthPolicy.allowed(base,"$base/classroom",base,true))
        for (bad in listOf("http://studystation.ebookcart.in", "https://evil.test", "https://studystation.ebookcart.in.evil.test", "https://user@studystation.ebookcart.in", "https://studystation.ebookcart.in:444")) {
            assertFalse(GoogleAuthPolicy.allowed(bad,"$base/classroom",base,true))
            assertFalse(GoogleAuthPolicy.allowed(base,bad,base,true))
        }
        assertFalse(GoogleAuthPolicy.allowed(base,base,base,false))
        assertFalse(GoogleAuthPolicy.allowed(base,null,base,true))
        assertFalse(GoogleAuthPolicy.allowed("http://localhost","http://localhost","http://localhost",true))
    }
    @Test fun nonceIsBoundedAndOpaque() {
        assertTrue(GoogleAuthPolicy.validNonce("Ab_9-".repeat(9)))
        for (bad in listOf("", "a".repeat(31),"a".repeat(129),"a".repeat(32)+"\n", "x y".repeat(20))) assertFalse(GoogleAuthPolicy.validNonce(bad))
    }
}
