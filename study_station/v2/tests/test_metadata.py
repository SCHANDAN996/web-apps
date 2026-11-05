from app.promo import metadata


def question(**changes):
    q = {'subject': 'GK', 'level': '12th_Level', 'chapter': '12th_Level/GK/B/Chapter_01_Constitution',
         'question': 'किस अनुच्छेद से अस्पृश्यता समाप्त होती है?',
         'options': ['अनुच्छेद 14', 'अनुच्छेद 17', 'अनुच्छेद 21', 'अनुच्छेद 32'],
         'answer': 1, 'explanation': 'SOLUTION_SECRET'}
    return dict(q, **changes)


def test_topic_first_bilingual_specific_and_no_solution(monkeypatch):
    monkeypatch.setattr(metadata, 'chapter_topics', lambda q: ('संविधान', 'Constitution'))
    result = metadata.build(question(), link='https://t.me/studystation_hindi')
    assert result['title'].startswith('संविधान') and len(result['title']) <= 90
    assert result['title'].endswith('#Shorts')
    assert 'Constitution' in result['description'] and 'एक सवाल' in result['description'].splitlines()[0]
    assert question()['question'] in result['description']
    assert all(o in result['description'] for o in question()['options'])
    assert 'SOLUTION_SECRET' not in str(result)
    assert 'Bank' not in str(result) and 'UPSC' not in str(result)
    assert result['description'].splitlines()[-1].split() == ['#Shorts', '#GK', '#StudyStation']


def test_titles_change_with_question_and_remain_topic_first(monkeypatch):
    monkeypatch.setattr(metadata, 'chapter_topics', lambda q: ('प्रतिशत', 'Percentage'))
    a = metadata.build(question(subject='Maths', question='200 का 10 प्रतिशत कितना है?'))
    b = metadata.build(question(subject='Maths', question='500 का 20 प्रतिशत कितना है?'))
    assert a['title'] != b['title'] and a['title'].startswith('प्रतिशत')


def test_long_title_is_word_bounded_and_has_no_raw_chapter_number(monkeypatch):
    monkeypatch.setattr(metadata, 'chapter_topics', lambda q: ('संविधान के मूल सिद्धांत तथा संवैधानिक संस्थाएँ', 'Constitution'))
    result = metadata.build(question(question='भारत के संविधान के अनुसार इनमें से कौन सा विकल्प नागरिकों के मौलिक अधिकारों से संबंधित है?'))
    assert len(result['title']) <= 90 and result['title'].endswith('#Shorts')
    assert 'Chapter_01' not in result['title']


def test_subject_level_exam_rules_are_conservative():
    assert metadata.exam_names(question(level='Graduation_Level', subject='GK')) == ['SSC CGL']
    assert 'Bank PO' in metadata.exam_names(question(level='Graduation_Level', subject='Maths'))
    assert 'Bank PO' in metadata.exam_names(question(level='Graduation_Level', subject='Reasoning'))
    assert 'Bank PO' not in metadata.exam_names(question(level='Graduation_Level', subject='English'))
    assert metadata.exam_names(question(level='unknown')) == []
    assert metadata.exam_names(question(subject='unknown')) == []


def test_missing_chapter_metadata_falls_back_and_never_escapes_books(tmp_path, monkeypatch):
    monkeypatch.setattr(metadata.pick, 'books_root', lambda: tmp_path)
    result = metadata.build(question(chapter='../outside/Chapter_01_Constitution'))
    assert result['topic_hi'] == 'सामान्य ज्ञान'
    assert 'outside' not in result['title']
    other = metadata.build(question(chapter='12th_Level/GK/B/Chapter_04_Indian_Constitution'))
    assert other['topic_en'] == 'Indian Constitution'


def test_validated_fallback_keeps_real_question_without_invented_answer(monkeypatch):
    monkeypatch.setattr(metadata, 'chapter_topics', lambda q: ('संविधान', 'Constitution'))
    result = metadata.build(question(answer=900, options=None))
    assert result['fallback'] and question()['question'] in result['description']
    assert 'SOLUTION_SECRET' not in str(result)
    assert 'PYQ' not in result['description'] and 'practice set' not in result['description'].lower()


def test_utf8_limits_and_small_unique_tag_set(monkeypatch):
    monkeypatch.setattr(metadata, 'chapter_topics', lambda q: ('अध्याय ' * 2000, 'Very long topic ' * 2000))
    result = metadata.build(question(question='सवाल ' * 2000))
    assert len(result['title']) <= 90 and len(result['description'].encode('utf-8')) <= 5000
    assert sum(len(t) + 3 for t in result['tags']) <= 450
    assert len(result['tags']) == len({t.casefold() for t in result['tags']})
    assert '<' not in result['title'] and '>' not in result['description']


def test_malformed_subject_and_level_types_are_safe():
    result = metadata.build(question(subject=[], level={}))
    assert len(result['title']) <= 90 and result['exams'] == []
    assert question()['question'] in result['description']
