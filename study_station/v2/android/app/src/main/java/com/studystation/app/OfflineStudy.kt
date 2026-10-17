package com.studystation.app

import java.net.URI

/** Strict, Android-independent route policy for the public study pack bundled in the APK. */
object OfflineStudy {
    /** Keep the live Jobs/CA screens, but their primary navigation returns to local study. */
    val navigationScript = """
        (function(){if(location.pathname==='/offline-study'||window.__ssLocalNavigation)return;
        window.__ssLocalNavigation=true;
        document.addEventListener('click',function(e){
          if(e.defaultPrevented||e.button!==0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
          var a=e.target.closest&&e.target.closest('a');if(!a||a.hasAttribute('download')||a.target==='_blank')return;
          var u;try{u=new URL(a.href,location.href);}catch(ignore){return;}
          if(u.origin!==location.origin)return;
          var routes={'/':'home','/practice':'practice','/mock':'mock','/revise':'revision','/books':'books','/questions':'questions','/progress':'progress','/settings':'settings'};
          if(!Object.prototype.hasOwnProperty.call(routes,u.pathname))return;
          e.preventDefault();e.stopImmediatePropagation();
          location.href='/offline-study#'+routes[u.pathname];
        },true);})();
    """.trimIndent()

    fun asset(method: String, url: String, base: String, language: String = "hi"): String? {
        if (!method.equals("GET", true) || !Links.isInApp(url, base)) return null
        val uri = try { URI(url) } catch (_: Exception) { return null }
        val path = uri.rawPath ?: return null
        if (path == "/offline-study" || path == "/offline-study/") {
            val requested = uri.rawQuery?.split('&')?.firstOrNull { it.startsWith("lang=") }?.substring(5)
            val lang = if ((requested ?: language) == "en") "en" else "hi"
            return "offline/$lang.html"
        }
        if (!path.startsWith("/offline-content/")) return null
        val name = path.removePrefix("/offline-content/")
        if (!name.matches(Regex("[A-Za-z0-9_./-]+")) ||
            name.split('/').any { it.isEmpty() || it == "." || it == ".." }) return null
        if (mime(name) == null) return null
        return "study/$name"
    }

    fun mime(name: String): String? = when (name.substringAfterLast('.').lowercase()) {
        "html" -> "text/html"
        "txt", "md" -> "text/plain"
        else -> Links.mime(name)
    }
}
