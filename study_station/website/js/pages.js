/**
 * pages.js — Page-specific rendering logic
 * Depends on: data.js, app.js (navigate, showToast, state vars)
 */

// ====== CLASSES PAGE ======
function renderClassesGrid() {
  var grid = document.getElementById('classesGrid');
  grid.innerHTML = CLASSES_DATA.map(function(c) {
    return '<div class="card class-card fade-in" onclick="goToClass(' + c.id + ')">' +
      '<div class="class-card__icon">' + c.emoji + '</div>' +
      '<div class="class-card__label">' + c.name + '</div>' +
      '<div class="class-card__sub">' + c.subjects + ' Subjects</div></div>';
  }).join('');
  requestAnimationFrame(function() {
    grid.querySelectorAll('.fade-in').forEach(function(el, i) {
      setTimeout(function() { el.classList.add('visible'); }, i * 50);
    });
  });
}

function goToClass(classId) {
  navigate('study');
  selectStudyClass(classId);
}

// ====== STUDY PAGE ======
function renderStudyClasses() {
  currentStudyClass = null;
  currentStudySubject = null;
  document.getElementById('studyClassSelect').style.display = 'block';
  document.getElementById('studySubjectSelect').style.display = 'none';
  document.getElementById('studyChapterSelect').style.display = 'none';
  document.getElementById('studyBackBtn').style.display = 'none';
  document.getElementById('studyBreadcrumbCurrent').textContent = 'Study Materials';
  document.getElementById('studyPageTitle').textContent = 'Study Materials';

  var grid = document.getElementById('studyClassGrid');
  grid.innerHTML = CLASSES_DATA.map(function(c) {
    return '<div class="card class-card" onclick="selectStudyClass(' + c.id + ')">' +
      '<div class="class-card__icon">' + c.emoji + '</div>' +
      '<div class="class-card__label">' + c.name + '</div>' +
      '<div class="class-card__sub">' + c.subjects + ' Subjects</div></div>';
  }).join('');
}

function selectStudyClass(classId) {
  currentStudyClass = classId;
  currentStudySubject = null;
  document.getElementById('studyClassSelect').style.display = 'none';
  document.getElementById('studySubjectSelect').style.display = 'block';
  document.getElementById('studyChapterSelect').style.display = 'none';
  document.getElementById('studyBackBtn').style.display = 'inline-flex';
  document.getElementById('studyBreadcrumbCurrent').textContent = 'Class ' + classId;
  document.getElementById('studyPageTitle').textContent = 'Class ' + classId + ' — Subjects';
  document.getElementById('studySubjectSubtitle').textContent = 'Select a subject for Class ' + classId + ':';

  var subs = SUBJECTS_DB[classId] || SUBJECTS_DB[10];
  var grid = document.getElementById('studySubjectGrid');
  grid.innerHTML = subs.map(function(s) {
    return '<div class="card subject-card" onclick="selectStudySubject(\'' + s.name + '\',' + s.chapters + ')">' +
      '<div class="subject-card__icon">' + s.icon + '</div>' +
      '<div class="subject-card__info"><div class="subject-card__name">' + s.name + '</div>' +
      '<div class="subject-card__meta">' + s.chapters + ' Chapters</div></div>' +
      '<ion-icon name="chevron-forward-outline" style="color:var(--text-secondary)"></ion-icon></div>';
  }).join('');
}

