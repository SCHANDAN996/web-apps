package com.studystation.app
import org.junit.Assert.*
import org.junit.Test
class QuestionLinksTest {
    private val url = "https://studystation.ebookcart.in/q/123"
    @Test fun acceptedLinksRouteToTheBundledQuestion() {
        assertEquals("https://studystation.ebookcart.in/offline-study?lang=en#shared/123", QuestionLinks.parse("$url?lang=en")?.destination("https://studystation.ebookcart.in", true))
        assertEquals("hi", QuestionLinks.parse(url)?.lang)
        assertEquals("$url?lang=hi", QuestionLinks.parse(url)?.destination("https://studystation.ebookcart.in", false))
    }
    @Test fun untrustedOrAmbiguousLinksCannotRoute() {
        listOf("http://studystation.ebookcart.in/q/123", "https://studystation.ebookcart.in.evil/q/123", "https://evil@studystation.ebookcart.in/q/123", "$url?lang=fr", "$url?lang=en&lang=hi", "$url?token=private", "$url#answer", "$url/", "https://studystation.ebookcart.in/q/%31", "https://studystation.ebookcart.in/q/0", "https://studystation.ebookcart.in:8443/q/1", "https://studystation.ebookcart.in/q/99999999999999999999999").forEach { assertNull(it, QuestionLinks.parse(it)) }
    }
    @Test fun shareContainsOnlyPublicQuestionAndChoices() {
        val target = QuestionLinks.target(123, "en")!!
        assertEquals("What?\n\nA) First\nB) Second\n\nSee the answer and solution in the Study Station app.\n$url?lang=en", QuestionLinks.text(target, "What?", listOf("First", "Second")))
        assertNull(QuestionLinks.text(target, "", listOf("A", "B")))
        assertNull(QuestionLinks.text(target, "What?", listOf("One")))
        assertNull(QuestionLinks.text(target, "What?", listOf("A", "")))
        assertNull(QuestionLinks.text(target, "What?", List(11) { "A" }))
        assertNull(QuestionLinks.target(-1, "en"))
        assertNull(QuestionLinks.target(1000000000000000L, "en"))
        assertNull(QuestionLinks.parse("https://studystation.ebookcart.in/q/1000000000000000"))
        assertNotNull(QuestionLinks.target(999999999999999L, "hi"))
        assertTrue(QuestionLinks.text(QuestionLinks.target(1, "hi")!!, "Q", listOf("A", "B"))!!.contains("उत्तर और समाधान"))
        assertNull(QuestionLinks.target(1, "xx"))
    }
}
