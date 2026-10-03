/**
 * book-reader.js — V2: Fetch-based chapter reader with SPA overlay
 * Content is loaded from pre-generated HTML files via fetch()
 * JS only handles: tabs, language toggle, MCQ clicks, flashcard flips, speaker
 */

var bookReaderLang = localStorage.getItem('language') || 'en';
var bookReaderActiveTab = 'content';
var currentBookChapter = null;
var chapterIndexCache = {}; // Cache for _index.json data

var BOOK_TABS = [
  { id: 'content',    icon: '📖', label_en: 'Content',      label_hi: 'सामग्री' },
  { id: 'feynman',    icon: '🧒', label_en: 'Feynman',      label_hi: 'फ़ेनमैन' },
  { id: 'mindmap',    icon: '🗺️', label_en: 'Mind Map',     label_hi: 'माइंड मैप' },
  { id: 'flashcards', icon: '🃏', label_en: 'Flashcards',   label_hi: 'फ़्लैशकार्ड' },
  { id: 'pyq',        icon: '📊', label_en: 'PYQ Analysis',  label_hi: 'PYQ विश्लेषण' },
  { id: 'tricks',     icon: '🪄', label_en: 'Short Tricks', label_hi: 'शॉर्ट ट्रिक्स' },
  { id: 'practice',   icon: '📝', label_en: 'Practice MCQs', label_hi: 'अभ्यास MCQ' }
];

// ====== BOOK CATEGORIES ======
var BOOK_CATEGORIES = [
  { id: 'competitive', emoji: '🏆', title_en: 'Competitive Exams', title_hi: 'प्रतियोगी परीक्षा', desc_en: 'SSC, Banking, Railway & more', desc_hi: 'SSC, बैंकिंग, रेलवे और अन्य', color: '#8B5CF6' },
  { id: 'ncert', emoji: '📚', title_en: 'NCERT Books', title_hi: 'NCERT पुस्तकें', desc_en: 'Class 6 to 12', desc_hi: 'कक्षा 6 से 12', color: '#10B981' }
];

var EXAM_LEVELS = [
  { id: '10th-level', emoji: '📗', title_en: 'Foundation — 10th Level', title_hi: 'फाउंडेशन — 10वीं स्तर', target_en: 'SSC MTS, GD Constable, Railway Group D', target_hi: 'SSC MTS, GD कॉन्स्टेबल, रेलवे ग्रुप D', color: '#10B981' },
  { id: '12th-level', emoji: '📘', title_en: 'Intermediate — 12th Level', title_hi: 'इंटरमीडिएट — 12वीं स्तर', target_en: 'SSC CHSL, Stenographer, Delhi Police SI', target_hi: 'SSC CHSL, स्टेनोग्राफर, दिल्ली पुलिस SI', color: '#3B82F6' },
  { id: 'graduation-level', emoji: '🎓', title_en: 'Advanced — Graduate Level', title_hi: 'एडवांस्ड — ग्रेजुएट स्तर', target_en: 'SSC CGL, Banking PO/Clerk, UPSC CSAT', target_hi: 'SSC CGL, बैंकिंग PO/क्लर्क, UPSC CSAT', color: '#8B5CF6' }
];

var SUBJECTS = [
  { id: 'math', emoji: '📐', name_en: 'Mathematics', name_hi: 'गणित', color: '#3B82F6' },
  { id: 'hindi', emoji: '📝', name_en: 'Hindi', name_hi: 'हिंदी', color: '#EF4444' },
  { id: 'gk', emoji: '🌍', name_en: 'General Knowledge', name_hi: 'सामान्य ज्ञान', color: '#10B981' },
  { id: 'reasoning', emoji: '🧠', name_en: 'Reasoning', name_hi: 'तर्कशक्ति', color: '#F59E0B' },
  { id: 'english', emoji: '🔤', name_en: 'English', name_hi: 'अंग्रेजी', color: '#8B5CF6' }
];

// Navigation state
var bookNavState = { category: null, level: null, subject: null };

