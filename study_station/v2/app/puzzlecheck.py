"""
Seating / ordering puzzle check: a model only *translates* each question's clues into a small JSON form, and a
brute-force solver here tries every arrangement. A question passes only when its clues fit at least one
arrangement and every fitting arrangement gives the same answer — the keyed option.

Why: both AI models (writer and re-solver) regularly agree on puzzle questions whose clues contradict each other
or allow two answers; reading the clues is much easier for a model than solving them.

    problems(ask, text) -> ['Q12: clues contradict each other — no arrangement fits', …]

`ask(system, user)` is the AI call (bookgen passes its budgeted checker call).

Layouts: "row" (places 1..n from the viewer's left), "circle" (places clockwise as seen from above), "line"
(place 1 = bottom / first / earliest / lowest floor / front of a queue). Directions in clues are the persons' own
(a row facing north: their left is the viewer's left; facing south: the viewer's right; a circle facing the centre:
their left is clockwise; facing outside: anticlockwise). A clue may carry "viewer": true when the question says
"as we view it".
"""
import json
import re
from itertools import permutations

from .importers import parse_mcq_text

MAX_PLACES = 9                       # 9! arrangements is still quick; bigger puzzles are skipped
UNDETERMINED = {'cannot be determined', 'cannot be determined uniquely', 'data inadequate', 'none of these'}

FORMALIZE_SYSTEM = """You translate seating and ordering puzzle questions into JSON for a solver program.
Do NOT solve anything and do NOT judge whether the answer key is right — only translate the words faithfully.

Reply with one JSON array; one object per question, in this form:
{"q": 12, "layout": "row" | "circle" | "line" | "skip", "n": 6, "facing": "north" | "south" | "centre" | "outside",
 "people": ["A", "B", ...], "clues": [[...], ...], "ask": [...], "options": {"a": "R", "b": "3", "c": "...", "d": "..."}}

layout: "row" = people in a straight row; "circle" = round/square/hexagonal table; "line" = a vertical stack,
floors, a sequence of days/months/events, a ranking or a queue (place 1 = bottom / first / earliest / lowest /
front). Use "skip" (with just "q") for anything else: blood relations, counting positions from both ends with
no names to place, coding, directions, statements, or when the question cannot be written with the clues below.
n = number of places (seats, floors, days...). people = everyone or everything being placed (names, subjects,
colours...) exactly as written in the options. facing: for rows "north" or "south" (use "north" when not stated),
for circles "centre" or "outside" (use "centre" when not stated); omit for lines.

Clues (left/right are the person's OWN left/right; add "viewer" as a last element when the question says
"as we view it"/"from the viewer's side"):
["left", X, Y, k]        X is k-th to the left of Y (k=1: immediately left)          row, circle
["right", X, Y, k]       X is k-th to the right of Y                                 row, circle
["left_any", X, Y]       X is somewhere to the left of Y                             row
["right_any", X, Y]      X is somewhere to the right of Y                            row
["after", X, Y, k]       X is k places above/after/behind Y (k=null: anywhere above/after)   line
["before", X, Y, k]      X is k places below/before/ahead of Y (k=null: anywhere)            line
["next", X, Y]           X sits next to Y (immediate neighbour)
["opposite", X, Y]       X faces/sits opposite Y (circle; or two facing rows: then write the question as "skip")
["between", X, Y, Z]     X sits immediately between Y and Z (neighbour of both)
["between_any", X, Y, Z] X is somewhere between Y and Z                              row, line
["gap", X, Y, k]         exactly k places between X and Y
["end", X]               X is at one of the ends                                     row, line
["left_end", X]          X at the left end (person's own left)                       row
["right_end", X]         X at the right end                                          row
["place", X, k]          X is k-th from the left end (row) / at place k (line, 1 = bottom/first)
["place_from_right", X, k]   X is k-th from the right end (row) / k-th from the top/last (line)
["not", clue]            the clue is false, e.g. ["not", ["next", "A", "B"]], ["not", ["end", "C"]]

ask (what the question asks):
["who_left", Y, k] / ["who_right", Y, k]   who is k-th to the left/right of Y
["who_after", Y, k] / ["who_before", Y, k] who is k places after/above or before/below Y (line)
["who_opposite", Y]                        who sits opposite Y (circle)
["who_place", k] / ["who_place_from_right", k]   who is at place k from the left end / bottom (or from the right / top)
["who_middle"]                             who is in the middle
["place_of", X] / ["place_from_right_of", X]
["count_between", X, Y]                    how many sit between X and Y
options: the value of each option as plain text — a name from people, a number, or "cannot be determined".
Reply with the JSON array only."""


