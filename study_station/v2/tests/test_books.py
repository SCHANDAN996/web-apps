import json
import os

import pytest

from app import books, config
from app.bookcheck import check_chapter, is_prompt, section_files
from app.models import Question, Topic
from test_bookcheck import mcq_set

PROMPT = "# Chapter: नदियाँ, Level: foundation\n\n@content_agent lang=hi 'नदियाँ' पर अध्याय लिखो"
STUB = "# Content (हिंदी) for काल (Tense)\nकृपया मास्टर प्रॉम्प्ट के अनुसार केवल Content खंड तैयार करें।"
FILL = '\n\nयह अनुच्छेद अध्याय की सामग्री को पूरा करता है ताकि फ़ाइल छोटी न लगे। ' * 8

CONTENT_HI = """📖 Content — प्रतिशत (हिंदी)

इस अध्याय में आप सीखेंगे:

· प्रतिशत का **असली** मतलब
· भिन्न और दशमलव

---

1. प्रागैतिहासिक कैनवस

पुरापाषाण: शिकारी-संग्राहक।
दूसरी पंक्ति।

| काल | स्थल |
|---|---|
| नवपाषाण | मेहरगढ़ |
| सिंधु | लोथल |

काल\tप्रमुख तथ्य\tयाद रखें
नवपाषाण\tमेहरगढ़\tसबसे प्राचीन कृषि
सिंधु\tलोथल\tगोदीबाड़ा
""" + FILL

MIND_MAP = '''```mermaid
graph TD
    R["💯 प्रतिशत<br>Percentage"]
    R --> D["📖 अर्थ"]
    R --> C["🔁 रूपांतरण"]
    D --> D1["प्रति सैकड़ा"]
    C --> C1["% → भिन्न:<br>n% = n/100"]
    C --> C2
    C2["<script>alert(1)</script>"]
```
''' + '%% ' + 'x' * 300 + '\n'

FLASH_HI = """🃏 फ्लैशकार्ड — प्रतिशत (हिंदी)

कार्ड 1
सामने: “प्रतिशत” का शाब्दिक अर्थ क्या है?
पीछे: “प्रति सैकड़ा।”

कार्ड 2
सामने: 40% को भिन्न में बदलो।
पीछे: 40/100 = 2/5।
दूसरी पंक्ति।

कार्ड 3
🃏 सामने: 12.5% किस भिन्न के बराबर है?
📝 पीछे: 1/8 के।
""" + FILL


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


