from app.bookcheck import check_chapter, is_prompt, main
from app.importers import ParsedQuestion, quality_problem


def mcq_set(lang, start=1, answers='abcd'):
    word, ans = ('उत्तर', 'हल') if lang == 'hi' else ('Answer', 'Solution')
    out = []
    for i in range(start, start + 25):
        a = answers[i % len(answers)]
        out.append(f'{i}. Question number {i} about rivers?\n(a) Ganga (b) Yamuna (c) Kaveri (d) Narmada\n'
                   f'{word}: ({a})\n{ans}: Because the textbook says so.\n')
    return '\n'.join(out)


def write_chapter(tmp_path, **override):
    ch = tmp_path / 'Chapter_07_States_Rivers'
    (ch / 'Prompts').mkdir(parents=True)
    body = 'Proper chapter text about states and rivers. ' * 20
    files = {f'{s}_{l}.txt': body for s in ('Content', 'Feynman', 'Flashcards', 'Key_Facts', 'PYQ')
             for l in ('hi', 'en')}
    files['Mind_Map.txt'] = '```mermaid\ngraph TD\n A-->B\n```\n' + body
    for n in range(1, 7):
        files[f'Practice_en_Set_{n:02d}.txt'] = mcq_set('en', (n - 1) * 25 + 1)
        files[f'Practice_hi_Set_{n:02d}.txt'] = mcq_set('hi', (n - 1) * 25 + 1)
    files.update(override)
    for name, text in files.items():
        (ch / 'Prompts' / name).write_text(text)
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
    good = 'Proper chapter text. ' * 30
    ch = write_chapter(tmp_path, **{
        'Mind_Map.txt': 'Diagram\nCode\nDownload\n' + good,
        'PYQ_hi.txt': 'वर्ष-वार प्रश्न (अनुमानित संख्या)\n' + good,
        'Practice_hi_Set_02.txt': mcq_set('hi', 26, answers='bcda'),
    })
    _, problems = check_chapter(ch)
    joined = ' '.join(problems)
    assert 'chat debris' in joined and 'no mermaid graph' in joined
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
