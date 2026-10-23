package com.studystation.app

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.SystemClock
import android.provider.Settings
import android.webkit.WebView
import androidx.webkit.WebMessageCompat
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import org.json.JSONObject

/** No payment or identity secrets: only a server-signed, account-scoped daily access lease. */
class MembershipBridge(private val activity: Activity, private val web: WebView) {
    private val origin = Uri.parse(BuildConfig.BASE_URL).let { "${it.scheme}://${it.authority}" }
    private val prefs = activity.getSharedPreferences("membership_lease", Activity.MODE_PRIVATE)
    private val required = BuildConfig.MEMBERSHIP_REQUIRED
    private var generation=0
    private var dead=false
    private var payuWaiting=false
    private fun boot() = runCatching { Settings.Global.getInt(activity.contentResolver, Settings.Global.BOOT_COUNT) }.getOrDefault(-1)
    private fun anchor(): MembershipPolicy.Anchor? = if (!prefs.contains("iat")) null else MembershipPolicy.Anchor(prefs.getLong("iat",0),prefs.getLong("exp",0),prefs.getLong("elapsed",-1),prefs.getInt("boot",-1),prefs.getString("namespace","") ?: "")
    private val script = """
      (function(){if(window!==window.top||!window.SSMembershipNative||window.StudyStationMembership)return;
      var seq=0,pending={};function request(op,lease){return new Promise(function(resolve){var id=String(++seq);pending[id]=resolve;
      window.SSMembershipNative.postMessage(JSON.stringify({op:op,lease:lease||'',requestId:id}));
      setTimeout(function(){if(pending[id]){delete pending[id];resolve({ok:false});}},5000);});}
      window.SSMembershipNative.onmessage=function(e){try{var r=JSON.parse(e.data),fn=pending[r.requestId];if(fn){delete pending[r.requestId];delete r.requestId;fn(r);}}catch(ignore){}};
      Object.defineProperty(window,'StudyStationMembership',{value:Object.freeze({required:function(){return $required;},allowPayu:function(){return ${BuildConfig.DIRECT_PAYU_ALLOWED};},openPayuWebsite:function(){if(!navigator.userActivation||!navigator.userActivation.isActive)return Promise.resolve({ok:false});return request('openpayu');},status:function(){return request('status');},storeLease:function(jwt){return request('store',jwt);},clear:function(){return request('clear');}})});
      window.dispatchEvent(new Event('ss-membership-ready'));})();
    """.trimIndent()
    fun clear() { prefs.edit().putBoolean("active",false).commit() }
    fun install() {
        if (!WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) return
        WebViewCompat.addWebMessageListener(web,"SSMembershipNative",setOf(origin)) { _, message, source, top, reply ->
            if(dead || message.type != WebMessageCompat.TYPE_STRING || !GoogleAuthPolicy.allowed(source.toString(),web.url,BuildConfig.BASE_URL,top)) return@addWebMessageListener
            val data = runCatching { val raw=message.data ?: error("invalid");require(raw.length<=34000);JSONObject(raw).also { require(it.keys().asSequence().toSet()==setOf("op","lease","requestId")); require(it.get("lease") is String && it.get("op") is String);require(Regex("[0-9]{1,12}").matches(it.getString("requestId"))) } }.getOrNull() ?: return@addWebMessageListener
            val result=JSONObject().put("requestId",data.getString("requestId")).put("ok",false)
            when(data.getString("op")) {
                "openpayu" -> {
                    if(!BuildConfig.DIRECT_PAYU_ALLOWED || data.getString("lease").isNotEmpty()) {reply.postMessage(result.toString());return@addWebMessageListener}
                    val epoch=generation
                    web.evaluateJavascript("Boolean(navigator.userActivation&&navigator.userActivation.isActive)") { active ->
                        if(dead || epoch!=generation)return@evaluateJavascript
                        val destination=PaymentChannelPolicy.checkoutWebsite(BuildConfig.DIRECT_PAYU_ALLOWED,active=="true",source.toString(),web.url,BuildConfig.BASE_URL,top)
                        if(destination!=null)runCatching {
                            activity.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(destination)).addCategory(Intent.CATEGORY_BROWSABLE))
                            payuWaiting=true;result.put("ok",true)
                        }
                        if(GoogleAuthPolicy.allowed(source.toString(),web.url,BuildConfig.BASE_URL,top))runCatching {reply.postMessage(result.toString())}
                    }
                    return@addWebMessageListener
                }
                "clear" -> { /* Keep a high-water mark so an old signed token cannot restart its TTL. */
                    clear();result.put("ok",true)
                }
                "store" -> {
                    val now=SystemClock.elapsedRealtime();val count=boot()
                    val next=MembershipPolicy.verify(data.getString("lease"),BuildConfig.MEMBERSHIP_PUBLIC_KEY,now,count) { header,payload ->
                        val h=JSONObject(header);val c=JSONObject(payload)
                        require(!h.has("crit") && !h.has("jku") && !h.has("jwk"))
                        MembershipPolicy.Envelope(h.getString("alg"),MembershipPolicy.Claims(c.getString("iss"),c.getString("aud"),c.getString("namespace"),c.getLong("iat"),c.getLong("exp"),c.getString("jti")))
                    }
                    val nowAnchor=MembershipPolicy.accept(next,anchor(),prefs.getLong("highest_iat",0),now,count,System.currentTimeMillis()/1000)
                    if(nowAnchor==null) { reply.postMessage(result.toString());return@addWebMessageListener }
                    prefs.edit().putLong("iat",nowAnchor.issued).putLong("exp",nowAnchor.expires).putLong("elapsed",nowAnchor.elapsed).putInt("boot",nowAnchor.boot).putString("namespace",nowAnchor.namespace).putLong("highest_iat",nowAnchor.issued).putBoolean("active",true).commit()
                }
            }
            val current=anchor();val remaining=if(current==null || !prefs.getBoolean("active",false))0 else MembershipPolicy.remaining(current,SystemClock.elapsedRealtime(),boot())
            if(data.getString("op")!="clear") { result.put("ok",remaining>0);if(remaining>0)result.put("namespace",current!!.namespace).put("expiresIn",remaining/1000.0) }
            reply.postMessage(result.toString())
        }
        if(WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT)) WebViewCompat.addDocumentStartJavaScript(web,script,setOf(origin))
    }
    fun pageStarted() { generation++ }
    fun resumed() {
        if(dead || !payuWaiting || !BuildConfig.DIRECT_PAYU_ALLOWED)return
        payuWaiting=false
        if(GoogleAuthPolicy.allowed(origin,web.url,BuildConfig.BASE_URL,true))
            web.evaluateJavascript("window.dispatchEvent(new Event('ss-payu-return'));",null)
    }
    fun destroy() { dead=true;generation++;payuWaiting=false }
    fun pageFinished() { if(!dead && GoogleAuthPolicy.allowed(origin,web.url,BuildConfig.BASE_URL,true)&&WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER))web.evaluateJavascript(script,null) }
}