@pytest.fixture
def books_dir(tmp_path, monkeypatch):
    root = tmp_path / 'books'
    gk = root / '10th_Level' / 'GK' / 'Foundation_10th_GK_WorldClass'
    # Old layout: content inside Prompts/
    ch1 = gk / 'Chapter_05_Polity'
    write(ch1 / 'README.md', '# भारतीय राजव्यवस्था / Indian Polity\n')
    write(ch1 / 'Prompts' / 'Content_hi.txt', 'राजव्यवस्था का पाठ।' + FILL)
    write(ch1 / 'Prompts' / 'Content_en.txt', 'Polity lesson text. ' * 30)
    write(ch1 / 'Prompts' / 'PYQ_hi.txt', 'Diagram\nCopy\n' + FILL)              # chat debris → hidden
    write(ch1 / 'Prompts' / 'Feynman_hi.txt', PROMPT)                            # still a prompt → hidden
    # New layout: content in root, prompts in Prompts/, chapter.json
    ch7 = gk / 'Chapter_07_States_Rivers'
    write(ch7 / 'Prompts' / 'Content_hi.txt', PROMPT)
    write(ch7 / 'Content_hi.txt', 'राज्य और नदियाँ।' + FILL)
    write(ch7 / 'chapter.json', json.dumps({'title_hi': 'राज्य एवं नदियाँ', 'title_en': 'States & Rivers',
                                            'topic': 'ga/indian-geography', 'type': 'static',
                                            'status': 'reviewed', 'as_of': 2025}))
    ch8 = gk / 'Chapter_08_World_Geography'                                       # todo only
    write(ch8 / 'Prompts' / 'Content_hi.txt', PROMPT)
    write(ch8 / 'README.md', '# विश्व भूगोल / World Geography\n')
    ch20 = gk / 'Chapter_20_Current_Affairs_6M'
    write(ch20 / 'chapter.json', '{"type": "dynamic", "title_hi": "करंट अफेयर्स", "title_en": "Current Affairs"}')
    write(ch20 / 'Prompts' / 'Content_hi.txt', PROMPT)
    maths = root / '10th_Level' / 'Maths' / 'Foundation_10th_Math_WorldClass' / 'Chapter_05_Percentage'
    write(maths / 'Content_hi.txt', CONTENT_HI)
    write(maths / 'Mind_Map.txt', MIND_MAP)
    write(maths / 'Flashcards_hi.txt', FLASH_HI)
    write(maths / 'Content_en.txt', STUB)                                         # English-book stub prompt
    # A book with nothing finished is not listed
    write(root / '10th_Level' / 'Reasoning' / 'Chapter_01_Analogy' / 'Content_hi.txt', PROMPT)
    # …nor one whose only "readable" chapter is the live current-affairs link
    ca12 = root / '12th_Level' / 'GK' / 'Intermediate_12th_GK_WorldClass' / 'Chapter_20_Current_Affairs_6M'
    write(ca12 / 'chapter.json', '{"type": "dynamic"}')
    write(ca12 / 'Prompts' / 'Content_hi.txt', PROMPT)
    monkeypatch.setattr(config, 'BOOKS_DIR', root)
    monkeypatch.setattr(config, 'BOOKS_RECHECK_SECONDS', 0)
    return root


# ------------------------------------------------------------------ discovery
def test_index_discovers_books_chapters_and_sections(books_dir):
    readable = {b.slug: b for b in books.readable_books()}
    assert set(readable) == {'foundation-10th-gk', 'foundation-10th-math'}
    assert books.get_book('10th-reasoning') is not None                          # discovered, just not readable
    assert books.get_book('intermediate-12th-gk').readable_chapters                # only the dynamic chapter
    gk = readable['foundation-10th-gk']
    assert [c.slug for c in gk.chapters] == ['05-polity', '07-states-rivers', '08-world-geography',
                                             '20-current-affairs-6m']
    polity, rivers, world, ca = gk.chapters
    assert (polity.title_hi, polity.title_en) == ('भारतीय राजव्यवस्था', 'Indian Polity')     # README title
    assert set(polity.sections) == {'Content'}            # PYQ (debris) and Feynman (prompt) skipped
    assert set(polity.sections['Content']) == {'hi', 'en'}
    assert rivers.title_en == 'States & Rivers' and rivers.reviewed and rivers.meta['as_of'] == '2025'
    assert rivers.sections['Content']['hi'] == rivers.path / 'Content_hi.txt'                 # root wins
    assert not world.readable and ca.dynamic and ca.readable
    assert [c.slug for c in gk.readable_chapters] == ['05-polity', '07-states-rivers', '20-current-affairs-6m']
    pct = readable['foundation-10th-math'].chapters[0]
    assert set(pct.sections) == {'Content', 'Mind_Map', 'Flashcards'} and 'en' not in pct.sections['Content']


def test_index_notices_new_and_changed_files(books_dir):
    world = books.get_book('foundation-10th-gk').chapters[2]
    assert not world.readable
    write(world.path / 'Content_hi.txt', 'विश्व भूगोल का पाठ।' + FILL)
    assert books.get_book('foundation-10th-gk').chapters[2].readable
    p = world.path / 'Content_hi.txt'
    write(p, PROMPT)
    os.utime(p, ns=(1, 1))                                 # different mtime even on a fast filesystem
    assert not books.get_book('foundation-10th-gk').chapters[2].readable


