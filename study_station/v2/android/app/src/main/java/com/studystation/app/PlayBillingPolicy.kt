package com.studystation.app

/** Deliberately only these prepaid base plans; no fallback to an auto-renewing offer. */
object PlayBillingPolicy {
    data class Plan(val id: String, val product: String, val base: String)
    val plans = listOf(Plan("monthly","study_station_monthly","monthly-prepaid"),Plan("yearly","study_station_yearly","yearly-prepaid"))
    fun validAccount(value: String) = Regex("[a-f0-9]{64}").matches(value)
    fun allowed(id: String, product: String, base: String) = plans.any { it.id==id && it.product==product && it.base==base }
    fun prepaid(base: String, offer: String?, periods: List<Pair<String,Int>>) =
        plans.any { it.base==base } && offer==null && periods.size==1 && periods[0].second==3 &&
            periods[0].first==if(base=="monthly-prepaid") "P1M" else "P1Y"
}
