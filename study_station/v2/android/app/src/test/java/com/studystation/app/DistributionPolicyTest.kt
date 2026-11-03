package com.studystation.app

import org.junit.Assert.*
import org.junit.Test

class DistributionPolicyTest {
    @Test fun externalCheckoutIsOnlyEnabledForDirectDistribution() {
        val direct = BuildConfig.BUILD_TYPE in setOf("directRelease","directDebug")
        assertEquals(direct, BuildConfig.DIRECT_PAYU_ALLOWED)
        if (BuildConfig.BUILD_TYPE == "directRelease") {
            assertEquals("com.studystation.app", BuildConfig.APPLICATION_ID)
            assertFalse(BuildConfig.DEBUG)
        }
        if (BuildConfig.BUILD_TYPE == "directDebug") {
            assertEquals("com.studystation.app.debug", BuildConfig.APPLICATION_ID)
            assertTrue(BuildConfig.DEBUG)
        }
    }
}