// ====== RENDER: Category Selection ======
function renderBookCategories() {
  bookNavState = { category: null, level: null, subject: null };
  var isHi = bookReaderLang === 'hi';
  var container = document.getElementById('bookContentArea');
  document.getElementById('bookBackBtn').style.display = 'none';
  document.getElementById('bookPageTitle').textContent = isHi ? 'पुस्तकें' : 'Books';

  container.innerHTML = BOOK_CATEGORIES.map(function(cat) {
    return '<div class="card book-level-card" onclick="openBookCategory(\'' + cat.id + '\')" style="border-left:4px solid ' + cat.color + ';">' +
      '<div style="display:flex;align-items:center;gap:1rem;">' +
      '<div style="font-size:2.5rem;">' + cat.emoji + '</div>' +
      '<div style="flex:1;">' +
      '<div style="font-weight:800;font-size:1.15rem;">' + (isHi ? cat.title_hi : cat.title_en) + '</div>' +
      '<div style="color:var(--text-secondary);font-size:0.85rem;margin-top:0.25rem;">' + (isHi ? cat.desc_hi : cat.desc_en) + '</div>' +
      '</div>' +
      '<ion-icon name="chevron-forward-outline" style="font-size:1.5rem;color:var(--text-secondary);"></ion-icon>' +
      '</div></div>';
  }).join('');
}

// ====== RENDER: Exam Levels ======
function openBookCategory(catId) {
  bookNavState.category = catId;
  var isHi = bookReaderLang === 'hi';
  var container = document.getElementById('bookContentArea');
  document.getElementById('bookBackBtn').style.display = 'inline-flex';
  document.getElementById('bookBackBtn').setAttribute('onclick', 'renderBookCategories()');

  if (catId === 'ncert') {
    window.location.href = 'classes.html';
    return;
  }

  document.getElementById('bookPageTitle').textContent = isHi ? 'प्रतियोगी परीक्षा' : 'Competitive Exams';
  container.innerHTML = EXAM_LEVELS.map(function(lv) {
    return '<div class="card book-level-card" onclick="openBookLevel(\'' + lv.id + '\')" style="border-left:4px solid ' + lv.color + ';">' +
      '<div style="display:flex;align-items:center;gap:1rem;">' +
      '<div style="font-size:2.5rem;">' + lv.emoji + '</div>' +
      '<div style="flex:1;">' +
      '<div style="font-weight:800;font-size:1.15rem;">' + (isHi ? lv.title_hi : lv.title_en) + '</div>' +
      '<div style="color:var(--text-secondary);font-size:0.85rem;margin-top:0.25rem;">' + (isHi ? lv.target_hi : lv.target_en) + '</div>' +
      '</div>' +
      '<ion-icon name="chevron-forward-outline" style="font-size:1.5rem;color:var(--text-secondary);"></ion-icon>' +
      '</div></div>';
  }).join('');
}

// ====== RENDER: Subjects ======
function openBookLevel(levelId) {
  bookNavState.level = levelId;
  var isHi = bookReaderLang === 'hi';
  var container = document.getElementById('bookContentArea');
  document.getElementById('bookBackBtn').setAttribute('onclick', 'openBookCategory("competitive")');

  var levelName = EXAM_LEVELS.find(function(l) { return l.id === levelId; });
  document.getElementById('bookPageTitle').textContent = isHi ? levelName.title_hi : levelName.title_en;

  container.innerHTML = SUBJECTS.map(function(sub) {
    return '<div class="card book-level-card" onclick="openSubject(\'' + levelId + '\', \'' + sub.id + '\')" style="border-left:4px solid ' + sub.color + ';">' +
      '<div style="display:flex;align-items:center;gap:1rem;">' +
      '<div style="font-size:2.5rem;">' + sub.emoji + '</div>' +
      '<div style="flex:1;">' +
      '<div style="font-weight:800;font-size:1.15rem;">' + (isHi ? sub.name_hi : sub.name_en) + '</div>' +
      '</div>' +
      '<ion-icon name="chevron-forward-outline" style="font-size:1.5rem;color:var(--text-secondary);"></ion-icon>' +
      '</div></div>';
  }).join('');
}