function selectStudySubject(subName, chapCount) {
  currentStudySubject = subName;
  document.getElementById('studySubjectSelect').style.display = 'none';
  document.getElementById('studyChapterSelect').style.display = 'block';
  document.getElementById('studyBreadcrumbCurrent').textContent = subName;
  document.getElementById('studyPageTitle').textContent = subName;
  document.getElementById('studyChapterSubtitle').textContent = 'Chapters in ' + subName + ':';

  var chapters = CHAPTERS_DB[subName] || CHAPTERS_DB['Mathematics'];
  var list = document.getElementById('studyChapterList');
  list.innerHTML = chapters.map(function(ch, i) {
    var diffBadge = ch.difficulty === 'easy' ? '<span class="badge badge--success">Easy</span>' :
      ch.difficulty === 'medium' ? '<span class="badge badge--warning">Medium</span>' :
      '<span class="badge badge--danger">Hard</span>';
    return '<div class="chapter-item" onclick="openChapter(\'' + ch.name.replace(/'/g, "\\'") + '\')">' +
      '<div class="chapter-num">' + (i + 1) + '</div>' +
      '<div class="chapter-name">' + ch.name + '</div>' +
      '<div class="chapter-status">' + diffBadge + '</div></div>';
  }).join('');
}

function studyBack() {
  if (currentStudySubject) {
    document.getElementById('studyChapterSelect').style.display = 'none';
    document.getElementById('studySubjectSelect').style.display = 'block';
    document.getElementById('studyBreadcrumbCurrent').textContent = 'Class ' + currentStudyClass;
    document.getElementById('studyPageTitle').textContent = 'Class ' + currentStudyClass + ' — Subjects';
    currentStudySubject = null;
  } else if (currentStudyClass) {
    document.getElementById('studySubjectSelect').style.display = 'none';
    document.getElementById('studyClassSelect').style.display = 'block';
    document.getElementById('studyBreadcrumbCurrent').textContent = 'Study Materials';
    document.getElementById('studyPageTitle').textContent = 'Study Materials';
    document.getElementById('studyBackBtn').style.display = 'none';
    currentStudyClass = null;
  }
}

function openChapter(chName) {
  var reader = document.getElementById('readerOverlay');
  document.getElementById('readerTitle').textContent = chName;
  document.getElementById('readerSubtitle').textContent = 'Class ' + currentStudyClass + ' • ' + currentStudySubject;

  var body = document.getElementById('readerBody');
  body.innerHTML = '<h2>' + chName + '</h2>' +
    '<p>This chapter covers the fundamental concepts and principles of ' + chName + '. Understanding this topic is essential for building a strong foundation in ' + currentStudySubject + '.</p>' +
    '<h3 style="margin:1.5rem 0 0.75rem;font-size:1.25rem;">Key Concepts</h3>' +
    '<ul><li>Introduction and definition of core concepts</li><li>Detailed explanation with examples</li><li>Important formulas and theorems</li><li>Solved examples from previous year papers</li><li>Practice problems with step-by-step solutions</li><li>Summary and quick revision notes</li></ul>' +
    '<h3 style="margin:1.5rem 0 0.75rem;font-size:1.25rem;">Important Formulas</h3>' +
    '<p>The key formulas and equations you need to remember for this chapter are highlighted below. Make sure to practice applying them in different contexts.</p>' +
    '<h3 style="margin:1.5rem 0 0.75rem;font-size:1.25rem;">Practice Tips</h3>' +
    '<p>After studying this chapter, head over to the Practice section to test your understanding with MCQs. Use the AI Chat Tutor if you have any doubts.</p>' +
    '<div style="margin-top:2rem;padding:1.5rem;background:var(--accent-surface);border-radius:var(--radius-lg);border:1px solid var(--accent);">' +
    '<div style="font-weight:700;margin-bottom:0.5rem;">💡 AI Tutor Tip</div>' +
    '<p style="margin:0;font-size:0.9rem;">Click the "AI Chat" button in the toolbar above to ask questions about this chapter. The AI tutor can explain concepts in Hindi or English!</p></div>';

  reader.classList.add('active');
  document.body.style.overflow = 'hidden';
  showToast('Chapter loaded: ' + chName, 'success');
}

function closeReader() {
  document.getElementById('readerOverlay').classList.remove('active');
  document.body.style.overflow = '';
}

// ====== PRACTICE PAGE ======
function getSubjectEmoji(subject) {
  var emojis = { 'Mathematics': '📐', 'Science': '🔬', 'Physics': '⚡', 'Chemistry': '🧪', 'English': '📖' };
  return emojis[subject] || '📚';
}

function renderPracticeSubjects() {
  document.getElementById('practiceHome').style.display = 'block';
  document.getElementById('practiceQuiz').style.display = 'none';

  var grid = document.getElementById('practiceSubjectGrid');
  grid.innerHTML = MCQ_DATA.map(function(d) {
    return '<div class="card subject-card" onclick="startQuiz(\'' + d.subject + '\')">' +
      '<div class="subject-card__icon">' + getSubjectEmoji(d.subject) + '</div>' +
      '<div class="subject-card__info"><div class="subject-card__name">' + d.subject + '</div>' +
      '<div class="subject-card__meta">' + d.questions.length + ' Questions • MCQ Practice</div></div>' +
      '<button class="btn btn--sm btn--primary">Start</button></div>';
  }).join('');
}

function filterPracticeSubjects() {
  var q = document.getElementById('practiceSearch').value.toLowerCase();
  document.querySelectorAll('#practiceSubjectGrid .subject-card').forEach(function(card) {
    var name = card.querySelector('.subject-card__name').textContent.toLowerCase();
    card.style.display = name.includes(q) ? '' : 'none';
  });
}

function startQuiz(subject) {
  var data = MCQ_DATA.find(function(d) { return d.subject === subject; });
  if (!data) return;
  currentQuizData = data;
  currentQuizIndex = 0;
  quizScore = 0;
  quizAnswered = false;
  quizUserData = [];
  quizSeconds = 0;

  document.getElementById('practiceHome').style.display = 'none';
  document.getElementById('practiceQuiz').style.display = 'block';
  document.getElementById('practiceQuizSubject').textContent = subject + ' Quiz';

  if (quizTimer) clearInterval(quizTimer);
  quizTimer = setInterval(function() { quizSeconds++; }, 1000);
  renderQuizQuestion();
}

function renderQuizQuestion() {
  if (currentQuizIndex >= currentQuizData.questions.length) { showQuizResults(); return; }
  quizAnswered = false;
  var q = currentQuizData.questions[currentQuizIndex];
  var total = currentQuizData.questions.length;
  var progress = ((currentQuizIndex) / total) * 100;
  var minutes = Math.floor(quizSeconds / 60);
  var secs = quizSeconds % 60;
  var letters = ['A', 'B', 'C', 'D'];

  var container = document.getElementById('quizContainer');
  container.innerHTML =
    '<div class="quiz-progress"><div class="quiz-progress-bar" style="width:' + progress + '%"></div></div>' +
    '<div class="quiz-info"><span>Question ' + (currentQuizIndex + 1) + ' of ' + total + '</span>' +
    '<span><ion-icon name="timer-outline" style="vertical-align:middle;"></ion-icon> ' + String(minutes).padStart(2, '0') + ':' + String(secs).padStart(2, '0') + '</span></div>' +
    '<div class="quiz-question">' + q.q + '</div>' +
    '<div class="quiz-options" id="quizOptions">' +
    q.options.map(function(opt, i) {
      return '<div class="quiz-option" data-idx="' + i + '" onclick="selectAnswer(' + i + ')">' +
        '<div class="quiz-option__letter">' + letters[i] + '</div><span>' + opt + '</span></div>';
    }).join('') + '</div>' +
    '<div id="quizExplanation" style="display:none;"></div>' +
    '<div class="quiz-actions" id="quizActions"><button class="btn btn--primary" id="quizNextBtn" onclick="nextQuestion()" style="display:none;">' +
    (currentQuizIndex < total - 1 ? 'Next Question' : 'View Results') +
    ' <ion-icon name="arrow-forward-outline"></ion-icon></button></div>';
}

function selectAnswer(idx) {
  if (quizAnswered) return;
  quizAnswered = true;
  var q = currentQuizData.questions[currentQuizIndex];
  var correct = q.correct;
  quizUserData.push({ questionIdx: currentQuizIndex, selected: idx, correct: idx === correct });
  if (idx === correct) quizScore++;

  document.querySelectorAll('#quizOptions .quiz-option').forEach(function(el) {
    var i = parseInt(el.getAttribute('data-idx'));
    if (i === correct) el.classList.add('correct');
    else if (i === idx && i !== correct) el.classList.add('wrong');
    el.style.pointerEvents = 'none';
  });

  var expl = document.getElementById('quizExplanation');
  expl.style.display = 'block';
  expl.className = 'quiz-explanation';
  expl.innerHTML = '<strong>Explanation:</strong> ' + q.explanation;
  document.getElementById('quizNextBtn').style.display = 'inline-flex';
}

function nextQuestion() { currentQuizIndex++; renderQuizQuestion(); }

function showQuizResults() {
  if (quizTimer) clearInterval(quizTimer);
  var total = currentQuizData.questions.length;
  var pct = Math.round((quizScore / total) * 100);
  var minutes = Math.floor(quizSeconds / 60);
  var secs = quizSeconds % 60;

  var container = document.getElementById('quizContainer');
  var badgeClass = pct >= 80 ? 'success' : pct >= 50 ? 'warning' : 'danger';
  var badgeText = pct >= 80 ? '🎉 Excellent!' : pct >= 50 ? '👍 Good Job!' : '💪 Keep Practicing!';

  var html = '<div class="score-card">' +
    '<div class="badge badge--' + badgeClass + '" style="margin-bottom:1.5rem;font-size:0.85rem;">' + badgeText + '</div>' +
    '<div class="score-circle" style="--score-pct:' + pct + '"><div class="score-circle-inner">' +
    '<div class="score-pct">' + pct + '%</div><div class="score-label">Score</div></div></div>' +
    '<div style="display:flex;justify-content:center;gap:2rem;margin-bottom:2rem;flex-wrap:wrap;">' +
    '<div><div style="font-size:1.25rem;font-weight:800;color:var(--success);">' + quizScore + '</div><div style="font-size:0.8rem;color:var(--text-secondary);">Correct</div></div>' +
    '<div><div style="font-size:1.25rem;font-weight:800;color:var(--danger);">' + (total - quizScore) + '</div><div style="font-size:0.8rem;color:var(--text-secondary);">Wrong</div></div>' +
    '<div><div style="font-size:1.25rem;font-weight:800;">' + String(minutes).padStart(2, '0') + ':' + String(secs).padStart(2, '0') + '</div><div style="font-size:0.8rem;color:var(--text-secondary);">Time Taken</div></div></div>';

  html += '<div style="text-align:left;margin-top:1.5rem;"><h4 style="margin-bottom:1rem;">Question Review</h4>';
  quizUserData.forEach(function(u) {
    var q = currentQuizData.questions[u.questionIdx];
    html += '<div style="display:flex;align-items:center;gap:0.75rem;padding:0.75rem;background:var(--bg-tertiary);border-radius:var(--radius-md);margin-bottom:0.5rem;">' +
      '<div style="width:28px;height:28px;border-radius:50%;background:' + (u.correct ? 'var(--success)' : 'var(--danger)') + ';display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.75rem;">' +
      '<ion-icon name="' + (u.correct ? 'checkmark-sharp' : 'close-sharp') + '"></ion-icon></div>' +
      '<span style="flex:1;font-size:0.9rem;">' + q.q.substring(0, 50) + '...</span></div>';
  });
  html += '</div>';

  html += '<div style="display:flex;gap:1rem;justify-content:center;margin-top:2rem;flex-wrap:wrap;">' +
    '<button class="btn btn--primary" onclick="startQuiz(\'' + currentQuizData.subject + '\')"><ion-icon name="refresh-outline"></ion-icon> Retry Quiz</button>' +
    '<button class="btn btn--secondary" onclick="exitPractice()"><ion-icon name="grid-outline"></ion-icon> All Subjects</button></div></div>';

  container.innerHTML = html;
}

function exitPractice() {
  if (quizTimer) clearInterval(quizTimer);
  currentQuizData = null;
  renderPracticeSubjects();
}

// ====== BOOKS PAGE ======
// Delegates to book-reader.js for deep category navigation
function renderBooks() {
  if (typeof renderBookCategories === 'function') {
    renderBookCategories();
  }
}

// ====== JOBS PAGE ======
function getJobEmoji(cat) {
  var emojis = { 'ssc': '🏛️', 'banking': '🏦', 'railway': '🚂', 'govt': '🇮🇳' };
  return emojis[cat] || '💼';
}

function daysLeftBadge(deadline) {
  if (!deadline) return '';
  var d = null;
  var m = deadline.match(/(\d{1,2})\s*[-\/.]\s*(\d{1,2})\s*[-\/.]\s*(\d{2,4})/);
  if (m) {
    var y = parseInt(m[3], 10); if (y < 100) y += 2000;
    d = new Date(y, parseInt(m[2], 10) - 1, parseInt(m[1], 10));
  } else {
    var p = Date.parse(deadline);
    if (!isNaN(p)) d = new Date(p);
  }
  if (!d) return '';
  var diff = Math.ceil((d - new Date()) / 86400000);
  if (diff < 0) return '<span class="badge" style="background:rgba(239,68,68,0.15);color:#ef4444;">Expired</span>';
  if (diff === 0) return '<span class="badge badge--warning">⏳ Last day today!</span>';
  if (diff <= 10) return '<span class="badge badge--warning">⏳ ' + diff + ' days left</span>';
  return '';
}

function renderJobs() {
  var filtered = JOBS_DATA.filter(function(j) {
    if (j.type !== currentJobTab) return false;
    if (currentJobCategory !== 'all' && j.category !== currentJobCategory) return false;
    var search = document.getElementById('jobSearch') ? document.getElementById('jobSearch').value.toLowerCase() : '';
    if (search && j.title.toLowerCase().indexOf(search) === -1 && (j.org || '').toLowerCase().indexOf(search) === -1) return false;
    return true;
  });

  var grid = document.getElementById('jobsGrid');
  if (filtered.length === 0) {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><div class="empty-state__icon">📭</div><div class="empty-state__title">No Jobs Found</div><div class="empty-state__desc">Try changing the filters or search term.</div></div>';
    return;
  }

  grid.innerHTML = filtered.map(function(job) {
    var catBadge = job.category === 'ssc' ? '<span class="badge badge--info">SSC</span>' :
      job.category === 'banking' ? '<span class="badge badge--warning">Banking</span>' :
      job.category === 'railway' ? '<span class="badge badge--success">Railway</span>' :
      '<span class="badge badge--new">Govt</span>';
    var typeBadge = job.type === 'latest' ? '<span class="badge badge--new">📌 Latest</span>' :
      job.type === 'results' ? '<span class="badge badge--success">✅ Result</span>' :
      job.type === 'admit' ? '<span class="badge badge--warning">🎫 Admit Card</span>' :
      '<span class="badge badge--info">📝 Answer Key</span>';

    // Only show meta rows for data we actually have — never invent values
    var meta = '';
    if (job.vacancies) meta += '<div class="job-meta"><ion-icon name="people-outline"></ion-icon> ' + job.vacancies + ' Vacancies</div>';
    if (job.deadline) meta += '<div class="job-meta"><ion-icon name="calendar-outline"></ion-icon> Last Date: ' + job.deadline + '</div>';
    if (job.eligibility) meta += '<div class="job-meta"><ion-icon name="school-outline"></ion-icon> ' + job.eligibility + '</div>';
    if (!meta) meta = '<div class="job-meta"><ion-icon name="document-text-outline"></ion-icon> See official notification for details</div>';

    return '<div class="card job-card">' +
      '<div class="job-card__header"><div class="job-card__logo">' + getJobEmoji(job.category) + '</div>' +
      '<div style="flex:1;"><div class="job-card__title">' + job.title + '</div>' + (job.org ? '<div class="job-card__org">' + job.org + '</div>' : '') + '</div>' +
      (job.isNew ? '<span class="badge badge--new">NEW</span>' : '') + '</div>' +
      '<div style="display:flex;gap:0.5rem;flex-wrap:wrap;">' + catBadge + typeBadge + daysLeftBadge(job.deadline) + '</div>' +
      '<div class="job-card__meta-grid">' + meta + '</div>' +
      '<div class="job-card__actions">' +
      (job.url ? '<a class="btn btn--sm btn--primary" href="' + job.url + '"><ion-icon name="reader-outline"></ion-icon> Full Details</a>' : '') +
      (job.official ? '<a class="btn btn--sm btn--secondary" href="' + job.official + '" target="_blank" rel="noopener nofollow"><ion-icon name="open-outline"></ion-icon> Official Link</a>' : '') +
      '</div></div>';
  }).join('');
}

function switchJobTab(tab, btn) {
  currentJobTab = tab;
  document.querySelectorAll('#jobTabs .tab').forEach(function(t) { t.classList.remove('active'); });
  btn.classList.add('active');
  renderJobs();
}

function filterJobCategory(cat, btn) {
  currentJobCategory = cat;
  document.querySelectorAll('#jobCategoryFilters .filter-chip').forEach(function(c) { c.classList.remove('active'); });
  btn.classList.add('active');
  renderJobs();
}

function filterJobs() { renderJobs(); }

// ====== PYQ PAGE ======
function renderPyq() {
  var papers = PYQ_DATA[currentPyqTab] || [];
  var search = document.getElementById('pyqSearch') ? document.getElementById('pyqSearch').value.toLowerCase() : '';
  var filtered = search ? papers.filter(function(p) { return p.title.toLowerCase().includes(search) || p.subject.toLowerCase().includes(search); }) : papers;

  var grid = document.getElementById('pyqGrid');
  grid.innerHTML = filtered.map(function(p) {
    return '<div class="card pyq-card">' +
      '<div class="pyq-card__header"><div class="pyq-card__icon">📄</div>' +
      '<div><div class="pyq-card__title">' + p.title + '</div><div class="pyq-card__exam">' + p.exam + ' • ' + p.year + ' • ' + p.subject + '</div></div></div>' +
      '<div class="pyq-card__actions">' +
      (p.q_url ? '<a class="btn btn--sm btn--primary" href="' + p.q_url + '" target="_blank" rel="noopener"><ion-icon name="download-outline"></ion-icon> Question Paper</a>'
               : '<button class="btn btn--sm btn--ghost" disabled>Question Paper — soon</button>') +
      (p.a_url ? '<a class="btn btn--sm btn--secondary" href="' + p.a_url + '" target="_blank" rel="noopener"><ion-icon name="document-outline"></ion-icon> Answer Key</a>'
               : '') +
      '</div></div>';
  }).join('');

  if (filtered.length === 0) {
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><div class="empty-state__icon">🗂️</div><div class="empty-state__title">PYQ Papers Coming Soon</div><div class="empty-state__desc">असली question papers जल्द जोड़े जा रहे हैं — हम नकली downloads नहीं दिखाते।</div></div>';
  }
}

function switchPyqTab(tab, btn) {
  currentPyqTab = tab;
  document.querySelectorAll('#pyqTabs .tab').forEach(function(t) { t.classList.remove('active'); });
  btn.classList.add('active');
  renderPyq();
}

function filterPyq() { renderPyq(); }
