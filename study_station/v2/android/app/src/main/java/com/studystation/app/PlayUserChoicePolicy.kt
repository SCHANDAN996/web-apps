package com.studystation.app

/** India is the only enrolled market; a callback is a checkout intent, never an entitlement. */
object PlayUserChoicePolicy {
    fun eligible(configured:Boolean, country:String) = configured && country=="IN"

    fun sameFlow(clientEpoch:Int,currentClient:Int,pageEpoch:Int,currentPage:Int,account:String,currentAccount:String) =
        clientEpoch==currentClient && pageEpoch==currentPage && account==currentAccount &&
            PlayBillingPolicy.validAccount(account)

    fun callbackAllowed(configured:Boolean, country:String, token:String,
                        products:List<Triple<String,String,String>>, product:String, offer:String):Boolean =
        eligible(configured,country) && token.length in 16..16384 &&
            token.none { it.isISOControl() } && offer.isNotEmpty() &&
            products==listOf(Triple(product,"subs",offer)) &&
            PlayBillingPolicy.plans.any { it.product==product }
}
