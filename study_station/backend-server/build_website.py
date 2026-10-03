import os
import re
from flask import Flask, render_template_string
from app import app
from models import db, StudyContent, PracticeQuestion, JobAlert
import shutil

# Public site URL — set env var SITE_URL when deploying to the VPS.
# Drives canonical tags, Open Graph URLs and the sitemap. Empty until deploy so
# we never emit a canonical pointing at the wrong (undecided) domain.
SITE_URL = os.environ.get('SITE_URL', '').rstrip('/')


def canonical_for(rel_path):
    """Return absolute canonical URL for a site-relative path, or None if SITE_URL unset."""
    if not SITE_URL:
        return None
    return f"{SITE_URL}/{rel_path.lstrip('/')}"


# The NCERT library was cleaned by clean_mock_ncert.py: populate_all_pdfs.py's
# run_mock() had copied ONE placeholder PDF into every class/subject/chapter
# (1458 fakes), which we deleted along with the 1179 empty rows they created.
# What remains is genuine — real downloaded PDFs and real notes — so pages are
# now indexed individually, based on whether they actually carry content.
# Never index a page whose content is missing: thin pages at scale would drag
# the whole domain down.

def _nonempty(value):
    return bool((value or '').strip())


def has_ai_notes(chapter):
    """True when the chapter carries real notes text."""
    return _nonempty(chapter.content_text)


def has_pdf(chapter):
    """True when the chapter's PDF actually exists on disk.

    pdf_url alone is not enough — it is a relative string that can outlive the
    file it points at (exactly what the mock cleanup left behind).
    """
    if not _nonempty(chapter.pdf_url):
        return False
    path = os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'website')),
        'books', 'ncert', f'class-{chapter.class_level}', 'books',
        (chapter.subject or '').lower().replace(' ', '_'), 'pdfs',
        f'chapter-{chapter.chapter_number}.pdf')
    return os.path.exists(path)


def parse_markdown(text):
    if not text: return 'No AI notes available yet.'
    content = re.sub(r'^### (.*$)', r'<h3 class="text-xl font-bold mt-4 mb-2 text-indigo-700">\1</h3>', text, flags=re.MULTILINE)
    content = re.sub(r'^## (.*$)', r'<h2 class="text-2xl font-bold mt-5 mb-3 text-indigo-800">\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.*$)', r'<h1 class="text-3xl font-bold mt-6 mb-4 text-indigo-900">\1</h1>', content, flags=re.MULTILINE)
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
    content = re.sub(r'\n\n', r'</p><p class="mb-4">', content)
    content = re.sub(r'\n', r'<br>', content)
    if not content.strip().startswith('<h'):
        content = '<p class="mb-4">' + content + '</p>'
    return content

