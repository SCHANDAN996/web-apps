package com.studystation.app

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.webkit.WebView
import androidx.webkit.WebMessageCompat
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import org.json.JSONObject

/** Origin-restricted public-question sharing. Android presents a chooser; the user chooses a recipient. */
class QuestionShareBridge(private val activity: Activity, private val web: WebView) {
    private val origin = Uri.parse(BuildConfig.BASE_URL).let { "${it.scheme}://${it.authority}" }
    private var lastShare = 0L
    private val script = """
        (function(){if(window!==window.top||!window.SSQuestionShareNative||window.SSNativeShare)return;
        var pending=null;
        window.SSQuestionShareNative.onmessage=function(e){if(!pending)return;try{var r=JSON.parse(e.data);pending(r);pending=null;}catch(ignore){}};
        Object.defineProperty(window,'SSNativeShare',{value:Object.freeze({shareQuestion:function(q){
          if(!navigator.userActivation||!navigator.userActivation.isActive)return Promise.resolve({ok:false,error:'gesture_required'});
          if(pending)return Promise.resolve({ok:false,error:'busy'});
          return new Promise(function(resolve){pending=resolve;window.SSQuestionShareNative.postMessage(JSON.stringify({id:q.id,lang:q.lang,question:q.question,options:q.options}));
          setTimeout(function(){if(pending===resolve){pending=null;resolve({ok:false,error:'unavailable'});}},5000);});
        }}),configurable:false});window.dispatchEvent(new Event('ss-native-share-ready'));})();
    """.trimIndent()
    fun install() {
        if (!WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) return
        WebViewCompat.addWebMessageListener(web, "SSQuestionShareNative", setOf(origin)) { _, message, source, top, reply ->
            if (!BackupPolicy.allowed(source.toString(), web.url, BuildConfig.BASE_URL, top) || message.type != WebMessageCompat.TYPE_STRING) return@addWebMessageListener
            var ok = false
            try {
                val data = message.data ?: error("invalid")
                require(data.length <= 30000)
                val q = JSONObject(data)
                require(q.keys().asSequence().toSet() == setOf("id", "lang", "question", "options"))
                val id = q.get("id").toString()
                require(Regex("[1-9][0-9]{0,14}").matches(id))
                require(q.get("lang") is String && q.get("question") is String)
                val target = QuestionLinks.target(id.toLong(), q.getString("lang")) ?: error("invalid")
                val options = q.getJSONArray("options")
                require(options.length() in 2..10)
                require((0 until options.length()).all { options.get(it) is String })
                val text = QuestionLinks.text(target, q.getString("question"), (0 until options.length()).map { options.getString(it) }) ?: error("invalid")
                val now = android.os.SystemClock.elapsedRealtime()
                require(now - lastShare > 800)
                lastShare = now
                val send = Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, text)
                activity.startActivity(Intent.createChooser(send, null))
                ok = true
            } catch (_: Exception) { /* Invalid payloads cannot launch an external activity. */ }
            runCatching { reply.postMessage(JSONObject().put("ok", ok).put("error", if (ok) "" else "unavailable").toString()) }
        }
        if (WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT))
            WebViewCompat.addDocumentStartJavaScript(web, script, setOf(origin))
    }
    fun pageFinished() {
        if (Links.isInApp(web.url ?: "", BuildConfig.BASE_URL) && WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER))
            web.evaluateJavascript(script, null)
    }
}
