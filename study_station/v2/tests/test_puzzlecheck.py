from app.puzzlecheck import Puzzle, problems, verdict

ROW = {'layout': 'row', 'n': 5, 'facing': 'north', 'people': list('PQRST')}


def spec(**kw):
    return {**ROW, **kw}


def test_contradictory_clues_are_reported():
    # Q on the left of R, S second right of P, T at the right end next to S: no seats left for Q-R side by side
    s = spec(clues=[['left', 'Q', 'R', 1], ['right', 'S', 'P', 2], ['right_end', 'T'], ['next', 'T', 'S']],
             ask=['who_middle'], options={'a': 'R', 'b': 'P', 'c': 'Q', 'd': 'S'})
    assert 'no arrangement' in verdict(s, 'a')


def test_two_answers_are_reported_and_undetermined_option_accepted():
    s = spec(clues=[['left_end', 'P']], ask=['who_place', 2],
             options={'a': 'Q', 'b': 'R', 'c': 'S', 'd': 'cannot be determined'})
    assert 'more than one answer' in verdict(s, 'a')
    assert verdict(s, 'd') == ''


def test_wrong_key_and_correct_key():
    s = spec(clues=[['place', 'P', 1], ['right', 'Q', 'P', 1], ['right', 'R', 'Q', 1], ['right', 'S', 'R', 1]],
             ask=['who_place_from_right', 1], options={'a': 'S', 'b': 'T', 'c': 'R', 'd': 'Q'})
    assert verdict(s, 'b') == ''
    assert 'key says (a)' in verdict(s, 'a')


def test_facing_south_reverses_left_and_right():
    s = spec(facing='south', clues=[['left_end', 'P'], ['left', 'Q', 'P', 1]], ask=['place_of', 'Q'],
             options={'a': '1', 'b': '2', 'c': '4', 'd': '5'})
    # P at their left end = viewer's right (place 5 from the viewer's left = 1st from their left); Q next on their left?
    assert Puzzle(s).answers() == set()                     # nothing is further left than the left end


def test_circle_facing_centre_left_is_clockwise():
    s = {'layout': 'circle', 'n': 6, 'facing': 'centre', 'people': list('ABCDEF'),
         'clues': [['opposite', 'A', 'D'], ['left', 'B', 'A', 2], ['left', 'C', 'D', 1], ['left', 'E', 'A', 1]],
         'ask': ['who_opposite', 'B'], 'options': {'a': 'C', 'b': 'E', 'c': 'F', 'd': 'D'}}
    assert verdict(s, 'c') == ''


def test_problems_uses_the_model_translation_only():
    text = ('1. Five persons sit in a row facing north. P is at the left end. Who sits second from the left?\n'
            '(a) Q (b) R (c) S (d) cannot be determined\nAnswer: (a)\nSolution: Not fixed, so the answer is Q.\n'
            'Source: PYQ-style\n')
    reply = ('[{"q": 1, "layout": "row", "n": 5, "facing": "north", "people": ["P","Q","R","S","T"], '
             '"clues": [["left_end", "P"]], "ask": ["who_place", 2], '
             '"options": {"a": "Q", "b": "R", "c": "S", "d": "cannot be determined"}}]')
    assert problems(lambda system, user: reply, text) == [
        'Q1: the clues allow more than one answer — add a clue so exactly one arrangement fits']
    assert problems(lambda system, user: '[{"q": 1, "layout": "skip"}]', text) == []
    assert problems(lambda system, user: 'no json here', text) == []
