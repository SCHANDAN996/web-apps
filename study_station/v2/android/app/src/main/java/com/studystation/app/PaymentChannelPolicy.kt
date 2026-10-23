package com.studystation.app

import java.net.URI

/** Presentation gate only. No account/session parameters are ever transferred to the browser. */
object PaymentChannelPolicy {
    fun checkoutWebsite(direct: Boolean, gesture: Boolean, origin: String, page: String?, base: String, top: Boolean): String? =
        if (!direct || !gesture || !GoogleAuthPolicy.allowed(origin,page,base,top)) null
        else runCatching { URI(base).let { URI("https",null,it.host,it.port,"/membership",null,null).toASCIIString() } }.getOrNull()
}
