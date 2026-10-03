from app.importers import (answer_conflicts_with_solution, is_translation_pair, parse_mcq_text,
                           quality_problem)

SAMPLE_EN = """Set 1: Analogy MCQs (English)
Questions 1–2: Easy | Questions 3–3: Medium

Q1. Cow : Calf :: Dog : ?
(a) Kitten (b) Puppy (c) Cub (d) Foal
Answer: (b) Puppy
Solution: The young one of a dog is a puppy.
Source: SSC MTS

2. What is 20% of 150?
(A) 20
(B) 30
(C) 40
(D) 50
**Answer:** (B) 30
Solution: 0.2 × 150 = 30.
2. Then check the units.
Source: NCERT Class 7

3. Broken question with only two options
(a) 1 (b) 2
Answer: (a)
"""


def test_parses_both_layouts_and_drops_broken():
    qs = parse_mcq_text(SAMPLE_EN)
    assert [q.number for q in qs] == [1, 2]
    q1, q2 = qs
    assert q1.text == 'Cow : Calf :: Dog : ?'
    assert q1.options == ['Kitten', 'Puppy', 'Cub', 'Foal'] and q1.answer_index == 1
    assert q1.difficulty == 'easy' and q1.source_claim == 'SSC MTS'
    assert q2.options == ['20', '30', '40', '50'] and q2.answer_index == 1
    assert 'Then check the units' in q2.solution     # "2." inside a solution is not a new question


def test_hindi_and_inline_difficulty():
    text = "26. (मध्यम) संविधान सभा की मसौदा समिति का गठन कब हुआ?\n(a) 1946\n(b) 1947\n(c) 1949\n(d) 1950\nउत्तर: (b)\nहल: 29 अगस्त 1947।\nस्रोत: SSC CGL 2020\n"
    [q] = parse_mcq_text(text)
    assert q.difficulty == 'medium' and q.answer_index == 1
    assert q.text.startswith('संविधान')


def test_garbled_math_is_dropped():
    text = "Q1. Simplify:\n3\n4\n+\n5\n6\n(a) 1 (b) 2 (c) 3 (d) 4\nAnswer: (a)\n"
    assert parse_mcq_text(text) == []


def test_quality_checks():
    [q] = parse_mcq_text("1. Find x.\n(a) 10 (b) 12 (c) 16 (d) 20\nAnswer: (c)\nSolution: 7x = 84 so x = 12.\n")
    assert answer_conflicts_with_solution(q)
    assert quality_problem(q) == 'answer_solution_conflict'
    [q] = parse_mcq_text("1. Find y.\n(a) 10 (b) 12 (c) 16 (d) 20\nAnswer: (b)\nSolution: Nice! So answer 12. I'll make that Q122.\n")
    assert quality_problem(q) == 'leaked_reasoning'
    [q] = parse_mcq_text("1. (Also from same arrangement, another question) Who sits third?\n(a) A (b) B (c) C (d) D\nAnswer: (a)\n")
    assert quality_problem(q) == 'needs_context'


def test_translation_pairing():
    en = parse_mcq_text("1. 20% of 150 is?\n(a) 20 (b) 30 (c) 40 (d) 50\nAnswer: (b)\n")[0]
    hi = parse_mcq_text("1. 150 का 20% कितना है?\n(a) 20 (b) 30 (c) 40 (d) 50\nउत्तर: (b)\n")[0]
    other = parse_mcq_text("1. 25 का 10% कितना है?\n(a) 2.5 (b) 5 (c) 10 (d) 25\nउत्तर: (a)\n")[0]
    assert is_translation_pair(en, hi)
    assert not is_translation_pair(en, other)