// ====== RENDER: Chapter List (fetched from _index.json) ======
function openSubject(levelId, subjectId) {
  bookNavState.subject = subjectId;
  var isHi = bookReaderLang === 'hi';
  var container = document.getElementById('bookContentArea');
  document.getElementById('bookBackBtn').setAttribute('onclick', 'openBookLevel("' + levelId + '")');

  var subName = SUBJECTS.find(function(s) { return s.id === subjectId; });
  document.getElementById('bookPageTitle').textContent = isHi ? subName.name_hi : subName.name_en;

  // Show loading
  container.innerHTML = '<div class="empty-state"><div class="loader"></div><div class="empty-state__title">Loading...</div></div>';

  var indexUrl = 'books/competitive-exams/' + levelId + '/' + subjectId + '/_index.json';

  fetch(indexUrl)
    .then(function(res) {
      if (!res.ok) throw new Error('Not found');
      return res.json();
    })
    .then(function(data) {
      chapterIndexCache[levelId + '/' + subjectId] = data;
      renderChapterList(data.chapters, levelId, subjectId);
    })
    .catch(function() {
      container.innerHTML = '<div class="empty-state"><div class="empty-state__icon">🚧</div>' +
        '<div class="empty-state__title">' + (isHi ? 'जल्द आ रहा है' : 'Coming Soon') + '</div>' +
        '<div class="empty-state__desc">' + (isHi ? 'इस विषय के अध्याय तैयार किए जा रहे हैं।' : 'Chapters for this subject are being prepared.') + '</div></div>';
    });
}

function renderChapterList(chapters, levelId, subjectId) {
  var isHi = bookReaderLang === 'hi';
  var container = document.getElementById('bookContentArea');

  container.innerHTML = chapters.map(function(ch) {
    var statusBadge = ch.status === 'ready'
      ? '<span class="badge badge--success">✅ ' + (isHi ? 'तैयार' : 'Ready') + '</span>'
      : '<span class="badge badge--warning">⏳ ' + (isHi ? 'जल्द' : 'Coming Soon') + '</span>';

    var clickAttr = ch.status === 'ready'
      ? 'onclick="openBookChapter(\'' + ch.slug + '\', \'' + levelId + '\', \'' + subjectId + '\')"'
      : 'style="opacity:0.5;cursor:default;"';

    return '<div class="chapter-item" ' + clickAttr + '>' +
      '<div class="chapter-num">' + ch.num + '</div>' +
      '<div style="flex:1;"><div class="chapter-name">' + (isHi ? ch.name_hi : ch.name_en) + '</div>' +
      '<div style="font-size:0.75rem;color:var(--text-secondary);">' + (isHi ? ch.name_en : ch.name_hi) + '</div></div>' +
      '<div>' + statusBadge + '</div></div>';
  }).join('');
}

// ====== OPEN CHAPTER READER (fetch HTML, inject into overlay) ======
function openBookChapter(slug, levelId, subjectId) {
  var isHi = bookReaderLang === 'hi';

  // Show loading in overlay immediately
  var reader = document.getElementById('readerOverlay');
  document.getElementById('readerTitle').textContent = '...';
  document.getElementById('readerBody').innerHTML = '<div class="empty-state"><div class="loader"></div><div class="empty-state__title">Loading chapter...</div></div>';
  reader.classList.add('active');
  document.body.style.overflow = 'hidden';

  var htmlUrl = 'books/competitive-exams/' + levelId + '/' + subjectId + '/' + slug + '.html';

  fetch(htmlUrl)
    .then(function(res) {
      if (!res.ok) throw new Error('Not found');
      return res.text();
    })
    .then(function(htmlContent) {
      // Parse the article element to get metadata
      var temp = document.createElement('div');
      temp.innerHTML = htmlContent;
      var article = temp.querySelector('.chapter-data');

      currentBookChapter = {
        slug: slug,
        levelId: levelId,
        subjectId: subjectId,
        nameEn: article ? article.getAttribute('data-name-en') : slug,
        nameHi: article ? article.getAttribute('data-name-hi') : slug,
        num: article ? article.getAttribute('data-num') : '',
        htmlContent: htmlContent
      };

      bookReaderActiveTab = 'content';
      renderReaderUI();
    })
    .catch(function(err) {
      document.getElementById('readerBody').innerHTML = '<div class="empty-state"><div class="empty-state__icon">❌</div>' +
        '<div class="empty-state__title">Failed to load chapter</div>' +
        '<div class="empty-state__desc">' + err.message + '</div></div>';
    });
}