def test_bad_chapter_json_is_ignored(books_dir, caplog):
    ch = books_dir / '10th_Level' / 'GK' / 'Foundation_10th_GK_WorldClass' / 'Chapter_05_Polity'
    write(ch / 'chapter.json', '{not json')
    assert books.load_meta(ch) == {}
    assert 'ignoring' in caplog.text
    write(ch / 'chapter.json', '{"topic": "ga/no-such-topic", "status": "final", "as_of": "soon"}')
    meta = books.load_meta(ch)
    assert 'topic' not in meta and meta['status'] == 'draft' and meta['as_of'] is None


# ------------------------------------------------------------------ rendering
def test_render_escapes_everything():
    html = str(books.render_text('<script>alert(1)</script>\n# <img src=x onerror=alert(1)>\n'
                                 '- **<b>bold</b>**\n| <i>a</i> | b |\n|---|---|\n| c | d |'))
    assert '<script' not in html and '<img' not in html and '<b>' not in html and '<i>' not in html
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html
    assert '<strong>&lt;b&gt;bold&lt;/b&gt;</strong>' in html


def test_render_blocks_and_tables():
    html = str(books.render_text(CONTENT_HI))
    assert html.startswith('<h2>📖 Content — प्रतिशत (हिंदी)</h2>')
    assert '<ul><li>प्रतिशत का <strong>असली</strong> मतलब</li><li>भिन्न और दशमलव</li></ul>' in html
    assert '<hr>' in html and '<h3>1. प्रागैतिहासिक कैनवस</h3>' in html
    assert '<strong>पुरापाषाण:</strong> शिकारी-संग्राहक।<br>दूसरी पंक्ति।' in html
    assert html.count('<div class="table-scroll"><table class="book-table">') == 2
    assert '<th scope="col">काल</th><th scope="col">स्थल</th>' in html          # pipe table, separator dropped
    assert '<td>मेहरगढ़</td><td>सबसे प्राचीन कृषि</td>' in html                      # tab table
    assert '---|' not in html
    ol = str(books.render_text('1. Pick the base, always the original amount.\n2. Then divide.'))
    assert ol == '<ol start="1"><li>Pick the base, always the original amount.</li><li>Then divide.</li></ol>'


def test_mind_map_tree():
    roots = books.parse_mermaid(MIND_MAP)
    assert len(roots) == 1
    label, kids = roots[0]
    assert label == '💯 प्रतिशत\nPercentage'
    assert [k[0] for k in kids] == ['📖 अर्थ', '🔁 रूपांतरण']
    assert [k[0] for k in kids[1][1]] == ['% → भिन्न:\nn% = n/100', 'alert(1)']        # tags stripped from labels
    html = str(books.render_tree(roots))
    assert html.startswith('<ul class="mm-tree"><li><details open><summary class="mm-node">💯 प्रतिशत<br>Percentage')
    assert '<script' not in html
    mm = books.parse_mermaid('mindmap\n  root((GK))\n    History\n      Ancient\n    Polity\n')
    assert mm == [('GK', [('History', [('Ancient', [])]), ('Polity', [])])]
    assert books.parse_mermaid('Diagram\nAncient Indian History\nPrehistoric Age') is None
    assert books.parse_mermaid('graph TD\n    A["only one node"]') is None
    chain = books.parse_mermaid('flowchart LR\n A[Start] -->|yes| B(Middle) --> C{End}\n A -.-> D')
    assert chain == [('Start', [('Middle', [('End', [])]), ('D', [])])]