def _neighbours(layout, n, i, j):
    d = abs(i - j)
    return d == 1 or (layout == 'circle' and d == n - 1)


class Puzzle:
    def __init__(self, spec):
        self.layout = spec['layout']
        self.n = int(spec['n'])
        self.people = [str(p) for p in spec['people']]
        self.facing = (spec.get('facing') or ('centre' if self.layout == 'circle' else 'north')).lower()
        self.clues = spec.get('clues') or []
        self.ask = spec['ask']
        if not 2 <= self.n <= MAX_PLACES or len(self.people) > self.n or len(set(self.people)) != len(self.people):
            raise ValueError('size')

    # place index 0..n-1. Row: viewer's left → right. Circle: clockwise. Line: bottom/first → top/last.
    def _left_step(self, viewer=False):
        """+1 or -1: one step to the person's left, in place indices."""
        if self.layout == 'row':
            return -1 if (viewer or self.facing != 'south') else 1
        if self.layout == 'circle':
            return 1 if self.facing != 'outside' else -1
        raise ValueError('left/right in a line')

    def _step(self, i, k):
        j = i + k
        if self.layout == 'circle':
            return j % self.n
        return j if 0 <= j < self.n else None

    def _holds(self, c, s):
        op, *a = c
        viewer = bool(a) and a[-1] == 'viewer'
        if viewer:
            a = a[:-1]
        if op == 'not':
            return not self._holds(a[0], s)
        p = lambda x: s[str(x)]
        if op in ('left', 'right'):
            k = int(a[2]) if len(a) > 2 and a[2] is not None else 1
            d = self._left_step(viewer) * (1 if op == 'left' else -1)
            return self._step(p(a[1]), d * k) == p(a[0])
        if op in ('left_any', 'right_any'):
            d = self._left_step(viewer) * (1 if op == 'left_any' else -1)
            return (p(a[0]) - p(a[1])) * d > 0
        if op in ('after', 'before'):
            sign = 1 if op == 'after' else -1
            k = a[2] if len(a) > 2 else None
            diff = (p(a[0]) - p(a[1])) * sign
            return diff > 0 if k is None else diff == int(k)
        if op == 'next':
            return _neighbours(self.layout, self.n, p(a[0]), p(a[1]))
        if op == 'opposite':
            return self.layout == 'circle' and self.n % 2 == 0 and (p(a[0]) - p(a[1])) % self.n == self.n // 2
        if op == 'between':
            return all(_neighbours(self.layout, self.n, p(a[0]), p(y)) for y in a[1:3]) and p(a[1]) != p(a[2])
        if op == 'between_any':
            return min(p(a[1]), p(a[2])) < p(a[0]) < max(p(a[1]), p(a[2]))
        if op == 'gap':
            d = abs(p(a[0]) - p(a[1]))
            if self.layout == 'circle':
                d = min(d, self.n - d)
            return d - 1 == int(a[2])
        if op == 'end':
            return p(a[0]) in (0, self.n - 1)
        if op in ('left_end', 'right_end'):
            left_end = 0 if self._left_step(viewer) == -1 else self.n - 1
            return p(a[0]) == (left_end if op == 'left_end' else self.n - 1 - left_end)
        if op in ('place', 'place_from_right'):
            return p(a[0]) == self._place_index(int(a[1]), op == 'place_from_right', viewer)
        raise ValueError(f'unknown clue {op}')

    def _place_index(self, k, from_right=False, viewer=False):
        if self.layout == 'line':
            return self.n - k if from_right else k - 1
        left_first = self.layout != 'row' or self._left_step(viewer) == -1
        i = k - 1 if left_first else self.n - k
        return self.n - 1 - i if from_right else i

    def _answer(self, s):
        who = {v: k for k, v in s.items()}
        op, *a = self.ask
        p = lambda x: s[str(x)]
        at = lambda i: who.get(i) if i is not None else None
        if op in ('who_left', 'who_right'):
            k = int(a[1]) if len(a) > 1 and a[1] is not None else 1
            d = self._left_step() * (1 if op == 'who_left' else -1)
            return at(self._step(p(a[0]), d * k))
        if op in ('who_after', 'who_before'):
            k = int(a[1]) if len(a) > 1 and a[1] is not None else 1
            return at(self._step(p(a[0]), k if op == 'who_after' else -k))
        if op == 'who_opposite':
            return at((p(a[0]) + self.n // 2) % self.n) if self.layout == 'circle' and self.n % 2 == 0 else None
        if op in ('who_place', 'who_place_from_right'):
            return at(self._place_index(int(a[0]), op == 'who_place_from_right'))
        if op == 'who_middle':
            return at(self.n // 2) if self.n % 2 else None
        if op in ('place_of', 'place_from_right_of'):
            i = p(a[0])
            for k in range(1, self.n + 1):
                if self._place_index(k, op == 'place_from_right_of') == i:
                    return str(k)
        if op == 'count_between':
            d = abs(p(a[0]) - p(a[1]))
            return str((min(d, self.n - d) if self.layout == 'circle' else d) - 1)
        raise ValueError(f'unknown ask {op}')

    def answers(self):
        """The set of answers over every arrangement that fits all clues (None = asked place is empty)."""
        out = set()
        places = range(1 if self.layout == 'circle' else 0, self.n)   # circle: first person fixed (rotation)
        rest = self.people[1:] if self.layout == 'circle' else self.people
        for perm in permutations(places, len(rest)):
            s = dict(zip(rest, perm))
            if self.layout == 'circle':
                s[self.people[0]] = 0
            if all(self._holds(c, s) for c in self.clues):
                out.add(self._answer(s))
                if len(out) > 1:
                    break
        return out


def _norm(v):
    return re.sub(r'\s+', ' ', str(v)).strip().strip('.').lower()


def verdict(spec, key_letter):
    """'' when the question is sound, else a short problem description. Raises ValueError when the spec is
    unusable (the question is then not judged)."""
    pz = Puzzle(spec)
    opts = {k.lower(): _norm(v) for k, v in (spec.get('options') or {}).items()}
    if sorted(opts) != ['a', 'b', 'c', 'd']:
        raise ValueError('options')
    got = pz.answers()
    if not got:
        return 'clues contradict each other — no arrangement fits all of them'
    undetermined = [k for k, v in opts.items() if v in UNDETERMINED]
    if len(got) > 1 or None in got:
        if key_letter in undetermined:
            return ''
        return 'the clues allow more than one answer — add a clue so exactly one arrangement fits'
    ans = _norm(next(iter(got)))
    match = [k for k, v in opts.items() if v == ans or v.removesuffix('th').removesuffix('rd').removesuffix('nd')
             .removesuffix('st') == ans]
    if not match:
        return f'the clues give "{ans}", which is not among the options'
    if key_letter not in match:
        return f'the clues give "{ans}" (option {match[0]}), but the key says ({key_letter})'
    return ''


CHUNK = 7                            # questions per model call: a whole set of JSON is too long for one answer


def formalize_request(text, qs=None):
    qs = parse_mcq_text(text) if qs is None else qs
    body = '\n\n'.join(f'{q.number}. {q.text}\n' + ' '.join(f'({l}) {o}' for l, o in zip('abcd', q.options))
                       for q in qs)
    return f'<questions>\n{body}\n</questions>\n\nTranslate every question above (one JSON object each).'


def _parse_json_array(answer):
    m = re.search(r'\[.*\]', answer, re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except ValueError:
        return []
    return [d for d in data if isinstance(d, dict) and 'q' in d]


def problems(ask, text):
    """Per-question problems of a practice set: ['Q12: …']. Questions the model skips are not judged."""
    qs = parse_mcq_text(text)
    keys = {q.number: 'abcd'[q.answer_index] for q in qs}
    specs = []
    for i in range(0, len(qs), CHUNK):
        chunk = qs[i:i + CHUNK]
        nums = {str(q.number) for q in chunk}
        specs += [s for s in _parse_json_array(ask(FORMALIZE_SYSTEM, formalize_request(text, chunk)))
                  if str(s.get('q')) in nums]
    out = []
    for spec in specs:
        try:
            q = int(spec['q'])
            if spec.get('layout') == 'skip' or q not in keys:
                continue
            why = verdict(spec, keys[q])
        except (ValueError, KeyError, TypeError, IndexError):
            continue
        if why:
            out.append(f'Q{q}: {why}')
    return out
