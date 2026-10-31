# ▶️ START HERE — Study Station का काम किसी भी AI से करवाने की मास्टर instruction

यह file मालिक के लिए है। हर काम के लिए **एक लाइन** है — repo को Antigravity / Cursor / Claude Code (कोई भी AI
जिसके पास files + terminal हों) में खोलें और नीचे की लाइन chat में चिपका दें। AI बाकी सब खुद करेगा:
काम चुनना → नियम पढ़ना → लिखना → खुद जाँचना → commit/push → हिंदी में रिपोर्ट।

> हमेशा branch `claude/elegant-rubin-sgov1q` पर काम होता है (जब तक आप इसे merge न करें)। `main` पर कभी नहीं।
> एक समय में **एक ही AI** एक branch पर लिखे — दो AI एक साथ चलाने हों तो अलग-अलग किताबें दें।
> Chat लंबी हो जाए → नई chat खोलें, वही लाइन फिर चिपकाएँ; काम वहीं से आगे चलता है।

---

## 1. 📚 किताबें पूरी करना (सबसे बड़ा काम)
```
study_station/books/BOOK_AGENT.md पढ़ो और उसके हिसाब से "book" चलाओ
```
| लिखें | क्या होगा |
|---|---|
| `"book"` | अगले 3 अध्याय (क्रम `books/QUEUE.txt` से) — लिखो, जाँचो, commit करो |
| `"book 5"` | 5 अध्याय |
| `"book status"` | सिर्फ़ हालत बताओ (कितने OK / FIX / TODO) |
| `"book study_station/books/…/Chapter_07_…"` | सिर्फ़ यही अध्याय |

नियम: `books/BOOK_RULES.md` · पूरी विधि (8 steps, सख़्त नियम, जाँच): `books/BOOK_AGENT.md` · जाँच का tool:
`cd study_station/v2 && python -m app.bookcheck --next | --status | <अध्याय>`

**अभी की हालत (3 अक्टूबर 2026):**
- 10th GK: 6–16 तैयार · 17, 18, 19 आधे लिखे (`WIP`) · 1 का सुधार आधा (`WIP`) · 2–5 सुधार बाकी · 20 = live करंट अफेयर्स
- 10th Reasoning (22), 10th Maths (22): लिखे हुए हैं पर सुधार चाहिए (`FIX`)
- 10th English, पूरी 12th और Graduation: लिखना बाकी (`TODO`)

## 2. ❓ गलत/संदिग्ध सवाल ठीक करना (868 flagged)
```
.claude/agents/ss-content-reviewer.md पढ़ो, उसे अपनी instruction मानो और 20 flagged सवाल ठीक करो
```
(डेटा `python -m app.review` से ही बदलता है — database को हाथ से नहीं छूना।)

## 3. 💼 सरकारी नौकरियाँ अपडेट करना
```
study_station/v2/JOBS_AGENT.md पढ़ो और उसके हिसाब से "job" चलाओ
```
(भारत के computer/server से चलाएँ — कई सरकारी sites विदेशी IP को रोकती हैं।)

## 4. 🩺 सब ठीक चल रहा है? (सिर्फ़ जाँच, कुछ बदलता नहीं)
```
.claude/agents/ss-observer.md पढ़ो, उसे अपनी instruction मानो और Study Station की हालत की रिपोर्ट हिंदी में दो
```

## 5. 🧪 Deploy से पहले टेस्ट
```
.claude/agents/ss-qa-tester.md पढ़ो, उसे अपनी instruction मानो और deploy से पहले पूरा टेस्ट करके bugs की सूची दो
```

## 6. 🚀 Deploy (आप खुद, एक बार)
`study_station/v2/DEPLOY.md` — server setup, `.env` भरना (`ADMIN_PASSWORD`, `SECRET_KEY`, `SITE_URL`,
`ANTHROPIC_API_KEY` — key हो तो AI tutor, सवाल बनाना, करंट अफेयर्स और `bookgen` चालू), फिर उसकी checklist।

---

## हर AI के लिए 6 पक्के नियम (हर काम पर लागू)
1. पहले उस काम की instruction file **पूरी पढ़ो**, फिर `study_station/v2/CLAUDE.md` के नियम।
2. तथ्य सिर्फ़ official/NCERT स्रोत से; पक्का न हो तो छोड़ दो। कोई गढ़ा हुआ आँकड़ा, PYQ, नाम या तारीख़ नहीं।
3. सिर्फ़ अपने काम की files बदलो; जाँच वाले tools/tests को पास करवाने के लिए कभी मत बदलो।
4. हर काम के बाद उसकी जाँच चलाओ (`bookcheck`, `pytest -q`, …) — fail हो तो commit मत करो।
5. Commit में सिर्फ़ अपने काम की files; `git pull --rebase` के बाद push; कभी `--force` नहीं, कभी `main` नहीं।
6. आख़िर में हिंदी में छोटी रिपोर्ट: क्या किया · क्या जाँचा · किस पर शक है · अगला क्या।
