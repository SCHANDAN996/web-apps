package com.studystation.app

import android.app.Activity
import android.content.MutableContextWrapper
import android.net.Uri
import android.os.CancellationSignal
import android.webkit.WebView
import androidx.credentials.ClearCredentialStateRequest
import androidx.credentials.CredentialManager
import androidx.credentials.CredentialManagerCallback
import androidx.credentials.CustomCredential
import androidx.credentials.GetCredentialRequest
import androidx.credentials.GetCredentialResponse
import androidx.credentials.exceptions.ClearCredentialException
import androidx.credentials.exceptions.GetCredentialCancellationException
import androidx.credentials.exceptions.GetCredentialException
import androidx.webkit.WebMessageCompat
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential
import org.json.JSONObject

/** Native account chooser only. Tokens are delivered once to the trusted page and never persisted. */
class GoogleAuthBridge(private val activity: Activity, private val web: WebView) {
    private val origin = Uri.parse(BuildConfig.BASE_URL).let { "${it.scheme}://${it.authority}" }
    private val manager = CredentialManager.create(activity)
    private var cancellation: CancellationSignal? = null
    private var generation = 0
    private var dead = false
    private val configured = BuildConfig.GOOGLE_WEB_CLIENT_ID.isNotEmpty() && origin.startsWith("https://")
    private val script = """
      (function(){if(window!==window.top||!window.SSGoogleAuthNative||window.StudyStationAuth)return;
      var pending=null,seq=0;
      function request(op,nonce){
        if(op==='signin'&&(!navigator.userActivation||!navigator.userActivation.isActive))return Promise.resolve({ok:false,error:'gesture_required'});
        if(pending)return Promise.resolve({ok:false,error:'busy'});
        return new Promise(function(resolve){var id=String(++seq);pending={id:id,resolve:resolve};
          window.SSGoogleAuthNative.postMessage(JSON.stringify({op:op,nonce:nonce||'',requestId:id}));
          setTimeout(function(){if(pending&&pending.id===id){pending=null;resolve({ok:false,error:'unavailable'});}},120000);
        });
      }
      window.SSGoogleAuthNative.onmessage=function(e){try{var result=JSON.parse(e.data);if(!pending||pending.id!==result.requestId)return;
        var resolve=pending.resolve;pending=null;delete result.requestId;resolve(result);
        window.dispatchEvent(new CustomEvent('ss-google-signin',{detail:result}));}catch(ignore){}};
      Object.defineProperty(window,'StudyStationAuth',{value:Object.freeze({configured:function(){return $configured;},
        signIn:function(nonce){return request('signin',nonce);},signOut:function(){return request('signout','');}}),configurable:false});
      window.dispatchEvent(new Event('ss-google-auth-ready'));})();
    """.trimIndent()

    fun install() {
        if (!WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) return
        WebViewCompat.addWebMessageListener(web, "SSGoogleAuthNative", setOf(origin)) { _, message, source, top, reply ->
            if (dead || message.type != WebMessageCompat.TYPE_STRING || !GoogleAuthPolicy.allowed(source.toString(), web.url, BuildConfig.BASE_URL, top)) return@addWebMessageListener
            val payload = runCatching {
                val raw = message.data ?: error("invalid")
                require(raw.length <= 512)
                JSONObject(raw).also { data ->
                    require(data.keys().asSequence().toSet() == setOf("op", "nonce", "requestId"))
                    require(data.get("op") is String && data.get("nonce") is String && data.get("requestId") is String)
                    require(Regex("[0-9]{1,12}").matches(data.getString("requestId")))
                }
            }.getOrNull() ?: return@addWebMessageListener
            val requestId = payload.getString("requestId")
            fun send(ok: Boolean, error: String = "", token: String? = null) {
                if (dead || !GoogleAuthPolicy.allowed(source.toString(), web.url, BuildConfig.BASE_URL, top)) return
                val result = JSONObject().put("requestId",requestId).put("ok",ok)
                if (!ok) result.put("error",error)
                if (token != null) result.put("idToken",token)
                runCatching { reply.postMessage(result.toString()) }
            }
            if (cancellation != null) { send(false,"busy"); return@addWebMessageListener }
            val signal = CancellationSignal()
            val currentGeneration = generation
            when (payload.getString("op")) {
                "signin" -> {
                    if (!configured) { send(false,"configuration"); return@addWebMessageListener }
                    val nonce = payload.getString("nonce")
                    if (!GoogleAuthPolicy.validNonce(nonce)) { send(false,"invalid_nonce"); return@addWebMessageListener }
                    // The facade checks activation synchronously; re-check it natively before opening UI.
                    cancellation = signal
                    web.evaluateJavascript("Boolean(navigator.userActivation&&navigator.userActivation.isActive)") { active ->
                        if (active != "true" || dead || currentGeneration != generation) { if(cancellation===signal) cancellation=null; if(currentGeneration==generation) send(false,"gesture_required"); return@evaluateJavascript }
                        cancellation = signal
                        val option = GetSignInWithGoogleOption.Builder(BuildConfig.GOOGLE_WEB_CLIENT_ID).setNonce(nonce).build()
                        val request = GetCredentialRequest.Builder().addCredentialOption(option).build()
                        manager.getCredentialAsync(MutableContextWrapper(activity),request,signal,java.util.concurrent.Executor { activity.runOnUiThread(it) },
                            object : CredentialManagerCallback<GetCredentialResponse,GetCredentialException> {
                                override fun onResult(result: GetCredentialResponse) {
                                    if (cancellation === signal) cancellation = null
                                    if (currentGeneration != generation) return
                                    val token = runCatching {
                                        val credential = result.credential as CustomCredential
                                        require(credential.type == GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL)
                                        GoogleIdTokenCredential.createFrom(credential.data).idToken.also { require(it.length in 32..16384) }
                                    }.getOrNull()
                                    if (token == null) send(false,"unavailable") else send(true,token=token)
                                }
                                override fun onError(e: GetCredentialException) {
                                    if (cancellation === signal) cancellation = null
                                    if (currentGeneration == generation) send(false,if(e is GetCredentialCancellationException) "cancelled" else "unavailable")
                                }
                            })
                    }
                }
                "signout" -> {
                    cancellation = signal
                    manager.clearCredentialStateAsync(ClearCredentialStateRequest(),signal,java.util.concurrent.Executor { activity.runOnUiThread(it) },
                        object : CredentialManagerCallback<Void?,ClearCredentialException> {
                            override fun onResult(result: Void?) { if(cancellation===signal) cancellation=null; if(currentGeneration==generation) send(true) }
                            override fun onError(e: ClearCredentialException) { if(cancellation===signal) cancellation=null; if(currentGeneration==generation) send(false,"unavailable") }
                        })
                }
                else -> send(false,"unavailable")
            }
        }
        if (WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT))
            WebViewCompat.addDocumentStartJavaScript(web,script,setOf(origin))
    }
    fun pageFinished() {
        if (!dead && GoogleAuthPolicy.allowed(origin,web.url,BuildConfig.BASE_URL,true) && WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER))
            web.evaluateJavascript(script,null)
    }
    fun pageStarted() { generation++; cancellation?.cancel(); cancellation=null }
    fun destroy() { dead=true; generation++; cancellation?.cancel(); cancellation=null }
}
