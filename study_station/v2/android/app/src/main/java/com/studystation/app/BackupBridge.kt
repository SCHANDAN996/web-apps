package com.studystation.app

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.webkit.WebView
import androidx.webkit.JavaScriptReplyProxy
import androidx.webkit.WebMessageCompat
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import com.google.android.gms.auth.api.identity.AuthorizationRequest
import com.google.android.gms.auth.api.identity.AuthorizationResult
import com.google.android.gms.auth.api.identity.Identity
import com.google.android.gms.common.api.Scope
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

/** Tokens never cross the WebView boundary. Only the current trusted main document can request work. */
class BackupBridge(private val activity: Activity, private val web: WebView) {
    private data class Pending(val operation: String, val json: String?, val reply: JavaScriptReplyProxy, val generation: Int, val pageUrl: String?)
    private val worker = Executors.newSingleThreadExecutor()
    private var generation = 0
    private var pending: Pending? = null
    // Activity results must stay attached to the original request, even if navigation intervenes.
    private var externalRequest: Pending? = null
    private val auth by lazy { Identity.getAuthorizationClient(activity) }
    private val origin = Uri.parse(BuildConfig.BASE_URL).let { "${it.scheme}://${it.authority}" }
    private val script = """
        (function(){if(window!==window.top||!window.SSBackupNative)return;
        var send=function(operation,data){window.SSBackupNative.postMessage(JSON.stringify({operation:operation,data:data}));};
        window.SSBackupNative.onmessage=function(e){try{var result=JSON.parse(e.data);window.dispatchEvent(new CustomEvent('ss-drive-result',{detail:result}));}catch(ignore){}};
        Object.defineProperty(window,'StudyStationNative',{value:Object.freeze({
        driveConfigured:function(){return ${BuildConfig.GOOGLE_DRIVE_ENABLED};},
        requestDriveBackup:function(data){send('backup',data);},requestDriveRestore:function(){send('restore');},
        requestLocalBackup:function(data){send('local-backup',data);},requestLocalRestore:function(){send('local-restore');}
        }),configurable:true});window.dispatchEvent(new Event('ss-native-ready'));})();
    """.trimIndent()

