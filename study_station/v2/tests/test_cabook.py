"""The current-affairs fact bank (tools/current_affairs/facts.tsv) and the set builder that uses it."""
import importlib.util
import re
from datetime import date
from pathlib import Path

import pytest

from app import bookgen

TOOL = Path(__file__).resolve().parents[1] / 'tools' / 'current_affairs' / 'cabook.py'
spec = importlib.util.spec_from_file_location('cabook', TOOL)
cabook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cabook)


def test_fact_bank_rows_are_complete():
    facts = cabook.load_facts()
    assert len(facts) >= 150
    for f in facts:
        date.fromisoformat(f['date'])
        assert f['level'] in 'EMH'
        assert f['question'].strip() and f['answer'].strip() and f['explanation'].strip()
        assert len(f['wrong']) == 3 and all(f['wrong'])
        assert f['answer'] not in f['wrong'], f['question']
        assert len(set(f['wrong'])) == 3, f['question']
        assert re.match(r'https://newsonair\.gov\.in/', f['air_link']), f['question']


@pytest.mark.parametrize('kind', ['10', '12', 'G6', 'G12'])
def test_sets_parse(kind, tmp_path):
    cabook.make_sets(kind, tmp_path)
    for s in range(6):
        text = (tmp_path / f'Practice_en_Set_0{s + 1}.txt').read_text(encoding='utf-8')
        assert bookgen._set_problem(text, s + 1) is None
        assert text.count('Source: All India Radio News') == 25
