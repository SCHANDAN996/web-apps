package com.studystation.app

import org.junit.Assert.*
import org.junit.Test

class PlayUserChoicePolicyTest {
    private val product="study_station_monthly"
    private val rows=listOf(Triple(product,"subs","sdk-offer"))
    @Test fun oldClientPageOrAccountCannotOwnTheNextFlow() {
        val account="a".repeat(64)
        assertTrue(PlayUserChoicePolicy.sameFlow(7,7,2,2,account,account))
        assertFalse(PlayUserChoicePolicy.sameFlow(6,7,2,2,account,account))
        assertFalse(PlayUserChoicePolicy.sameFlow(7,7,1,2,account,account))
        assertFalse(PlayUserChoicePolicy.sameFlow(7,7,2,2,account,"b".repeat(64)))
        assertFalse(PlayUserChoicePolicy.sameFlow(7,7,2,2,"",""))
    }
    @Test fun countryComesFromPlayAndIndiaEnrollmentIsExplicit() {
        assertTrue(PlayUserChoicePolicy.eligible(true,"IN"))
        for(country in listOf("","in","US","DE","IN "))assertFalse(PlayUserChoicePolicy.eligible(true,country))
        assertFalse(PlayUserChoicePolicy.eligible(false,"IN"))
    }
    @Test fun callbackMustMatchExactLaunchedProductTypeAndOffer() {
        fun valid(products:List<Triple<String,String,String>>) = PlayUserChoicePolicy.callbackAllowed(true,"IN","t".repeat(64),products,product,"sdk-offer")
        assertTrue(valid(rows))
        assertFalse(valid(emptyList()))
        assertFalse(valid(rows+rows))
        assertFalse(valid(listOf(Triple("study_station_yearly","subs","sdk-offer"))))
        assertFalse(valid(listOf(Triple(product,"inapp","sdk-offer"))))
        assertFalse(valid(listOf(Triple(product,"subs","other-offer"))))
        assertFalse(valid(listOf(Triple(product,"subs",""))))
    }
    @Test fun malformedTokensAndUnenrolledCallbacksAreRejected() {
        for(token in listOf("", "x".repeat(15),"x".repeat(16385),"x".repeat(20)+"\n"))
            assertFalse(PlayUserChoicePolicy.callbackAllowed(true,"IN",token,rows,product,"sdk-offer"))
        assertFalse(PlayUserChoicePolicy.callbackAllowed(false,"IN","t".repeat(64),rows,product,"sdk-offer"))
        assertFalse(PlayUserChoicePolicy.callbackAllowed(true,"US","t".repeat(64),rows,product,"sdk-offer"))
    }
}