def test_flashcards_parse_and_render():
    intro, cards, outro = books.parse_flashcards(FLASH_HI)
    assert intro.strip() == '🃏 फ्लैशकार्ड — प्रतिशत (हिंदी)'
    assert cards[0] == ('“प्रतिशत” का शाब्दिक अर्थ क्या है?', '“प्रति सैकड़ा।”')
    assert cards[1][1] == '40/100 = 2/5।\nदूसरी पंक्ति।'
    assert cards[2] == ('12.5% किस भिन्न के बराबर है?', '1/8 के।')
    qa = books.parse_flashcards('Flashcards\n\nCard 1\nQ: What is 10% of 50?\nA: 5\n\nCard 2\nQ: 1/4 as %?\nA: 25%\n')
    assert qa[1] == [('What is 10% of 50?', '5'), ('1/4 as %?', '25%')]
    assert books.parse_flashcards('Just some text\nwith no cards at all.') is None
    html = str(books.render_flashcards((intro, cards, outro), 'hi'))
    assert html.count('data-flip aria-expanded="false"') == 3 and 'कार्ड 1' in html
    assert '<script' not in str(books.render_flashcards(('', [('<script>x</script>', 'b'), ('c', 'd')], ''), 'en'))


def test_topic_mapping_covers_gk_chapters():
    gk = {'States_Rivers': ('ga', 'indian-geography'), 'World_Geography': ('ga', 'physical-geography'),
          'Economy_Basic': ('ga', 'economy'), 'Physics_Daily': ('science', 'physics'),
          'Chemistry': ('science', 'chemistry'), 'Biology': ('science', 'biology'),
          'Awards': ('ga', 'awards-books'), 'Sports': ('ga', 'sports'), 'Days_Dates': ('ga', 'important-days'),
          'Books_Authors': ('ga', 'awards-books'), 'Culture_Art': ('ga', 'art-culture'),
          'Science_Tech': ('ga', 'science-tech'), 'Environment': ('ga', 'environment'),
          'Ancient_History': ('ga', 'ancient-history')}
    for name, ref in gk.items():
        assert books.topic_for_chapter('ga', name) == ref, name
    assert books.topic_for_chapter('english', 'Tense') == ('english', 'tenses')
    assert books.topic_for_chapter('ga', 'Current_Affairs_6M') is None
    assert books.topic_for_chapter('ga', 'Awards', {'topic': 'ga/sports'}) == ('ga', 'sports')
    for ref in books.CHAPTER_TOPICS.values():                       # every mapping target exists
        assert books._topic_ref(ref), ref


# ------------------------------------------------------------------ pages
def test_books_pages(client, books_dir):
    r = client.get('/books')
    assert r.status_code == 200
    assert '/books/foundation-10th-gk' in r.text and '/books/foundation-10th-math' in r.text
    assert '10th-reasoning' not in r.text and '3/4 अध्याय तैयार' in r.text
    r = client.get('/books/foundation-10th-gk')
    assert r.status_code == 200
    assert 'href="/books/foundation-10th-gk/05-polity"' in r.text
    assert 'href="/books/foundation-10th-gk/08-world-geography"' not in r.text and 'जल्द आ रहा है' in r.text
    for url in ('/books/nope', '/books/10th-reasoning', '/books/foundation-10th-gk/08-world-geography',
                '/books/foundation-10th-gk/99-nothing', '/books/foundation-10th-gk/05-polity?s=pyq'):
        assert client.get(url).status_code == 404, url


