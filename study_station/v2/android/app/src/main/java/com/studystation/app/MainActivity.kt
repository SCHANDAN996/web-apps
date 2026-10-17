package com.studystation.app

import android.annotation.SuppressLint
import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.View
import android.view.WindowInsets
import android.webkit.CookieManager
import android.webkit.RenderProcessGoneDetail
import android.webkit.ServiceWorkerClient
import android.webkit.ServiceWorkerController
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.ProgressBar
import android.window.OnBackInvokedDispatcher
import java.io.IOException

/**
 * The whole app: one WebView on the Study Station v2 server. The learner's progress lives on the server
 * (device cookie, kept by CookieManager); CSS/JS/icon are read from the APK; other sites open outside.
 */
class MainActivity : Activity() {
    private lateinit var web: WebView
    private lateinit var progress: ProgressBar
    private lateinit var offline: View
    private var failed = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        web = findViewById(R.id.web)
        progress = findViewById(R.id.progress)
        offline = findViewById(R.id.offline)
        padForSystemBars(findViewById(R.id.root))
        findViewById<Button>(R.id.retry).setOnClickListener { web.loadUrl(web.url ?: HOME) }
        if (Build.VERSION.SDK_INT >= 33) {
            onBackInvokedDispatcher.registerOnBackInvokedCallback(OnBackInvokedDispatcher.PRIORITY_DEFAULT) { goBack() }
        }
        setUpWebView()
        if (savedInstanceState == null || web.restoreState(savedInstanceState) == null) web.loadUrl(HOME)
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setUpWebView() {
        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            userAgentString = "$userAgentString StudyStationApp/${BuildConfig.VERSION_NAME}"
        }
        CookieManager.getInstance().setAcceptCookie(true)
        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG)
        web.webViewClient = Client()
        web.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView, newProgress: Int) {
                progress.progress = newProgress
                progress.visibility = if (newProgress < 100) View.VISIBLE else View.GONE
            }
        }
        web.setDownloadListener { url, _, _, _, _ -> openOutside(Uri.parse(url)) }
        ServiceWorkerController.getInstance().setServiceWorkerClient(object : ServiceWorkerClient() {
            override fun shouldInterceptRequest(request: WebResourceRequest) =
                frame(request, false) ?: bundled(request.url)
        })
    }

    /**
     * The app's structure lives in the APK: opening a screen shows the bundled frame (top bar, tab bar,
     * icons — assets/shell) at once, and app.js fetches that screen's content from the server.
     * Skipped when the page has found the server's CSS/JS newer than this APK's (cookie ss_shell_off).
     */
    private fun frame(request: WebResourceRequest, mainFrame: Boolean): WebResourceResponse? {
        if (!Links.wantsFrame(request.method, request.url.toString(), request.requestHeaders, BuildConfig.BASE_URL, mainFrame)) return null
        val cookies = CookieManager.getInstance().getCookie(BuildConfig.BASE_URL)
        if (Links.cookie(cookies, "ss_shell_off") == BuildConfig.ASSET_V) return null
        val lang = if (Links.cookie(cookies, "ss_lang") == "en") "en" else "hi"
        return try {
            WebResourceResponse("text/html", "utf-8", 200, "OK", mapOf("Cache-Control" to "no-store"),
                assets.open("shell/$lang.html"))
        } catch (e: IOException) {
            null                // no frame in this APK: the server sends the whole page
        }
    }

    private inner class Client : WebViewClient() {
        override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
            if (Links.isInApp(request.url.toString(), BuildConfig.BASE_URL)) return false
            openOutside(request.url)
            return true
        }

        override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest) =
            frame(request, request.isForMainFrame) ?: bundled(request.url)

        override fun onPageStarted(view: WebView, url: String?, favicon: Bitmap?) {
            failed = false
        }

        override fun onReceivedError(view: WebView, request: WebResourceRequest, error: WebResourceError) {
            if (request.isForMainFrame) {
                failed = true
                showOffline(true)
            }
        }

        override fun onPageFinished(view: WebView, url: String?) {
            if (!failed) showOffline(false)
            CookieManager.getInstance().flush()
        }

        override fun onRenderProcessGone(view: WebView, detail: RenderProcessGoneDetail): Boolean {
            recreate()          // the page's process died (low memory): start the screen again instead of crashing
            return true
        }
    }

    /** Our own CSS/JS/icon from the APK when the page asks for the version this APK was built with. */
    private fun bundled(uri: Uri): WebResourceResponse? {
        val name = Links.bundledAsset(uri.toString(), BuildConfig.BASE_URL, BuildConfig.ASSET_V) ?: return null
        return try {
            WebResourceResponse(Links.mime(name), "utf-8", 200, "OK",
                mapOf("Cache-Control" to "public, max-age=31536000, immutable"), assets.open(name))
        } catch (e: IOException) {
            null                // not in this APK: let the network answer
        }
    }

    private fun openOutside(uri: Uri) {
        if (!Links.opensOutside(uri.toString())) return
        try {
            startActivity(Intent(Intent.ACTION_VIEW, uri))
        } catch (e: ActivityNotFoundException) {
            // no app on this phone for the link
        }
    }

    private fun showOffline(show: Boolean) {
        offline.visibility = if (show) View.VISIBLE else View.GONE
        web.visibility = if (show) View.INVISIBLE else View.VISIBLE
    }

    private fun goBack() {
        if (!failed && web.canGoBack()) web.goBack() else finish()
    }

    @Deprecated("Android 12 and older; newer versions use the callback registered in onCreate")
    override fun onBackPressed() = goBack()

    /** Android 15+ draws apps under the status and navigation bars: keep the page (and keyboard) clear of them. */
    private fun padForSystemBars(root: View) {
        root.setOnApplyWindowInsetsListener { v, insets ->
            if (Build.VERSION.SDK_INT >= 30) {
                val i = insets.getInsets(
                    WindowInsets.Type.systemBars() or WindowInsets.Type.displayCutout() or WindowInsets.Type.ime())
                v.setPadding(i.left, i.top, i.right, i.bottom)
                WindowInsets.CONSUMED       // or the page pads for the same bars again (safe-area-inset)
            } else {
                @Suppress("DEPRECATION")
                v.setPadding(insets.systemWindowInsetLeft, insets.systemWindowInsetTop,
                    insets.systemWindowInsetRight, insets.systemWindowInsetBottom)
                @Suppress("DEPRECATION")
                insets.consumeSystemWindowInsets()
            }
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        web.saveState(outState)
    }

    override fun onResume() {
        super.onResume()
        web.onResume()
    }

    override fun onPause() {
        CookieManager.getInstance().flush()
        web.onPause()
        super.onPause()
    }

    override fun onDestroy() {
        web.destroy()
        super.onDestroy()
    }

    private companion object {
        const val HOME = BuildConfig.BASE_URL + "/"
    }
}