// ====== RENDER READER UI ======
function renderReaderUI() {
  if (!currentBookChapter) return;
  var isHi = bookReaderLang === 'hi';

  // Update header
  document.getElementById('readerTitle').textContent = isHi ? currentBookChapter.nameHi : currentBookChapter.nameEn;
  document.getElementById('readerSubtitle').textContent = 'Chapter ' + currentBookChapter.num + ' • Foundation Math • ' + (isHi ? 'हिंदी' : 'English');

  // SEO: update page title
  document.title = (isHi ? currentBookChapter.nameHi : currentBookChapter.nameEn) + ' — Chapter ' + currentBookChapter.num + ' | Study Station';

  var body = document.getElementById('readerBody');

  // Language toggle
  var langBar = '<div class="book-reader__lang-bar">' +
    '<button class="' + (bookReaderLang === 'hi' ? 'active' : '') + '" onclick="switchBookLang(\'hi\')">हिंदी</button>' +
    '<button class="' + (bookReaderLang === 'en' ? 'active' : '') + '" onclick="switchBookLang(\'en\')">English</button>' +
    '</div>';

  // Tabs
  var tabs = '<div class="book-reader__tabs">' +
    BOOK_TABS.map(function(t) {
      return '<button class="book-reader__tab' + (bookReaderActiveTab === t.id ? ' active' : '') + '" onclick="switchBookTab(\'' + t.id + '\')">' +
        t.icon + ' ' + (isHi ? t.label_hi : t.label_en) + '</button>';
    }).join('') + '</div>';

  // Inject chapter HTML content
  body.innerHTML = langBar + tabs + '<div class="book-reader__content content-rendered" id="chapterContent">' + currentBookChapter.htmlContent + '</div>';

  // Show only active tab + language sections
  updateVisibleSections();
}

// ====== TAB / LANGUAGE SWITCHING (pure DOM toggle) ======
function updateVisibleSections() {
  var sections = document.querySelectorAll('#chapterContent section[data-tab]');
  sections.forEach(function(sec) {
    var tabMatch = sec.getAttribute('data-tab') === bookReaderActiveTab;
    var langMatch = sec.getAttribute('data-lang') === bookReaderLang;
    sec.style.display = (tabMatch && langMatch) ? 'block' : 'none';
  });
  // Stop speech when switching
  stopSpeech();
}

function switchBookTab(tabId) {
  bookReaderActiveTab = tabId;
  // Update tab active state
  document.querySelectorAll('.book-reader__tab').forEach(function(btn) {
    btn.classList.remove('active');
  });
  var tabs = document.querySelectorAll('.book-reader__tab');
  BOOK_TABS.forEach(function(t, i) {
    if (t.id === tabId && tabs[i]) tabs[i].classList.add('active');
  });
  updateVisibleSections();
  // Trigger Mermaid rendering for mind map tab
  if (tabId === 'mindmap') {
    setTimeout(function() {
      try { mermaid.run({ querySelector: '.mermaid' }); } catch(e) { console.log('Mermaid:', e); }
    }, 100);
  }
  document.getElementById('readerBody').scrollTop = 0;
}

function switchBookLang(lang) {
  bookReaderLang = lang;
  localStorage.setItem('language', lang);
  // Update lang bar active state
  document.querySelectorAll('.book-reader__lang-bar button').forEach(function(btn) {
    btn.classList.remove('active');
    if ((lang === 'hi' && btn.textContent === 'हिंदी') || (lang === 'en' && btn.textContent === 'English')) {
      btn.classList.add('active');
    }
  });
  // Update header
  if (currentBookChapter) {
    var isHi = lang === 'hi';
    document.getElementById('readerTitle').textContent = isHi ? currentBookChapter.nameHi : currentBookChapter.nameEn;
    document.getElementById('readerSubtitle').textContent = 'Chapter ' + currentBookChapter.num + ' • Foundation Math • ' + (isHi ? 'हिंदी' : 'English');
  }
  updateVisibleSections();
}

function closeBookReader() {
  var reader = document.getElementById('readerOverlay');
  reader.classList.remove('active');
  document.body.style.overflow = '';
  currentBookChapter = null;
  stopSpeech();
  // Restore page title
  document.title = 'Study Station — Study Smarter, Not Harder';
}

function bookBack() {
  if (bookNavState.subject) {
    openBookLevel(bookNavState.level);
    bookNavState.subject = null;
  } else if (bookNavState.level) {
    openBookCategory('competitive');
    bookNavState.level = null;
  } else {
    renderBookCategories();
  }
}