def test_chapter_page_sections_language_and_badges(client, books_dir):
    r = client.get('/books/foundation-10th-math/05-percentage')
    assert r.status_code == 200
    assert 'class="tap-link" href="/books"' in r.text
    assert '>पाठ</a>' in r.text and '>माइंड मैप</a>' in r.text and '>फ़्लैशकार्ड</a>' in r.text
    assert 'AI की मदद से लिखा · समीक्षा बाकी' in r.text                        # no chapter.json → draft
    assert "script-src 'self'" in r.headers['content-security-policy']
    r = client.get('/books/foundation-10th-math/05-percentage?s=mind-map')
    assert 'class="mm-tree"' in r.text and '&lt;script' not in r.text and '<script>alert' not in r.text
    r = client.get('/books/foundation-10th-math/05-percentage?s=flashcards')
    assert 'class="fc"' in r.text and 'aria-expanded="false"' in r.text
    # English learner on a Hindi-only section: shown in Hindi with a note
    client.cookies.set('ss_lang', 'en')
    r = client.get('/books/foundation-10th-math/05-percentage')
    assert 'This section is only in Hindi for now.' in r.text
    # Both languages: a toggle to the other one
    r = client.get('/books/foundation-10th-gk/05-polity')
    assert 'Polity lesson text.' in r.text and '?s=content&amp;lang=hi' in r.text and 'Read in Hindi' in r.text
    r = client.get('/books/foundation-10th-gk/05-polity?lang=hi')
    assert 'राजव्यवस्था का पाठ।' in r.text and 'Read in English' in r.text
    r = client.get('/books/foundation-10th-gk/07-states-rivers')
    assert 'States &amp; Rivers' in r.text and 'Facts as of 2025' in r.text and 'AI-assisted' not in r.text
    assert 'href="/books/foundation-10th-gk/05-polity" rel="prev"' in r.text
    assert 'href="/books/foundation-10th-gk/20-current-affairs-6m" rel="next"' in r.text
    r = client.get('/books/foundation-10th-gk/20-current-affairs-6m')
    assert r.status_code == 200 and 'href="/current-affairs"' in r.text
    client.cookies.delete('ss_lang')


def test_section_with_script_renders_inert(client, books_dir):
    ch = books_dir / '10th_Level' / 'GK' / 'Foundation_10th_GK_WorldClass' / 'Chapter_05_Polity'
    write(ch / 'Key_Facts_hi.txt', '<script>alert("x")</script>\n<a href="javascript:alert(1)">x</a>' + FILL)
    r = client.get('/books/foundation-10th-gk/05-polity?s=key-facts')
    assert r.status_code == 200
    assert '<script>alert' not in r.text and '<a href="javascript' not in r.text
    assert '&lt;script&gt;alert(&#34;x&#34;)&lt;/script&gt;' in r.text


def test_practice_button_only_with_questions(client, books_dir, db):
    polity = db.query(Topic).filter(Topic.slug == 'polity').first()
    r = client.get('/books/foundation-10th-gk/05-polity')              # ga/polity has 30 test questions
    assert f'data-practice="{polity.id}"' in r.text and 'इस अध्याय का अभ्यास' in r.text
    ch = books_dir / '10th_Level' / 'GK' / 'Foundation_10th_GK_WorldClass' / 'Chapter_07_States_Rivers'
    write(ch / 'chapter.json', '{"topic": "ga/important-days"}')     # chapter.json picks the topic
    days = db.query(Topic).filter(Topic.slug == 'important-days').first()
    assert not db.query(Question).filter(Question.topic_id == days.id).count()
    r = client.get('/books/foundation-10th-gk/07-states-rivers')
    assert 'data-practice=' not in r.text


def test_home_practice_and_sitemap_link_books(client, books_dir):
    client.post('/api/v1/me', json={'level': '10th'})
    assert 'href="/books"' in client.get('/').text
    assert 'href="/books"' in client.get('/practice').text
    sm = client.get('/sitemap.xml').text
    assert '/books/foundation-10th-gk/05-polity</loc>' in sm and '08-world-geography' not in sm


def test_seed_imports_mapped_chapter_sets(books_dir, db):
    from app.seed import seed_questions
    ch = books_dir / '10th_Level' / 'GK' / 'Foundation_10th_GK_WorldClass' / 'Chapter_07_States_Rivers'
    write(ch / 'Practice_en_Set_01.txt', mcq_set('en'))
    write(ch / 'Practice_hi_Set_01.txt', mcq_set('hi'))
    try:
        stats = seed_questions(db, root=books_dir)
        assert stats['skipped_topic'] == 0
        geo = db.query(Topic).filter(Topic.slug == 'indian-geography').first()
        qs = db.query(Question).filter(Question.import_key.like('10th/ga/states-rivers/%')).all()
        assert len(qs) == 50 and all(q.topic_id == geo.id for q in qs)
    finally:
        db.query(Question).filter(Question.import_key.like('10th/ga/states-rivers/%')).delete(synchronize_session=False)
        db.commit()