MONTHS_RE = (r'Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
             r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?')
MONTH_NUM = {m: i + 1 for i, m in enumerate(
    ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}


def parse_date_str(s):
    """Parse '30-05-2026', '30/05/2026', '12 May 2026', 'May 12, 2026' → datetime or None."""
    from datetime import datetime
    if not s:
        return None
    s = s.strip()
    m = re.search(r'(\d{1,2})\s*[-/.]\s*(\d{1,2})\s*[-/.]\s*(\d{2,4})', s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        try:
            return datetime(y, mo, d)
        except ValueError:
            return None
    m = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(' + MONTHS_RE + r')\.?,?\s+(\d{4})', s, re.I)
    if m:
        try:
            return datetime(int(m.group(3)), MONTH_NUM[m.group(2)[:3].lower()], int(m.group(1)))
        except (ValueError, KeyError):
            return None
    m = re.search(r'(' + MONTHS_RE + r')\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})', s, re.I)
    if m:
        try:
            return datetime(int(m.group(3)), MONTH_NUM[m.group(1)[:3].lower()], int(m.group(2)))
        except (ValueError, KeyError):
            return None
    return None


def is_job_expired(job, now=None, stale_days=90):
    """A job is expired if its last date has passed, or (for LATEST_JOB with no
    known last date) if it was scraped more than `stale_days` ago."""
    from datetime import datetime, timedelta
    now = now or datetime.utcnow()
    last = parse_date_str(job.last_date)
    if last:
        return last < now - timedelta(days=1)
    if job.job_type == 'LATEST_JOB' and job.created_at:
        return job.created_at < now - timedelta(days=stale_days)
    return False


def export_jobs_js(jobs, website_dir, limit=200):
    """Write real job data from the DB into website/js/jobs_data.js for the SPA.

    Only real, extracted values are exported — missing fields stay null and the
    frontend shows 'See official notification' instead of invented data.
    """
    import json
    from datetime import datetime, timedelta

    type_map = {
        'LATEST_JOB': 'latest', 'RESULT': 'results',
        'ADMIT_CARD': 'admit', 'ANSWER_KEY': 'answer', 'SYLLABUS': 'latest',
    }
    chip_map = {'SSC': 'ssc', 'BANKING': 'banking', 'RAILWAY': 'railway'}
    new_cutoff = datetime.utcnow() - timedelta(days=5)

    out = []
    for job in jobs:
        if len(out) >= limit:
            break
        if is_job_expired(job):
            continue
        out.append({
            'title': job.title,
            'org': job.organization,
            'vacancies': job.vacancies,
            'deadline': job.last_date,
            'eligibility': job.eligibility,
            'type': type_map.get(job.job_type, 'latest'),
            'category': chip_map.get(job.category or '', 'govt'),
            'isNew': bool(job.created_at and job.created_at > new_cutoff),
            'url': f'jobs/job_{job.id}.html',
            'official': job.official_url or job.application_url,
        })

    js_path = os.path.join(website_dir, 'js', 'jobs_data.js')
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write('/* AUTO-GENERATED by build_website.py — do not edit by hand. */\n')
        f.write('var JOBS_DATA = ' + json.dumps(out, ensure_ascii=False, indent=1) + ';\n')
    print(f"Generated js/jobs_data.js ({len(out)} real jobs)")


def build_ssg():
    basedir = os.path.abspath(os.path.dirname(__name__))
    website_dir = os.path.abspath(os.path.join(basedir, '../website'))
    templates_dir = os.path.join(basedir, 'templates', 'ssg')
    
    # Copy JS Assets
    frontend_js_src = os.path.join(basedir, 'static', 'js', 'frontend')
    frontend_js_dest = os.path.join(website_dir, 'js', 'frontend')
    os.makedirs(frontend_js_dest, exist_ok=True)
    if os.path.exists(frontend_js_src):
        for f in os.listdir(frontend_js_src):
            if f.endswith('.js'):
                shutil.copy2(os.path.join(frontend_js_src, f), os.path.join(frontend_js_dest, f))

    # Site-relative paths of pages that carry real content — the only ones that
    # go into the sitemap. Filled while generating NCERT pages below.
    indexable_pages = []

    with app.app_context():
        # Get all distinct classes
        classes_tuples = db.session.query(StudyContent.class_level).distinct().order_by(StudyContent.class_level).all()
        classes = [c[0] for c in classes_tuples if c[0] is not None]
        
        # 1. Generate website/classes.html
        html = app.jinja_env.get_template('ssg/classes.html').render(
            title="All Classes",
            meta_description="Browse study material and NCERT books for Classes 1 to 12.",
            root_path="./",
            canonical_url=canonical_for('classes.html'),
            classes=classes
        )
        with open(os.path.join(website_dir, 'classes.html'), 'w', encoding='utf-8') as f:
            f.write(html)
            
        print("Generated classes.html")
        
        for c_level in classes:
            class_folder = os.path.join(website_dir, 'books', 'ncert', f'class-{c_level}')
            os.makedirs(class_folder, exist_ok=True)
            
            # Get subjects for this class
            from sqlalchemy import func
            # Group by subject ONLY. Grouping by icon too would list a subject
            # twice whenever its rows carry different icons (Class 5 Maths had
            # both 📐 and 📚), building the same pages twice and putting
            # duplicate URLs in the sitemap.
            subjects_data = db.session.query(
                StudyContent.subject,
                func.min(StudyContent.subject_icon).label('icon'),
                func.count(StudyContent.id).label('count')
            ).filter_by(class_level=c_level).group_by(StudyContent.subject).all()

            subjects = []
            for s in subjects_data:
                subjects.append({
                    'subject': s.subject,
                    'icon': s.icon or '📚',
                    'count': s.count
                })
            
            # 2. Generate website/class-X/index.html
            html = app.jinja_env.get_template('ssg/class_index.html').render(
                title=f"Class {c_level} Subjects",
                meta_description=f"Subjects for Class {c_level}",
                root_path="../../../",
                canonical_url=canonical_for(f'books/ncert/class-{c_level}/index.html'),
                class_level=c_level,
                subjects=subjects
            )
            with open(os.path.join(class_folder, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)
            # Every surviving subject has real content (clean_mock_ncert.py
            # dropped the rest), so these hubs are worth indexing.
            indexable_pages.append(f'books/ncert/class-{c_level}/index.html')
                
            books_folder = os.path.join(class_folder, 'books')
            os.makedirs(books_folder, exist_ok=True)
            
            for s in subjects:
                subj_name_safe = s['subject'].lower().replace(' ', '_')
                subj_folder = os.path.join(books_folder, subj_name_safe)
                
                os.makedirs(os.path.join(subj_folder, 'main_pdf'), exist_ok=True)
                os.makedirs(os.path.join(subj_folder, 'ai_notes'), exist_ok=True)
                os.makedirs(os.path.join(subj_folder, 'solutions'), exist_ok=True)
                
                chapters = StudyContent.query.filter_by(class_level=c_level, subject=s['subject']).order_by(StudyContent.chapter_number).all()
                
                # 3. Generate website/class-X/books/subj/index.html
                html = app.jinja_env.get_template('ssg/subject_index.html').render(
                    title=f"Class {c_level} {s['subject']} Chapters",
                    meta_description=f"Class {c_level} {s['subject']} — chapter-wise NCERT book PDFs and notes.",
                    root_path="../../../../../../",
                    canonical_url=canonical_for(f'books/ncert/class-{c_level}/books/{subj_name_safe}/index.html'),
                    class_level=c_level,
                    subject=s['subject'],
                    chapters=chapters
                )
                with open(os.path.join(subj_folder, 'index.html'), 'w', encoding='utf-8') as f:
                    f.write(html)
                indexable_pages.append(
                    f'books/ncert/class-{c_level}/books/{subj_name_safe}/index.html')
                
                # 4. Generate Chapter Pages
                #    A page is indexable ONLY if it carries real content. Empty
                #    placeholder pages stay reachable but get noindex and are
                #    kept out of the sitemap.
                for chapter in chapters:
                    root_path = "../../../../../../../"
                    subj_rel = f"books/ncert/class-{c_level}/books/{subj_name_safe}"

                    # PDF Page
                    pdf_rel = f"{subj_rel}/main_pdf/chapter-{chapter.chapter_number}.html"
                    pdf_ok = has_pdf(chapter)
                    html_pdf = app.jinja_env.get_template('ssg/pdf_page.html').render(
                        title=f"Ch {chapter.chapter_number} PDF - {s['subject']}",
                        meta_description=f"Class {c_level} {s['subject']} Chapter {chapter.chapter_number} original NCERT book PDF.",
                        root_path=root_path,
                        canonical_url=canonical_for(pdf_rel) if pdf_ok else None,
                        noindex=not pdf_ok,
                        chapter=chapter
                    )
                    with open(os.path.join(subj_folder, 'main_pdf', f'chapter-{chapter.chapter_number}.html'), 'w', encoding='utf-8') as f:
                        f.write(html_pdf)
                    if pdf_ok:
                        indexable_pages.append(pdf_rel)

                    # AI Notes Page
                    ai_rel = f"{subj_rel}/ai_notes/chapter-{chapter.chapter_number}.html"
                    ai_ok = has_ai_notes(chapter)
                    html_ai = app.jinja_env.get_template('ssg/ai_page.html').render(
                        title=f"Ch {chapter.chapter_number} AI Notes - {s['subject']}",
                        meta_description=f"Class {c_level} {s['subject']} Chapter {chapter.chapter_number} notes and summary.",
                        root_path=root_path,
                        canonical_url=canonical_for(ai_rel) if ai_ok else None,
                        noindex=not ai_ok,
                        chapter=chapter,
                        parsed_notes=parse_markdown(chapter.content_text)
                    )
                    with open(os.path.join(subj_folder, 'ai_notes', f'chapter-{chapter.chapter_number}.html'), 'w', encoding='utf-8') as f:
                        f.write(html_ai)
                    if ai_ok:
                        indexable_pages.append(ai_rel)

                    # Solutions / Chat Page
                    practice_questions = PracticeQuestion.query.filter_by(
                        class_level=c_level,
                        subject=s['subject'],
                        chapter_number=chapter.chapter_number
                    ).all()

                    sol_rel = f"{subj_rel}/solutions/chapter-{chapter.chapter_number}.html"
                    sol_ok = bool(practice_questions)
                    html_sol = app.jinja_env.get_template('ssg/solution_page.html').render(
                        title=f"Ch {chapter.chapter_number} Solutions - {s['subject']}",
                        meta_description=f"Class {c_level} {s['subject']} Chapter {chapter.chapter_number} practice questions and solutions.",
                        root_path=root_path,
                        canonical_url=canonical_for(sol_rel) if sol_ok else None,
                        noindex=not sol_ok,
                        chapter=chapter,
                        practice_questions=practice_questions
                    )
                    with open(os.path.join(subj_folder, 'solutions', f'chapter-{chapter.chapter_number}.html'), 'w', encoding='utf-8') as f:
                        f.write(html_sol)
                    if sol_ok:
                        indexable_pages.append(sol_rel)
                        
        # 5. Generate website/jobs.html (only non-expired jobs are listed)
        jobs = JobAlert.query.order_by(JobAlert.created_at.desc()).all()
        active_jobs = [j for j in jobs if not is_job_expired(j)]
        html_jobs = app.jinja_env.get_template('ssg/jobs_index.html').render(
            title="Latest Sarkari Job Alerts",
            meta_description="Latest government, banking and railway job alerts — auto-updated from public sources.",
            root_path="./",
            canonical_url=canonical_for('jobs.html'),
            jobs=active_jobs
        )
        with open(os.path.join(website_dir, 'jobs.html'), 'w', encoding='utf-8') as f:
            f.write(html_jobs)
        print("Generated jobs.html")

        # 5b. Export REAL jobs for the SPA (js/jobs_data.js) — replaces demo data
        export_jobs_js(jobs, website_dir)
        
        # Generate Previous Papers Hub
        from models import PreviousYearPaper
        papers = PreviousYearPaper.query.order_by(PreviousYearPaper.year.desc()).all()
        html_papers = app.jinja_env.get_template('ssg/previous_papers.html').render(
            title="Previous Year Papers",
            meta_description="Download previous year question papers and answer keys for SSC, Banking, Railway and more.",
            root_path="./",
            canonical_url=canonical_for('previous_papers.html'),
            papers=papers
        )
        with open(os.path.join(website_dir, 'previous_papers.html'), 'w', encoding='utf-8') as f:
            f.write(html_papers)
        print("Generated previous_papers.html")
        
        # 6. Generate individual Job Detail pages
        jobs_folder = os.path.join(website_dir, 'jobs')
        os.makedirs(jobs_folder, exist_ok=True)
        
        import json
        for job in jobs:
            # Simple matching: fetch papers where exam_name is in job title, or category matches
            # For robustness in SSG, we just pass papers that share the same category, 
            # and limit to 5 so we don't overload the page.
            related_papers = [p for p in papers if p.category == job.category][:5]
            
            html_job_detail = app.jinja_env.get_template('ssg/job_detail.html').render(
                title=job.title,
                meta_description=(f"{job.title} — dates, eligibility and official links. "
                                  f"Verify on the official website before applying."),
                root_path="../",
                canonical_url=canonical_for(f'jobs/job_{job.id}.html'),
                job=job,
                json=json,
                related_papers=related_papers,
                is_expired=is_job_expired(job)
            )
            with open(os.path.join(jobs_folder, f'job_{job.id}.html'), 'w', encoding='utf-8') as f:
                f.write(html_job_detail)

        # 7. Generate sitemap.xml (only when SITE_URL is configured, e.g. after deploy)
        site_url = os.environ.get('SITE_URL', '').rstrip('/')
        if site_url:
            urls = ['index.html', 'classes.html', 'jobs.html', 'previous_papers.html']
            urls += [f'jobs/job_{job.id}.html' for job in active_jobs]
            # Standalone chapter SEO pages (written by books/build_chapters.py,
            # which lists them in chapters/_pages.json). These carry our best
            # content, so they matter most for search.
            seo_list = os.path.join(website_dir, 'chapters', '_pages.json')
            if os.path.exists(seo_list):
                import json as _json
                with open(seo_list, encoding='utf-8') as f:
                    urls += _json.load(f)

            # Only NCERT pages that actually carry content (collected above).
            # Empty placeholder pages are noindex and stay out of the sitemap —
            # thin pages at scale would drag down the whole domain's ranking.
            # Competitive-exam chapter files are SPA fragments (<article> only),
            # so they are excluded too — reached inside the app, not indexed.
            urls += indexable_pages
            from datetime import date
            today = date.today().isoformat()
            entries = ''.join(
                f'<url><loc>{site_url}/{u}</loc><lastmod>{today}</lastmod></url>' for u in urls
            )
            sitemap = ('<?xml version="1.0" encoding="UTF-8"?>'
                       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                       f'{entries}</urlset>')
            with open(os.path.join(website_dir, 'sitemap.xml'), 'w', encoding='utf-8') as f:
                f.write(sitemap)
            print(f"Generated sitemap.xml ({len(urls)} URLs)")
        else:
            print("Skipped sitemap.xml (set SITE_URL env var after deploying).")

        print("SSG Build Complete!")

if __name__ == "__main__":
    build_ssg()
