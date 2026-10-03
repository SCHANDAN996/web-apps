# 🤖 Study Station — Agent टीम

Project का हर काम एक तय agent करता है। Agents `.claude/agents/` (repo root) में हैं, और slash commands
`.claude/commands/` में। Claude Code में repo खोलें — agents अपने-आप मिल जाते हैं; किसी और AI में उस
agent की `.md` file पढ़ाकर वही निर्देश दें। सभी agents `study_station/v2/CLAUDE.md` के नियम मानते हैं।

## कौन क्या करता है

| Agent | काम | बदलाव करता है? | कब |
|---|---|---|---|
| **ss-developer** | features बनाना, bugs ठीक करना, tests के साथ | ✅ code | जब काम तय हो |
| **ss-improver** | सबूत (metrics, code, UX) देखकर अगले सबसे ज़रूरी सुधारों की ranked सूची — `IMPROVEMENTS.md` | सिर्फ़ सूची | हफ़्ते में एक बार / "अब क्या सुधारें?" |
| **ss-observer** | site, jobs, current affairs, content, AI budget की निगरानी | ❌ read-only | रोज़ / deploy के बाद / "कुछ गड़बड़ है" |
| **ss-qa-tester** | pytest + फ़ोन वाला browser flow + exploratory testing, bug रिपोर्ट | ❌ | deploy से पहले, UI बदलने के बाद |
| **ss-security-reviewer** | auth, XSS, CSRF, scraping, AI abuse की जाँच | ❌ | risky बदलाव से पहले, महीने में एक बार |
| **ss-ux-designer** | design/motion/accessibility review, design system के अंदर सुधार | ✅ CSS/templates | नई screen, polish |
| **ss-jobs-updater** | पूरा नौकरी-अपडेट (`JOBS_AGENT.md`), research lanes parallel में | ✅ CLI से data | `job` / jobs पुरानी लगें |
| **ss-jobs-researcher** | एक lane (जैसे रेलवे) की official research | ❌ सिर्फ़ जवाब | ss-jobs-updater चलाता है |
| **ss-content-reviewer** | reported/flagged सवाल जाँचकर ठीक करना (`app.review`) | ✅ CLI से data | admin queue बढ़े |
| **ss-content-generator** | कमज़ोर topics में नए सवाल (`app.generate`) | ✅ CLI से data | observe "thin topics" बताए |
| **ss-current-affairs** | AIR/PIB pipeline, सार और MCQ की spot-check | ✅ CLI से data | रोज़ |

## Slash commands (Claude Code)

| Command | क्या होता है |
|---|---|
| `/job` | ss-jobs-updater → पूरा नौकरी-अपडेट (research 6 lanes parallel) |
| `/observe` | ss-observer → हालत की रिपोर्ट + किसे क्या ठीक करना है |
| `/review-questions` | ss-content-reviewer → reported, फिर flagged सवाल |
| `/content` | ss-content-generator → फिर ss-content-reviewer |
| `/ca` | ss-current-affairs |
| `/improve` | ss-improver → `IMPROVEMENTS.md`; "build" कहें तो ss-developer + ss-qa-tester |
| `/qa` | ss-qa-tester + ss-security-reviewer **एक साथ** → एक रिपोर्ट |

## साथ में कैसे काम करते हैं

```
            ┌──────────── ss-observer (रोज़) ────────────┐
            │  समस्या + सबूत                              │
            ▼                                             ▼
   data की समस्या                                code/infra की समस्या
   ├─ jobs      → ss-jobs-updater ─┬─ ss-jobs-researcher ×6 (parallel)
   ├─ सवाल     → ss-content-reviewer
   ├─ कम सवाल  → ss-content-generator → ss-content-reviewer
   └─ ख़बरें    → ss-current-affairs
                                                  ss-improver (हफ़्ता) → IMPROVEMENTS.md
                                                         │ top item
                                                         ▼
                                   ss-developer / ss-ux-designer → ss-qa-tester + ss-security-reviewer (parallel) → deploy
```

**Parallel के नियम**
- Research, review और testing parallel चल सकते हैं (एक-दूसरे का data नहीं बदलते)।
- Database में लिखने वाला एक समय में **एक** agent (SQLite) — researchers सिर्फ़ जवाब लौटाते हैं।
- एक ही files पर दो developer agents एक साथ नहीं।

## सुझाया गया routine

| कब | क्या |
|---|---|
| हर 3 घंटे (cron, बिना AI) | jobs sweep · दिन में 3 बार current affairs · रात में cleanup + backup |
| रोज़ सुबह | `/observe` |
| हफ़्ते में 2–3 बार | `/job` (गहरी research) · `/review-questions` |
| हफ़्ते में एक बार | `/improve` · `/content` (AI key हो तो) |
| हर deploy से पहले | `/qa` |
