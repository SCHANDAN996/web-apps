# 🤖 Study Station — Agent टीम

Project का हर काम एक तय agent करता है। Agents `.claude/agents/` (repo root) में हैं, और slash commands
`.claude/commands/` में। Claude Code में repo खोलें — agents अपने-आप मिल जाते हैं; किसी और AI में उस
agent की `.md` file पढ़ाकर वही निर्देश दें। सभी agents `study_station/v2/CLAUDE.md` के नियम मानते हैं।

## 👑 Boss — ss-boss

सबका मुखिया। कोई भी बड़ा काम सिर्फ़ boss को दें — वह काम बाँटता है, सही agent चुनता है, जो काम साथ
चल सकते हैं उन्हें **एक साथ** चलाता है, नतीजे खुद जाँचता है (tests, observe), और हिंदी में रिपोर्ट देता है।
Deploy, data हटाना, बड़ा AI ख़र्च जैसे फ़ैसलों से पहले आपसे पूछता है।

```
/boss <काम>            # Claude Code में, जैसे: /boss नया "previous year papers" page बनाओ और deploy से पहले जाँचो
/boss                  # खाली = रोज़ का routine
claude --agent ss-boss # पूरा session boss mode में
```

> Boss को **main agent** की तरह चलाएँ (`/boss` या `--agent`) — Claude Code में sub-agent आगे sub-agent
> नहीं चला सकता, इसलिए किसी दूसरे agent के अंदर से boss काम नहीं बाँट पाएगा (तब वह सिर्फ़ plan देता है)।

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
| **ss-book-writer** | किताब का एक अध्याय लिखना/सुधारना (prompts → हिंदी+English content, 6×25 MCQ), `app.bookcheck` से जाँच | ✅ `books/` files | `/book` — हर अध्याय के लिए एक, parallel |

## Slash commands (Claude Code)

| Command | क्या होता है |
|---|---|
| `/boss <काम>` | 👑 boss → plan, सही agents (parallel), जाँच, हिंदी रिपोर्ट |
| `/job` | main agent `JOBS_AGENT.md` चलाता है — 6 ss-jobs-researcher lanes parallel |
| `/observe` | ss-observer → हालत की रिपोर्ट + किसे क्या ठीक करना है |
| `/review-questions` | ss-content-reviewer → reported, फिर flagged सवाल |
| `/content` | ss-content-generator → फिर ss-content-reviewer |
| `/ca` | ss-current-affairs |
| `/improve` | ss-improver → `IMPROVEMENTS.md`; "build" कहें तो ss-developer + ss-qa-tester |
| `/qa` | ss-qa-tester + ss-security-reviewer **एक साथ** → एक रिपोर्ट |
| `/book [किताब]` | main agent `app.bookcheck` चलाता है → हर अधूरे अध्याय पर एक ss-book-writer (7 तक parallel) → जाँच → commit |

## साथ में कैसे काम करते हैं

```
                              👑 ss-boss (आपका हर काम यहीं से)
                                          │ बाँटता · parallel चलाता · जाँचता · रिपोर्ट
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

## 📚 किताबें (Books)

किताबें `study_station/books/<Level>/<Subject>/…/Chapter_NN_*/` में हैं। हर अध्याय के sections (Content, Key Facts,
Feynman, Mind Map, Flashcards, PYQ, Memory Hooks/Short Tricks, 6×25 MCQ) हिंदी+English में। जो file अभी भी
prompt है वह "todo" है। हालत देखने के लिए:

```
cd study_station/v2 && python -m app.bookcheck ../books/10th_Level/GK/Foundation_10th_GK_WorldClass
```

प्राथमिकता: 10th GK → 10th Reasoning (सुधार) → 10th English → 12th Maths → 12th GK/Reasoning/English → Graduation।
करंट अफेयर्स वाले अध्याय किताब में नहीं लिखे जाते — वे live AIR/PIB pipeline (`/ca`) से आते हैं।

## सुझाया गया routine

| कब | क्या |
|---|---|
| हर 3 घंटे (cron, बिना AI) | jobs sweep · दिन में 3 बार current affairs · रात में cleanup + backup |
| रोज़ सुबह | `/observe` |
| हफ़्ते में 2–3 बार | `/job` (गहरी research) · `/review-questions` |
| हफ़्ते में एक बार | `/improve` · `/content` (AI key हो तो) |
| हर deploy से पहले | `/qa` |