    fun install() {
        if (!WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) return
        WebViewCompat.addWebMessageListener(web, "SSBackupNative", setOf(origin)) { _, message, source, top, reply ->
            if (!BackupPolicy.allowed(source.toString(), web.url, BuildConfig.BASE_URL, top)) return@addWebMessageListener
            if (message.type != WebMessageCompat.TYPE_STRING) return@addWebMessageListener
            val text = message.data ?: return@addWebMessageListener
            // JSON string encoding can expand payloads, so cap the envelope separately before parsing.
            if (text.length > BackupPolicy.MAX_BYTES * 2 + 256) return@addWebMessageListener
            var started: Pending? = null
            try {
                val request = JSONObject(text)
                val operation = request.getString("operation")
                if (operation !in BackupPolicy.OPERATIONS) return@addWebMessageListener
                val p = Pending(operation, request.optString("data").takeIf { request.has("data") }, reply, generation, web.url)
                if (pending != null || externalRequest != null) { emit(p, false, "busy"); return@addWebMessageListener }
                if (operation.endsWith("backup")) validate(p.json ?: error("invalid_backup"))
                pending = p
                started = p
                if (operation.startsWith("local-")) openDocument(p) else authorize(p)
            } catch (_: Exception) {
                runCatching { reply.postMessage(JSONObject().put("operation", runCatching { JSONObject(text).getString("operation") }.getOrDefault("backup"))
                    .put("ok", false).put("error", "invalid_backup").toString()) }
                if (started != null && pending === started) pending = null
            }
        }
        if (WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT)) {
            WebViewCompat.addDocumentStartJavaScript(web, script, setOf(origin))
        }
    }

    fun pageStarted() { generation++; pending = null }
    fun navigationChanged(url: String?) {
        if (pending?.pageUrl != null && pending?.pageUrl != url) { generation++; pending = null }
    }
    fun pageFinished() {
        if (Links.isInApp(web.url ?: "", BuildConfig.BASE_URL) && WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER))
            web.evaluateJavascript(script, null)
    }

    private fun openDocument(p: Pending) {
        val save = p.operation == "local-backup"
        val intent = Intent(if (save) Intent.ACTION_CREATE_DOCUMENT else Intent.ACTION_OPEN_DOCUMENT)
            .addCategory(Intent.CATEGORY_OPENABLE).setType("application/json")
        if (save) intent.putExtra(Intent.EXTRA_TITLE, BackupPolicy.FILE_NAME)
        try { externalRequest = p; activity.startActivityForResult(intent, DOCUMENT_REQUEST) }
        catch (_: Exception) { externalRequest = null; complete(p, false, "unavailable") }
    }

    private fun authorize(p: Pending) {
        if (!BuildConfig.GOOGLE_DRIVE_ENABLED) { complete(p, false, "not_configured"); return }
        val request = AuthorizationRequest.builder().setRequestedScopes(listOf(Scope(SCOPE))).build()
        auth.authorize(request).addOnSuccessListener { result ->
            if (!current(p)) return@addOnSuccessListener
            if (result.hasResolution()) {
                try { externalRequest = p; activity.startIntentSenderForResult(result.pendingIntent!!.intentSender, AUTH_REQUEST, null, 0, 0, 0) }
                catch (_: Exception) { externalRequest = null; complete(p, false, "authorization_failed") }
            } else transfer(p, result)
        }.addOnFailureListener { complete(p, false, "authorization_failed") }
    }

    fun activityResult(request: Int, result: Int, data: Intent?): Boolean {
        if (request != AUTH_REQUEST && request != DOCUMENT_REQUEST) return false
        val p = externalRequest ?: return true
        externalRequest = null
        if (!current(p)) return true
        if (result != Activity.RESULT_OK) { complete(p, false, "cancelled"); return true }
        if (request == AUTH_REQUEST) {
            try { transfer(p, auth.getAuthorizationResultFromIntent(data)) }
            catch (_: Exception) { complete(p, false, "authorization_failed") }
        } else {
            val uri = data?.data
            if (uri == null || uri.scheme != "content") { complete(p, false, "invalid_backup"); return true }
            worker.execute {
                try {
                    if (p.operation == "local-backup") {
                        activity.contentResolver.openOutputStream(uri, "wt")?.use { it.write(p.json!!.toByteArray(Charsets.UTF_8)) }
                            ?: error("unavailable")
                        activity.runOnUiThread { complete(p, true) }
                    } else {
                        val json = activity.contentResolver.openInputStream(uri)?.use { readBounded(it) } ?: error("invalid_backup")
                        val parsed = validate(json)
                        activity.runOnUiThread { complete(p, true, data = parsed) }
                    }
                } catch (_: Exception) { activity.runOnUiThread { complete(p, false, "invalid_backup") } }
            }
        }
        return true
    }

    private fun transfer(p: Pending, result: AuthorizationResult) {
        val token = result.accessToken
        if (token.isNullOrBlank() || SCOPE !in result.grantedScopes) {
            complete(p, false, "authorization_failed"); return
        }
        worker.execute {
            try {
                val query = "spaces=appDataFolder&fields=files(id)&pageSize=1&orderBy=modifiedTime%20desc&q=" +
                    java.net.URLEncoder.encode("name = '${BackupPolicy.FILE_NAME}' and trashed = false", "UTF-8")
                val files = JSONObject(http("GET", "$DRIVE/files?$query", token)).getJSONArray("files")
                // Never choose an arbitrary document: this list is restricted to the app's own folder and filename.
                val id = if (files.length() > 0) files.getJSONObject(0).getString("id") else null
                if (p.operation == "restore") {
                    if (id == null) error("no_backup")
                    require(id.matches(Regex("[A-Za-z0-9_-]+")))
                    val parsed = validate(http("GET", "$DRIVE/files/$id?alt=media", token))
                    activity.runOnUiThread { complete(p, true, data = parsed) }
                } else {
                    if (id != null) {
                        require(id.matches(Regex("[A-Za-z0-9_-]+")))
                        http("PATCH", "$UPLOAD/files/$id?uploadType=media", token, p.json!!, "application/json; charset=UTF-8")
                    } else {
                        val boundary = "ssbackup_${java.util.UUID.randomUUID()}"
                        val metadata = JSONObject().put("name", BackupPolicy.FILE_NAME).put("parents", org.json.JSONArray().put("appDataFolder"))
                        val body = "--$boundary\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n$metadata\r\n" +
                            "--$boundary\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${p.json}\r\n--$boundary--\r\n"
                        http("POST", "$UPLOAD/files?uploadType=multipart", token, body, "multipart/related; boundary=$boundary")
                    }
                    activity.runOnUiThread { complete(p, true) }
                }
            } catch (e: Exception) {
                val reason = if (e.message == "no_backup") "no_backup" else "network_error"
                activity.runOnUiThread { complete(p, false, reason) }
            }
        }
    }

    private fun http(method: String, url: String, token: String, body: String? = null, type: String = "application/json"): String {
        val connection = URL(url).openConnection() as HttpURLConnection
        try {
            connection.instanceFollowRedirects = false
            connection.connectTimeout = 20000; connection.readTimeout = 30000
            connection.requestMethod = method
            connection.setRequestProperty("Authorization", "Bearer $token")
            if (body != null) {
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", type)
                val bytes = body.toByteArray(Charsets.UTF_8)
                connection.setFixedLengthStreamingMode(bytes.size)
                connection.outputStream.use { it.write(bytes) }
            }
            check(connection.responseCode in 200..299) { "request_failed" }
            return connection.inputStream.use { readBounded(it) }
        } finally { connection.disconnect() }
    }

    private fun readBounded(input: java.io.InputStream): String {
        val output = java.io.ByteArrayOutputStream()
        val buffer = ByteArray(8192)
        while (true) {
            val n = input.read(buffer); if (n == -1) break
            require(output.size() + n <= BackupPolicy.MAX_BYTES) { "too_large" }
            output.write(buffer, 0, n)
        }
        return output.toString("UTF-8")
    }

    private fun validate(json: String): JSONObject {
        require(BackupPolicy.allowedSize(json.toByteArray(Charsets.UTF_8).size))
        val value = JSONObject(json)
        require(value.getString("format") == "study-station-backup" && value.getInt("version") == 1)
        value.getJSONObject("progress"); value.getJSONObject("local")
        return value
    }

    private fun current(p: Pending) = pending === p && p.generation == generation && web.url == p.pageUrl && !activity.isDestroyed
    private fun emit(p: Pending, ok: Boolean, error: String? = null, data: JSONObject? = null) {
        val result = JSONObject().put("operation", p.operation).put("ok", ok)
        if (error != null) result.put("error", error)
        if (data != null) result.put("data", data)
        // A renderer can disappear between the URL check and delivery; that must never crash the app.
        runCatching { p.reply.postMessage(result.toString()) }
    }
    private fun complete(p: Pending, ok: Boolean, error: String? = null, data: JSONObject? = null) {
        if (!current(p)) return
        pending = null
        emit(p, ok, error, data)
    }
    fun destroy() { generation++; pending = null; worker.shutdownNow() }

    companion object {
        private const val AUTH_REQUEST = 4101
        private const val DOCUMENT_REQUEST = 4102
        private const val SCOPE = "https://www.googleapis.com/auth/drive.appdata"
        private const val DRIVE = "https://www.googleapis.com/drive/v3"
        private const val UPLOAD = "https://www.googleapis.com/upload/drive/v3"
    }
}
