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


def test_question_that_admits_broken_data_is_rejected():
    q = ParsedQuestion(1, 'C, A से 6 स्थान बाएँ है। D का स्थान क्या होगा? ⚠️ (आँकड़े असंगत हो सकते हैं)',
                       ['30वाँ', '31वाँ', '32वाँ', 'निर्धारित नहीं'], 3, '')
    assert quality_problem(q) == 'broken_question'
    ok = ParsedQuestion(2, 'भारत की राजधानी क्या है?', ['दिल्ली', 'मुंबई', 'कोलकाता', 'चेन्नई'], 0, 'नई दिल्ली।')
    assert quality_problem(ok) is None


def test_trap_hint_is_cut_from_the_question():
    from app.importers import parse_mcq_text
    text = ('1. (⚠️ परीक्षक का जाल: सभी अभाज्य, लेकिन सम-विषम)\nभिन्न संख्या चुनिए –\n(a) 2 (b) 3 (c) 5 (d) 9\nउत्तर: (d)\nहल: 9 अभाज्य नहीं है।\n')
    q = parse_mcq_text(text)[0]
    assert q.text == 'भिन्न संख्या चुनिए –' and quality_problem(q) is None


def test_trap_heading_line_is_cut_too():
    from app.importers import parse_mcq_text
    text = ('5. ⚠️ परीक्षक का जाल\nशाम 4 बजे लड़की की छाया बाईं ओर है। वह किस दिशा में है?\n'
            '(a) उत्तर (b) दक्षिण (c) पूर्व (d) पश्चिम\nउत्तर: (b)\nहल: शाम को सूर्य पश्चिम में।\n')
    assert parse_mcq_text(text)[0].text.startswith('शाम 4 बजे')


def test_trap_hint_variants_and_no_false_cut():
    from app.importers import TRAP_HINT
    assert TRAP_HINT.sub('', 'कौन? (परीक्षक का जाल – दोहरा संबंध)') == 'कौन? '
    assert TRAP_HINT.sub('', 'x (Examiner’s Trap – Misleading Options)') == 'x '
    assert TRAP_HINT.sub('', 'समलंब (Trapezium) का क्षेत्रफल') == 'समलंब (Trapezium) का क्षेत्रफल'


def test_quoted_examples_are_not_leaked_reasoning():
    from app.importers import ParsedQuestion, quality_problem
    ok = ParsedQuestion(1, 'Fill in the blank: "I will ____ for you at the gate."', ['wait', 'waits', 'waited', 'waiting'],
                        0, 'After "will" the base form is used: "I will wait for you".')
    leak = ParsedQuestion(2, 'Choose the synonym of happy.', ['glad', 'sad', 'angry', 'tired'], 0,
                          'Glad. Wait, let me recheck the options.')
    assert quality_problem(ok) is None and quality_problem(leak) == 'leaked_reasoning'


def test_english_book_hindi_files_may_quote_much_english():
    from app.bookcheck import language_problem
    text = 'नियम: Present Perfect में have/has के बाद क्रिया का तीसरा रूप आता है। ' * 2 + 'Example: She has finished her homework already. ' * 6
    assert language_problem('Mind_Map_hi.txt', text) is not None
    assert language_problem('Mind_Map_hi.txt', text, english_book=True) is None
    assert language_problem('Mind_Map_hi.txt', 'Only English here. ' * 20, english_book=True) is not None