// ====== MCQ CLICK HANDLER ======
function selectMcqOption(el, qId) {
  var card = document.getElementById('card_' + qId);
  if (!card || card.classList.contains('answered')) return;
  card.classList.add('answered');

  var allOpts = card.querySelectorAll('.mcq-opt');
  var isCorrect = el.getAttribute('data-correct') === '1';

  allOpts.forEach(function(opt) {
    opt.style.pointerEvents = 'none';
    if (opt.getAttribute('data-correct') === '1') {
      opt.classList.add('correct');
    }
    if (opt === el && !isCorrect) {
      opt.classList.add('wrong');
    }
  });

  if (isCorrect) {
    el.insertAdjacentHTML('beforeend', '<span class="mcq-feedback mcq-feedback--correct">✅</span>');
  } else {
    el.insertAdjacentHTML('beforeend', '<span class="mcq-feedback mcq-feedback--wrong">❌</span>');
  }

  var ansEl = document.getElementById('ans_' + qId);
  if (ansEl) {
    if(ansEl.tagName.toLowerCase() === 'details') {
        ansEl.open = true;
    } else {
        ansEl.style.display = 'block';
    }
    ansEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

// ====== 🔊 TEXT-TO-SPEECH (SPEAKER) ======
var speechState = { speaking: false, paused: false };

function speakContent() {
  if (speechSynthesis.speaking && !speechSynthesis.paused) {
    // Already speaking — pause
    speechSynthesis.pause();
    speechState.paused = true;
    updateSpeakerUI();
    return;
  }
  if (speechSynthesis.paused) {
    // Resume
    speechSynthesis.resume();
    speechState.paused = false;
    updateSpeakerUI();
    return;
  }

  // Start new speech
  var activeSection = document.querySelector('#chapterContent section[data-tab][style*="block"]');
  if (!activeSection) return;

  var text = activeSection.innerText;
  if (!text || text.length < 10) return;

  // Split into chunks of ~200 chars for smoother playback
  var chunks = splitTextForSpeech(text);
  speakChunks(chunks, 0);
}

function splitTextForSpeech(text) {
  var sentences = text.split(/(?<=[।\.!\?])\s+/);
  var chunks = [];
  var current = '';
  sentences.forEach(function(s) {
    if ((current + ' ' + s).length > 300 && current) {
      chunks.push(current.trim());
      current = s;
    } else {
      current += ' ' + s;
    }
  });
  if (current.trim()) chunks.push(current.trim());
  return chunks;
}

function speakChunks(chunks, index) {
  if (index >= chunks.length) {
    speechState.speaking = false;
    updateSpeakerUI();
    return;
  }

  var utterance = new SpeechSynthesisUtterance(chunks[index]);
  utterance.lang = bookReaderLang === 'hi' ? 'hi-IN' : 'en-US';
  utterance.rate = parseFloat(localStorage.getItem('speechRate') || '1.0');

  utterance.onend = function() {
    speakChunks(chunks, index + 1);
  };
  utterance.onerror = function() {
    speechState.speaking = false;
    updateSpeakerUI();
  };

  speechState.speaking = true;
  updateSpeakerUI();
  speechSynthesis.speak(utterance);
}

function pauseSpeech() {
  if (speechSynthesis.speaking) {
    speechSynthesis.pause();
    speechState.paused = true;
    updateSpeakerUI();
  }
}

function stopSpeech() {
  speechSynthesis.cancel();
  speechState.speaking = false;
  speechState.paused = false;
  updateSpeakerUI();
}

function setSpeechRate(rate) {
  localStorage.setItem('speechRate', rate);
  // Show feedback
  var btn = document.getElementById('speedBtn');
  if (btn) btn.textContent = rate + 'x';
}

function cycleSpeechRate() {
  var rates = [0.8, 1.0, 1.25, 1.5];
  var current = parseFloat(localStorage.getItem('speechRate') || '1.0');
  var idx = rates.indexOf(current);
  var next = rates[(idx + 1) % rates.length];
  setSpeechRate(next);
}

function updateSpeakerUI() {
  var playBtn = document.getElementById('speakerPlayBtn');
  var pauseBtn = document.getElementById('speakerPauseBtn');
  var stopBtn = document.getElementById('speakerStopBtn');
  if (!playBtn) return;

  if (speechState.speaking && !speechState.paused) {
    playBtn.style.display = 'none';
    pauseBtn.style.display = 'inline-flex';
    stopBtn.style.display = 'inline-flex';
  } else if (speechState.paused) {
    playBtn.style.display = 'inline-flex';
    playBtn.innerHTML = '<ion-icon name="play"></ion-icon>';
    pauseBtn.style.display = 'none';
    stopBtn.style.display = 'inline-flex';
  } else {
    playBtn.style.display = 'inline-flex';
    playBtn.innerHTML = '<ion-icon name="volume-high-outline"></ion-icon>';
    pauseBtn.style.display = 'none';
    stopBtn.style.display = 'none';
  }
}
