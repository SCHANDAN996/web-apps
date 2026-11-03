package com.studystation.app

import org.junit.Assert.*
import org.junit.Test

class PlayBillingPolicyTest {
    @Test fun onlyApprovedPrepaidPairsAndOpaqueAccountAreAccepted() {
        assertTrue(PlayBillingPolicy.allowed("monthly","study_station_monthly","monthly-prepaid"))
        assertFalse(PlayBillingPolicy.allowed("monthly","study_station_yearly","yearly-prepaid"))
        assertFalse(PlayBillingPolicy.allowed("monthly","study_station_monthly","monthly-auto"))
        assertTrue(PlayBillingPolicy.validAccount("a".repeat(64)))
        assertFalse(PlayBillingPolicy.validAccount("person@example.com"))
        assertFalse(PlayBillingPolicy.validAccount("a".repeat(65)))
    }
    @Test fun neverFallBackToRecurringTrialOfferOrDifferentPeriod() {
        assertTrue(PlayBillingPolicy.prepaid("monthly-prepaid",null,listOf("P1M" to 3)))
        assertTrue(PlayBillingPolicy.prepaid("yearly-prepaid",null,listOf("P1Y" to 3)))
        assertFalse(PlayBillingPolicy.prepaid("monthly-prepaid",null,listOf("P1M" to 1)))
        assertFalse(PlayBillingPolicy.prepaid("monthly-prepaid","trial",listOf("P1M" to 3)))
        assertFalse(PlayBillingPolicy.prepaid("monthly-prepaid",null,listOf("P1Y" to 3)))
        assertFalse(PlayBillingPolicy.prepaid("monthly-prepaid",null,listOf("P3D" to 2,"P1M" to 1)))
    }
}
