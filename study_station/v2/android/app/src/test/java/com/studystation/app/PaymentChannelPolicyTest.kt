package com.studystation.app

import org.junit.Assert.*
import org.junit.Test

class PaymentChannelPolicyTest {
    private val base="https://studystation.ebookcart.in"
    @Test fun directCheckoutHasOneFixedPublicDestinationAndNoTransferredCredentials() {
        assertEquals("$base/membership",PaymentChannelPolicy.checkoutWebsite(true,true,base,"$base/offline-study?private=ignored#settings",base,true))
    }
    @Test fun playDebugUntrustedFramesAndMissingGestureCannotOpenCheckout() {
        assertNull(PaymentChannelPolicy.checkoutWebsite(false,true,base,base,base,true))
        assertNull(PaymentChannelPolicy.checkoutWebsite(true,false,base,base,base,true))
        assertNull(PaymentChannelPolicy.checkoutWebsite(true,true,base,base,base,false))
        assertNull(PaymentChannelPolicy.checkoutWebsite(true,true,"https://evil.example",base,base,true))
        assertNull(PaymentChannelPolicy.checkoutWebsite(true,true,base,"https://evil.example",base,true))
        assertNull(PaymentChannelPolicy.checkoutWebsite(true,true,"http://studystation.ebookcart.in",base,base,true))
    }
}
