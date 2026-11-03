package com.studystation.app

import org.junit.Assert.*
import org.junit.Test
import java.security.KeyPairGenerator
import java.security.Signature
import java.util.Base64

class MembershipPolicyTest {
    private val pair = KeyPairGenerator.getInstance("RSA").apply { initialize(2048) }.generateKeyPair()
    private val key = Base64.getEncoder().encodeToString(pair.public.encoded)
    private val ns = "a".repeat(48)
    private fun claims(issued: Long=1000, expires: Long=87400, audience: String="com.studystation.app", namespace: String=ns) = MembershipPolicy.Envelope("RS256",MembershipPolicy.Claims("StudyStation",audience,namespace,issued,expires,"test-unique-lease-id"))
    private fun token(): String {
        val encoder=Base64.getUrlEncoder().withoutPadding()
        val raw=encoder.encodeToString("header".toByteArray())+"."+encoder.encodeToString("payload".toByteArray())
        val sig=Signature.getInstance("SHA256withRSA").apply { initSign(pair.private);update(raw.toByteArray()) }.sign()
        return raw+"."+encoder.encodeToString(sig)
    }
    @Test fun signedLeaseUsesMonotonicClockAndExpiresAtTwentyFourHours() {
        val anchor=MembershipPolicy.verify(token(),key,10000,7){_,_->claims()}!!
        assertEquals(86400000L,MembershipPolicy.remaining(anchor,10000,7))
        assertEquals(0L,MembershipPolicy.remaining(anchor,86410000,7))
        assertEquals(86399000L,MembershipPolicy.remaining(anchor,11000,7))
    }
    @Test fun rebootOrElapsedResetAlwaysRequiresOnlineRenewal() {
        val a=MembershipPolicy.verify(token(),key,10000,7){_,_->claims()}!!
        assertEquals(0L,MembershipPolicy.remaining(a,11000,8));assertEquals(0L,MembershipPolicy.remaining(a,9999,7));assertEquals(0L,MembershipPolicy.remaining(a,10000,-1))
    }
    @Test fun wrongSignatureAlgorithmAudienceNamespaceAndDurationFailClosed() {
        val jwt=token()
        assertNull(MembershipPolicy.verify(jwt.dropLast(10)+"AAAAAAAAAA",key,10000,7){_,_->claims()})
        assertNull(MembershipPolicy.verify(jwt,key,10000,7){_,_->claims().copy(algorithm="none")})
        assertNull(MembershipPolicy.verify(jwt,key,10000,7){_,_->claims(audience="other.app")})
        assertNull(MembershipPolicy.verify(jwt,key,10000,7){_,_->claims(namespace="user1")})
        assertNull(MembershipPolicy.verify(jwt,key,10000,7){_,_->claims(expires=87401)})
        assertNull(MembershipPolicy.verify(jwt,key,10000,7){_,_->claims(expires=1000)})
        assertNull(MembershipPolicy.verify("a".repeat(32769),key,10000,7){_,_->claims()})
    }
    @Test fun duplicateAndSameSecondLoginCannotRestartOrCrossAccountLease() {
        val a=MembershipPolicy.Anchor(1000,2000,10000,7,ns)
        val duplicate=a.copy(elapsed=500000)
        assertEquals(a,MembershipPolicy.accept(duplicate,a,1000,500000,7,1500))
        assertNull(MembershipPolicy.accept(duplicate,a,1000,500000,8,1500))
        assertNull(MembershipPolicy.accept(duplicate.copy(namespace="b".repeat(48)),a,1000,500000,7,1500))
        assertNull(MembershipPolicy.accept(duplicate,a,1000,1010000,7,1500))
        assertNull(MembershipPolicy.accept(a,null,0,10000,7,699))
        assertNull(MembershipPolicy.accept(a,null,0,10000,7,1301))
        assertEquals(a,MembershipPolicy.accept(a,null,0,10000,7,1000))
    }
    @Test fun trustedOriginIsMainFrameAndHttpsOnly() {
        val base="https://studystation.ebookcart.in"
        assertTrue(GoogleAuthPolicy.allowed(base,"$base/offline-study",base,true))
        assertFalse(GoogleAuthPolicy.allowed(base,"$base/offline-study",base,false))
        assertFalse(GoogleAuthPolicy.allowed("https://evil.example",base,base,true))
        assertFalse(GoogleAuthPolicy.allowed("http://studystation.ebookcart.in",base,base,true))
    }
}
