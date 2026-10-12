package com.studystation.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class LinksTest {
    private val base = "https://ss.example.org"
    private val v = "5cb63f101a"

    @Test
    fun onlyOurServerStaysInTheApp() {
        assertTrue(Links.isInApp("https://ss.example.org/practice/maths/percentage", base))
        assertTrue(Links.isInApp("https://SS.example.org:443/", base))
        assertFalse(Links.isInApp("http://ss.example.org/", base))                      // not HTTPS
        assertFalse(Links.isInApp("https://ss.example.org.evil.in/", base))
        assertFalse(Links.isInApp("https://ss.example.org@evil.in/", base))             // user-info trick
        assertFalse(Links.isInApp("https://ssc.gov.in/notice.pdf", base))
        assertFalse(Links.isInApp("javascript:alert(1)", base))
        assertFalse(Links.isInApp("not a url", base))
    }

    @Test
    fun aLocalTestServerMatchesByPort() {
        assertTrue(Links.isInApp("http://10.0.2.2:8000/mock", "http://10.0.2.2:8000"))
        assertFalse(Links.isInApp("http://10.0.2.2:5000/mock", "http://10.0.2.2:8000"))
    }

    @Test
    fun otherLinksGoToThePhonesApps() {
        assertTrue(Links.opensOutside("https://ssc.gov.in/notice.pdf"))
        assertTrue(Links.opensOutside("tel:1800123456"))
        assertFalse(Links.opensOutside("intent://evil#Intent;end"))
        assertFalse(Links.opensOutside("file:///data/data/x"))
        assertFalse(Links.opensOutside("javascript:alert(1)"))
    }

    @Test
    fun bundledFilesAreUsedOnlyForTheExactVersion() {
        assertEquals("css/app.css", Links.bundledAsset("$base/static/css/app.css?v=$v", base, v))
        assertEquals("icon.svg", Links.bundledAsset("$base/static/icon.svg?x=1&v=$v", base, v))
        assertNull(Links.bundledAsset("$base/static/css/app.css?v=0000000000", base, v))   // server is newer
        assertNull(Links.bundledAsset("$base/static/css/app.css", base, v))
        assertNull(Links.bundledAsset("$base/static/css/app.css?v=$v", base, ""))
        assertNull(Links.bundledAsset("https://evil.in/static/css/app.css?v=$v", base, v))
        assertNull(Links.bundledAsset("$base/api/v1/me?v=$v", base, v))
    }

    @Test
    fun bundledPathsCannotLeaveTheFolder() {
        assertNull(Links.bundledAsset("$base/static/../secret.css?v=$v", base, v))
        assertNull(Links.bundledAsset("$base/static/js/%2e%2e/app.js?v=$v", base, v))
        assertNull(Links.bundledAsset("$base/static//app.js?v=$v", base, v))
        assertNull(Links.bundledAsset("$base/static/notes.txt?v=$v", base, v))               // unknown type
    }
}
