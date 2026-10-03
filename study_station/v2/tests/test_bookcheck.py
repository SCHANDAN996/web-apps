from app.bookcheck import check_chapter, is_prompt, main
from app.importers import ParsedQuestion, quality_problem


def mcq_set(lang, start=1, answers='abcd', source=''):
    if lang == 'hi':
        word, ans, q, opts, why = 'उत्तर', 'हल', 'नदी के बारे में प्रश्न', '(a) गंगा (b) यमुना (c) कावेरी (d) नर्मदा', 'पाठ्यपुस्तक के अनुसार।'
    else:
        word, ans, q, opts, why = 'Answer', 'Solution', 'Question about rivers', '(a) Ganga (b) Yamuna (c) Kaveri (d) Narmada', 'Because the textbook says so.'
    out = []
    for i in range(start, start + 25):
        a = answers[i % len(answers)]
        out.append(f'{i}. {q} {i}?\n{opts}\n{word}: ({a})\n{ans}: {why}\n{source}')
    return '\n'.join(out)


def write_chapter(tmp_path, **override):
    ch = tmp_path / 'Chapter_07_States_Rivers'
    (ch / 'Prompts').mkdir(parents=True)
    body = {'en': 'Proper chapter text about states and rivers. ' * 20,
            'hi': 'राज्य और नदियों के बारे में अध्याय का पाठ। ' * 20}
    files = {f'{s}_{l}.txt': body[l] for s in ('Content', 'Feynman', 'Flashcards', 'Key_Facts', 'PYQ')
             for l in ('hi', 'en')}
    files['Mind_Map.txt'] = ('```mermaid\ngraph TD\n' + ''.join(
        f'    R["नदियाँ / Rivers"] --> N{i}["नदी {i} / River {i}<br>उद्गम और राज्य"]\n' for i in range(8)) + '```\n')
    files['chapter.json'] = ('{"title_hi": "राज्य एवं नदियाँ", "title_en": "States & Rivers", '
                             '"topic": "ga/indian-geography", "type": "static", "status": "draft"}')
    for n in range(1, 7):
        files[f'Practice_en_Set_{n:02d}.txt'] = mcq_set('en', (n - 1) * 25 + 1)
        files[f'Practice_hi_Set_{n:02d}.txt'] = mcq_set('hi', (n - 1) * 25 + 1)
    files.update(override)
    for name, text in files.items():
        (ch / name if name == 'chapter.json' else ch / 'Prompts' / name).write_text(text)
    return ch


def test_complete_chapter_passes(tmp_path):
    ch = write_chapter(tmp_path)
    assert check_chapter(ch) == ([], [])
    assert main([str(ch)]) == 0


def test_prompt_files_are_todo(tmp_path):
    prompt = "# Chapter: नदियाँ, Level: foundation\n\n@content_agent lang=hi 'नदियाँ' पर अध्याय लिखो"
    assert is_prompt(prompt)
    ch = write_chapter(tmp_path, **{'Content_hi.txt': prompt, 'Practice_hi_Set_03.txt': prompt})
    todo, problems = check_chapter(ch)
    assert 'Content_hi.txt' in todo and any('Set 03 hi' in t for t in todo)
    assert main([str(ch)]) == 1


def test_debris_unsourced_and_mismatch_are_problems(tmp_path):
    good = 'अध्याय का सही पाठ। ' * 30
    ch = write_chapter(tmp_path, **{
        'Mind_Map.txt': 'Diagram\nCode\nDownload\n' + good,
        'PYQ_hi.txt': 'वर्ष-वार प्रश्न (अनुमानित संख्या)\n' + good,
        'Practice_hi_Set_02.txt': mcq_set('hi', 26, answers='bcda'),
    })
    _, problems = check_chapter(ch)
    joined = ' '.join(problems)
    assert 'chat debris' in joined and 'no ```mermaid graph' in joined
    assert 'unsourced claim' in joined
    assert 'Set 02 hi/en answer mismatch' in joined


def test_ordinary_here_is_is_not_debris(tmp_path):
    text = 'The ground here is made of boulders. ' * 20
    ch = write_chapter(tmp_path, **{'Feynman_en.txt': text})
    assert check_chapter(ch) == ([], [])


def test_statement_question_is_self_contained():
    q = ParsedQuestion(1, 'नालंदा के संदर्भ में कथनों पर विचार करें:\n1. कुमारगुप्त ने स्थापना की\n'
                          '2. ह्वेनसांग ने अध्ययन किया\nउपरोक्त में से कौन-से कथन सही हैं?',
                       ['केवल 1', 'केवल 2', 'दोनों', 'कोई नहीं'], 2, 'दोनों सही हैं।')
    assert quality_problem(q) is None
    lone = ParsedQuestion(2, 'उपरोक्त व्यवस्था में कौन बीच में है?', ['A', 'B', 'C', 'D'], 0, '')
    assert quality_problem(lone) == 'needs_context'


def test_strict_rules(tmp_path):
    root = tmp_path / '10th_Level'
    ch = write_chapter(root, **{
        'PYQ_en.txt': 'Pattern of questions asked in UPSC and SSC exams. ' * 20,           # UPSC in a 10th book
        'Content_hi.txt': 'This Hindi file was written in English by mistake. ' * 20,      # wrong language
        'Practice_en_Set_02.txt': mcq_set('en', 26, answers='a'),                          # every answer (a)
        'Practice_hi_Set_02.txt': mcq_set('hi', 26, answers='a'),
        'Practice_en_Set_03.txt': mcq_set('en', 1),                                        # numbered 1-25, not 51-75
        'Practice_en_Set_04.txt': mcq_set('en', 76, source='Source: SSC CGL 2019 Tier-I\n'),  # unverified exam source
        'chapter.json': '{"title_hi": "x", "title_en": "x", "topic": "ga/nope", "type": "static", "status": "ok"}',
    })
    joined = ' '.join(check_chapter(ch)[1])
    for expected in ('mentions UPSC', 'Hindi file is mostly not in Hindi', 'answers not spread',
                     'numbering should be 51–75', 'unverified exam/year source', 'not a catalog topic',
                     'status must be'):
        assert expected in joined, expected


def test_verified_exam_source_with_link_is_allowed(tmp_path):
    src = 'Source: SSC CGL 2019 Tier-I, official answer key https://ssc.gov.in/x.pdf\n'
    ch = write_chapter(tmp_path, **{'Practice_en_Set_04.txt': mcq_set('en', 76, source=src)})
    assert check_chapter(ch) == ([], [])


def test_next_and_status_follow_the_queue(tmp_path, monkeypatch, capsys):
    import app.bookcheck as bc
    books = tmp_path / 'books'
    done = write_chapter(books / 'A')
    todo = write_chapter(books / 'B', **{'Content_hi.txt': "# Chapter: x\n@content_agent lang=hi 'x'"})
    (books / 'QUEUE.txt').write_text('# order\nA\nB\n')
    monkeypatch.setattr(bc, 'BOOKS_ROOT', books)
    assert bc.next_chapter()[0] == todo
    assert main(['--next']) == 1 and 'MODE: write' in capsys.readouterr().out
    assert main(['--status']) == 0
    out = capsys.readouterr().out
    assert 'A:  OK 1' in out and 'B:  TODO 1' in out
