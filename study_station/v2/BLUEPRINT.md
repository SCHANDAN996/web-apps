# Study Station v2 — Blueprint

पुराने ढाँचे (Class 1–12 tree, अलग-अलग static pages, demo data) को छोड़कर यह version
इस सवाल से शुरू होता है: **2026 में एक सरकारी-परीक्षा aspirant को असल में क्या चाहिए?**

## 1. User कौन है

- 10वीं / 12वीं / Graduate पास, ज़्यादातर Hindi-medium, छोटे शहर/गाँव।
- सस्ता Android फ़ोन, कमज़ोर 4G, सीमित data।
- लक्ष्य: SSC (GD, MTS, CHSL, CGL), Railway (Group D, NTPC), Banking (IBPS Clerk/PO)।
- असली exam **computer-based (CBT)** होता है — negative marking, section, timer, question palette।

## 2. उसे क्या चाहिए → हम क्या बनाते हैं

| ज़रूरत | Feature | v2 में |
|---|---|---|
| "मेरे exam के हिसाब से बताओ" | Onboarding: भाषा + योग्यता + target exams → personalised home | ✅ |
| रोज़ थोड़ा-थोड़ा अभ्यास | Topic practice: तुरंत feedback, हल, हिंदी⇄English हर सवाल पर | ✅ |
| असली exam जैसा अनुभव | CBT mock: असली pattern, timer, palette (answered / not answered / marked / not visited), negative marking | ✅ |
| ग़लतियाँ न दोहराऊँ | Mistake notebook + spaced repetition "आज दोहराएँ" queue | ✅ |
| कहाँ कमज़ोर हूँ | Topic-wise accuracy, कमज़ोर topics की सूची | ✅ |
| कौन सी vacancy मेरे लिए | Jobs: योग्यता/राज्य filter, अंतिम तिथि, "X दिन बचे", official link, last verified | ✅ |
| भरोसा | हर सवाल पर source + review status; "गलती बताएँ" button | ✅ |
| Data कम, offline | PWA, बिना CDN, system fonts, inline SVG icons, offline shell | ✅ |
| Google से मिलना | Server-rendered pages: exam, topic, job (JobPosting schema) | ✅ |
| Current affairs | रोज़ के 10 facts + monthly quiz | ⏭ Phase 2 (content pipeline चाहिए) |
| AI doubt solver | "इसे और आसान समझाओ" — grounded, rate-limited | ⏭ Phase 2 |
| Login / sync | Phone OTP या Google; अभी guest device-id पर progress | ⏭ Phase 2 |

**जानबूझकर नहीं:** नकली user counts, नकली rank/percentile (जब तक असली users न हों),
बिना source के "PYQ" label, class 1–8 NCERT tree।

## 3. Data — क्या ज़रूरी है

```
Exam            slug, name_hi/en, level (10th/12th/graduate), body (SSC/RRB/IBPS),
                duration_min, negative_mark, pattern_note, pattern_source_url
ExamSection     exam, subject, questions, marks_per_q, order
Subject         slug, name_hi/en               (quant, reasoning, english, ga)
Topic           subject, slug, name_hi/en, level
Question        topic, level, text_hi/en, options_hi/en[4], answer_index,
                solution_hi/en, difficulty, source_type (pyq|ai_generated|editorial),
                source_ref, review_status (unreviewed|verified|flagged)
Device          anonymous id (cookie) — लॉगिन आने पर user से जुड़ेगा
Attempt         device, mode (practice|mock), exam?, started/finished, score
AttemptAnswer   attempt, question, chosen_index, correct, time_ms, marked
ReviewCard      device, question, box (Leitner 1–5), due_at   ← mistake notebook
QuestionReport  question, device, reason, note
Job             slug, title, org, category, job_type, min_qualification, states,
                vacancies, last_date (DATE), source_url, official_url, verified_at
```

नियम:
- तारीख़ें **DATE** column में (text नहीं) — expiry और sorting भरोसेमंद।
- `source_type=ai_generated` वाले सवाल साफ़ label के साथ दिखते हैं; "PYQ" label
  सिर्फ़ तब जब `source_ref` में exam + साल + shift हो।
- Exam pattern के साथ हमेशा "official notification से मिलाएँ" note + source link।

## 4. Stack — और क्यों

| चुनाव | वजह |
|---|---|
| **FastAPI** + Jinja2 SSR | typed JSON API (आगे Android/Flutter app वही API इस्तेमाल करेगा) + SEO वाले HTML pages एक ही server से |
| **SQLAlchemy 2** + SQLite (WAL) | एक VPS पर काफ़ी; `DATABASE_URL` से Postgres पर बिना code बदले |
| Vanilla JS modules, **no build step** | छोटा bundle, सस्ते फ़ोन पर तेज़, कोई toolchain नहीं |
| System font stack (Noto Sans Devanagari Android में पहले से) | 0 KB font download |
| Inline SVG icons | CDN पर निर्भरता नहीं |
| Service worker | offline shell + पिछले practice sets |
| pytest + Playwright | API और असली browser flow दोनों test |

## 5. Design system

- Mobile-first, 16px gutter, bottom tab bar (Home · Practice · Mock · Revise · Jobs)।
- Tokens: color (light/dark, AA contrast), radius, spacing (4px grid), motion
  (`--dur-1 120ms`, `--dur-2 200ms`, `--dur-3 320ms`, `--ease-out cubic-bezier(.2,.8,.2,1)`)।
- Motion सिर्फ़ `transform`/`opacity` पर; `prefers-reduced-motion` पर बंद।
- सही/गलत feedback: सही पर हल्का scale-pulse, गलत पर 2-step shake + रंग; हमेशा रंग के साथ
  icon/text भी (color-blind safe)।
- Devanagari: line-height 1.75, body 17px।
- हर interactive element पर `:focus-visible` ring, 44px touch target।

## 6. Phases

1. **v2 core (यह PR):** ऊपर ✅ वाले सब features, existing MCQ sets और jobs का import।
2. Content: सवालों की review queue (admin), current affairs pipeline, AI doubt solver।
3. Accounts + sync, push notifications (job deadline reminders), Android wrapper (TWA)।
