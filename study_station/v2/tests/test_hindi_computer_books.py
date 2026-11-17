"""New subjects must be readable/importable without translating away Hindi questions."""
import json

import pytest

from app import books, catalog
from app.bookcheck import (check_practice_pair, hindi_pair_problems, language_problem,
                           meta_problems)
from app.i18n import t
from app.importers import ParsedQuestion, discover_practice_files


@pytest.mark.parametrize('folder,subject,level,topic', [
    ('Hindi', 'hindi', '10th_Level', 'sandhi'),
    ('Computer', 'computer', '12th_Level', 'networking'),
])
def test_new_book_discovered_with_catalog_topic_and_label(tmp_path, folder, subject, level, topic):
    chapter = tmp_path / level / folder / 'New_Book_WorldClass' / ('Chapter_01_' + topic.replace('-', '_'))
    chapter.mkdir(parents=True)
    (chapter / 'chapter.json').write_text(json.dumps({
        'title_hi': 'नया अध्याय', 'title_en': topic,
        'topic': f'{subject}/{topic}', 'type': 'static', 'status': 'draft',
    }))
    found = books._scan(tmp_path)
    assert len(found) == 1
    assert found[0].subject == subject
    assert found[0].chapters[0].topic == (subject, topic)
    assert meta_problems(chapter) == []
    assert t('book_subject_' + subject, 'hi') != 'book_subject_' + subject
    assert subject in {row[0] for row in catalog.SUBJECTS}


@pytest.mark.parametrize('folder,subject,level', [
    ('Hindi', 'hindi', '10th_Level'), ('Computer', 'computer', '12th_Level'),
])
def test_new_subject_practice_import_discovery(tmp_path, folder, subject, level):
    path = tmp_path / level / folder / 'New_Book_WorldClass' / 'Chapter_01_Basics' / 'Practice_hi_Set_01.txt'
    path.parent.mkdir(parents=True)
    path.write_text('अभ्यास सामग्री ' * 300)
    found = list(discover_practice_files(tmp_path))
    assert len(found) == 1
    assert found[0][1] == subject
    assert found[0][-1] == path


def test_hindi_targets_allowed_only_in_hindi_subject_english_wrapper():
    text = ('Choose the correct synonym of «अत्यंतसुंदरविशालमनोहर». '
            'The answer preserves the original Hindi meaning. ' * 4)
    assert language_problem('Content_en.txt', text, hindi_book=True) is None
    assert language_problem('Content_en.txt', text) is not None
    assert language_problem('Content_en.txt', text.replace('«', '').replace('»', ''), hindi_book=True) is not None
    assert language_problem('Content_en.txt', '«पूरा हिंदी पाठ»' * 40, hindi_book=True) is not None
    assert language_problem('Content_en.txt', 'पूरा हिंदी पाठ ' * 40, hindi_book=True) is not None
    assert language_problem('Content_hi.txt', 'Wrong language English paragraph. ' * 30, hindi_book=True) is not None


def question(stem, options=None):
    return ParsedQuestion(1, stem, options or ['«जल»', '«अग्नि»', '«वायु»', '«भूमि»'], 0, 'Water means जल.')


def test_hindi_practice_translation_keeps_options_and_tested_text():
    en = [question('Choose the synonym of «पानी» from the options.')]
    hi = [question('«पानी» का पर्यायवाची चुनिए।')]
    assert hindi_pair_problems(en, hi) == []
    unquoted = [question('Choose the synonym of पानी from the options.')]
    assert 'must be explicitly quoted' in ' '.join(hindi_pair_problems(unquoted, hi))
    assert 'tested Hindi text changed' in ' '.join(hindi_pair_problems(en, [question('«आग» का पर्यायवाची चुनिए।')]))
    translated = [question('«पानी» का पर्यायवाची चुनिए।', ['Water', 'Fire', 'Air', 'Earth'])]
    assert 'options changed' in ' '.join(hindi_pair_problems(en, translated))
    reordered = [question('«पानी» का पर्यायवाची चुनिए।', ['«अग्नि»', '«जल»', '«वायु»', '«भूमि»'])]
    assert 'options changed' in ' '.join(hindi_pair_problems(en, reordered))


def test_hindi_book_checks_hindi_without_english_dependency(tmp_path):
    en_path, hi_path = [tmp_path / f'Practice_{lang}_Set_01.txt' for lang in ('en', 'hi')]
    en, hi = [], []
    for n in range(1, 26):
        answer = 'abcd'[(n - 1) % 4]
        opts = '(a) «जल» (b) «अग्नि» (c) «वायु» (d) «भूमि»'
        en.append(f'{n}. Choose the matching Hindi word in «पानी» example number {n}.\n{opts}\nAnswer: ({answer})\nSolution: The example tests original Hindi words and their meaning.\nSource: PYQ-style')
        hi.append(f'{n}. «पानी» उदाहरण {n} में उचित हिंदी शब्द चुनिए।\n{opts}\nउत्तर: ({answer})\nहल: मूल हिंदी शब्दों के अर्थ के आधार पर उचित विकल्प चुना जाता है।\nस्रोत: PYQ-style')
    en_path.write_text('\n'.join(en))
    hi_path.write_text('\n'.join(hi))
    assert check_practice_pair(en_path, hi_path, hindi_book=True) == []
    hi_path.write_text('\n'.join(hi).replace('«पानी»', '«आग»', 1))
    assert check_practice_pair(en_path, hi_path, hindi_book=True) == []
    en_path.unlink()
    assert check_practice_pair(None, hi_path, hindi_book=True) == []
    hi_path.write_text('\n'.join(hi).replace('(b) «अग्नि»', '(b) «जल»', 1))
    assert 'duplicate_options' in ' '.join(check_practice_pair(None, hi_path, hindi_book=True))