# ------------------------------------------------------------------ bookcheck layout rules
def test_section_files_prefers_finished_root(tmp_path):
    ch = tmp_path / 'Chapter_01_Noun'
    write(ch / 'Prompts' / 'Content_hi.txt', 'old content in Prompts. ' * 20)
    write(ch / 'Content_hi.txt', 'new content in root. ' * 20)
    write(ch / 'Prompts' / 'Content_en.txt', 'finished English in Prompts. ' * 20)
    write(ch / 'Content_en.txt', PROMPT)                                    # root still a prompt → Prompts/ wins
    write(ch / 'Prompts' / 'PYQ_hi.txt', PROMPT)
    files = section_files(ch)
    assert files['Content_hi.txt'] == ch / 'Content_hi.txt'
    assert files['Content_en.txt'] == ch / 'Prompts' / 'Content_en.txt'
    assert files['PYQ_hi.txt'] == ch / 'Prompts' / 'PYQ_hi.txt'


def test_stub_prompts_and_language_mind_maps(tmp_path):
    assert is_prompt(STUB)
    assert is_prompt('# काल (Tense), Set 1/6\n25 MCQs (प्रश्न 1-25)। प्रत्येक में 4 विकल्प, उत्तर, हल, स्रोत।')
    assert not is_prompt('Finished text that mentions a prompt reply. ' * 20)     # long text is never a stub
    ch = tmp_path / 'Chapter_05_Tense'
    write(ch / 'Content_hi.txt', STUB)
    write(ch / 'Mind_Map_hi.txt', 'केवल पाठ, कोई ग्राफ़ नहीं। ' * 30)
    todo, problems = check_chapter(ch)
    assert 'Content_hi.txt' in todo
    assert any('Mind_Map_hi.txt: no ```mermaid graph block' in p for p in problems)


def test_language_mind_maps_in_reader(books_dir):
    ch = books_dir / '10th_Level' / 'Maths' / 'Foundation_10th_Math_WorldClass' / 'Chapter_05_Percentage'
    write(ch / 'Mind_Map_en.txt', MIND_MAP.replace('प्रतिशत<br>', ''))
    pct = books.get_book('foundation-10th-math').chapters[0]
    assert set(pct.sections['Mind_Map']) == {'*', 'en'}
    assert books.pick_lang(pct, 'Mind_Map', 'en') == 'en'
    assert books.pick_lang(pct, 'Mind_Map', 'hi') == '*'


def test_fill_meta_creates_and_completes_without_overwriting(tmp_path):
    ch = tmp_path / '10th_Level' / 'GK' / 'Foundation_10th_GK_WorldClass' / 'Chapter_07_States_Rivers'
    write(ch / 'README.md', '# राज्य एवं नदियाँ / States & Rivers\n')
    assert set(books.fill_meta(ch)) == {'title_hi', 'title_en', 'type', 'status', 'topic'}
    meta = json.loads((ch / 'chapter.json').read_text())
    assert meta['title_en'] == 'States & Rivers' and meta['topic'] == 'ga/indian-geography'
    assert meta['type'] == 'static' and meta['status'] == 'draft'
    meta.update(status='reviewed', as_of=2025)
    (ch / 'chapter.json').write_text(json.dumps(meta))
    assert books.fill_meta(ch) == []                                  # nothing missing → untouched
    assert json.loads((ch / 'chapter.json').read_text())['status'] == 'reviewed'
    ca = tmp_path / '10th_Level' / 'GK' / 'Foundation_10th_GK_WorldClass' / 'Chapter_20_Current_Affairs_6M'
    ca.mkdir()
    books.fill_meta(ca)
    assert json.loads((ca / 'chapter.json').read_text())['type'] == 'dynamic'
