package com.studystation.app

import org.junit.Assert.*
import org.junit.Test

class OfflineStudyTest {
    private val base = "https://study.example"

    @Test fun localPagesRespectExplicitLanguageAndHashRoutes() {
        assertEquals("offline/hi.html", OfflineStudy.asset("GET", "$base/offline-study#/books", base))
        assertEquals("offline/en.html", OfflineStudy.asset("GET", "$base/offline-study?lang=en#/questions", base))
        assertEquals("offline/en.html", OfflineStudy.asset("GET", "$base/offline-study", base, "en"))
        assertEquals("study/books/chapter-1.json", OfflineStudy.asset("GET", "$base/offline-content/books/chapter-1.json", base))
        assertEquals("application/json", OfflineStudy.mime("study/catalog.json"))
        assertEquals("text/html", OfflineStudy.mime("offline/hi.html"))
    }

    @Test fun foreignOriginsWritesAndPrivateServerRoutesAreNeverLocal() {
        assertNull(OfflineStudy.asset("POST", "$base/offline-study", base))
        assertNull(OfflineStudy.asset("GET", "https://evil.example/offline-study", base))
        assertNull(OfflineStudy.asset("GET", "http://study.example/offline-content/catalog.json", base))
        assertNull(OfflineStudy.asset("GET", "$base/api/v1/me", base))
        assertNull(OfflineStudy.asset("GET", "$base/offline-study-extra", base))
    }

    @Test fun contentCannotEscapePackOrDecodeIntoAnotherPath() {
        for (name in listOf("../shell/hi.html", "a/../b.json", "a//b.json", "%2e%2e/secret.json",
            "%252e%252e/secret.json", "a%2fb.json", "a%5cb.json", "a/./b.json", "secret.exe", "")) {
            assertNull(name, OfflineStudy.asset("GET", "$base/offline-content/$name", base))
        }
    }
}
