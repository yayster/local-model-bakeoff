"""The sixteen rungs of ladder v2.

Each rung is a small Python project with a bug, a gold fix, public tests the
model can run, hidden tests that score it, a structured list of examples that
is rendered into the spec and checked against the gold, and one or more traps:
plausible wrong fixes that the hidden tests must reject.

Difficulty rises from a one-line off-by-one to rungs that need the model to
act on a non-functional requirement and to hold the spec above a wrong test.
"""

from __future__ import annotations

import hashlib
import json
from textwrap import dedent

RUNGS: list[dict] = []


def rung(id, level, title, skill, rules, examples, files_buggy, files_gold, public, hidden,
         traps, public_passes_on_bug=True, gold_passes_public=True, note="", max_turns=10,
         test_timeout=10.0, prelude=""):
    spec = render_spec(rules, examples, prelude)
    RUNGS.append({
        "id": id,
        "level": level,
        "title": title,
        "skill": skill,
        "rules": dedent(rules).strip(),
        "examples": examples,
        "prelude": prelude,
        "spec": spec,
        "files_buggy": {k: dedent(v).lstrip("\n") for k, v in files_buggy.items()},
        "files_gold": {k: dedent(v).lstrip("\n") for k, v in files_gold.items()},
        "public": dedent(public).lstrip("\n"),
        "hidden": dedent(hidden).lstrip("\n"),
        "traps": {name: {k: dedent(v).lstrip("\n") for k, v in files.items()} for name, files in traps.items()},
        "public_passes_on_bug": public_passes_on_bug,
        "gold_passes_public": gold_passes_public,
        "note": dedent(note).strip(),
        "max_turns": max_turns,
        "test_timeout": test_timeout,
        "hidden_n": dedent(hidden).count("def test_"),
    })


def render_spec(rules: str, examples: list, prelude: str) -> str:
    parts = [" ".join(dedent(rules).split())]
    if examples:
        head = "Examples are Python"
        if prelude:
            head += f" after `{prelude}`"
        parts.append(head + ".")
    for ex in examples:
        if "text" in ex:
            parts.append(ex["text"])
            continue
        lead = f"With {ex['setup']}, " if ex.get("setup") else ""
        if "raises" in ex:
            parts.append(f"{lead}{ex['call']} raises {ex['raises']}.")
        else:
            parts.append(f"{lead}{ex['call']} is {ex['expect']}.")
    return " ".join(parts)


def tests(body: str) -> str:
    """A unittest file: the import, the dedented body, and a main guard."""
    return "import unittest\n" + dedent(body).lstrip("\n") + "\nif __name__ == '__main__':\n    unittest.main()\n"


# --------------------------------------------------------------------------- 1
rung(
    "pages", 1, "Pages", "off-by-one, red public test",
    """
    page_count(items, per_page) returns how many pages are needed to show items things
    with per_page on each page. A partial last page counts as a page. Zero items need
    zero pages. per_page is at least 1.
    """,
    [
        {"call": "page_count(10, 3)", "expect": "4"},
        {"call": "page_count(9, 3)", "expect": "3"},
        {"call": "page_count(0, 5)", "expect": "0"},
        {"call": "page_count(1, 100)", "expect": "1"},
    ],
    {"mod.py": """
        def page_count(items, per_page):
            return items // per_page
    """},
    {"mod.py": """
        def page_count(items, per_page):
            return (items + per_page - 1) // per_page
    """},
    tests("""
    from mod import page_count
    class T(unittest.TestCase):
        def test_partial(self):
            self.assertEqual(page_count(10, 3), 4)
    """),
    tests("""
    from mod import page_count
    class T(unittest.TestCase):
        def test_exact(self):
            self.assertEqual(page_count(9, 3), 3)
            self.assertEqual(page_count(100, 10), 10)
        def test_zero(self):
            self.assertEqual(page_count(0, 5), 0)
        def test_one(self):
            self.assertEqual(page_count(1, 100), 1)
            self.assertEqual(page_count(10, 3), 4)
    """),
    {
        "plus_one": {"mod.py": """
            def page_count(items, per_page):
                return items // per_page + 1
        """},
        "add_full_page": {"mod.py": """
            def page_count(items, per_page):
                return (items + per_page) // per_page
        """},
    },
    public_passes_on_bug=False, max_turns=8,
)

# --------------------------------------------------------------------------- 2
rung(
    "slug", 2, "Slug", "edge cases of a one-liner",
    """
    slugify(text) lowercases text, replaces every run of characters that are not ASCII
    letters or digits with a single hyphen, and removes hyphens from both ends.
    A letter outside ASCII is not a letter here: a run of them becomes a hyphen like
    any other run.
    """,
    [
        {"call": "slugify('Hello World')", "expect": "'hello-world'"},
        {"call": "slugify('  A--b  ')", "expect": "'a-b'"},
        {"call": "slugify('x')", "expect": "'x'"},
        {"call": "slugify('!!!')", "expect": "''"},
        {"call": "slugify('café')", "expect": "'caf'"},
        {"call": "slugify('naïve')", "expect": "'na-ve'"},
    ],
    {"mod.py": """
        import re

        def slugify(text):
            return re.sub(r'[^a-z0-9]', '-', text.lower())
    """},
    {"mod.py": """
        import re

        def slugify(text):
            return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    """},
    tests("""
    from mod import slugify
    class T(unittest.TestCase):
        def test_words(self):
            self.assertEqual(slugify('Hello World'), 'hello-world')
            self.assertEqual(slugify('a-b'), 'a-b')
    """),
    tests("""
    from mod import slugify
    class T(unittest.TestCase):
        def test_runs(self):
            self.assertEqual(slugify('  A--b  '), 'a-b')
            self.assertEqual(slugify('Rock & Roll'), 'rock-roll')
            self.assertEqual(slugify('a_b'), 'a-b')
        def test_ends(self):
            self.assertEqual(slugify('!!!'), '')
            self.assertEqual(slugify('-x-'), 'x')
            self.assertEqual(slugify('x'), 'x')
        def test_non_ascii(self):
            self.assertEqual(slugify('café'), 'caf')
            self.assertEqual(slugify('Ünïcode'), 'n-code')
            self.assertEqual(slugify('naïve'), 'na-ve')
    """),
    {
        "no_strip": {"mod.py": """
            import re

            def slugify(text):
                return re.sub(r'[^a-z0-9]+', '-', text.lower())
        """},
        "unicode_word": {"mod.py": """
            import re

            def slugify(text):
                return re.sub(r'\\W+', '-', text.lower()).strip('-')
        """},
    },
    max_turns=8,
)

# --------------------------------------------------------------------------- 3
rung(
    "semver", 3, "Versions", "parsing and ordering",
    """
    compare_versions(a, b) returns -1, 0, or 1 when version a is lower than, equal to,
    or higher than version b. A version is dot-separated non-negative integers compared
    numerically from the left. A missing trailing component counts as 0. A version may
    end in a hyphen and a pre-release label, like 1.0.0-beta. A pre-release sorts
    before the same numeric version without a label. Two labels on the same numeric
    version compare as plain strings.
    """,
    [
        {"call": "compare_versions('1.10', '1.9')", "expect": "1"},
        {"call": "compare_versions('1.2', '1.2.0')", "expect": "0"},
        {"call": "compare_versions('1.2.1', '1.2')", "expect": "1"},
        {"call": "compare_versions('1.0.0-beta', '1.0.0')", "expect": "-1"},
        {"call": "compare_versions('1.0.0-alpha', '1.0.0-beta')", "expect": "-1"},
        {"call": "compare_versions('2.0-rc1', '1.9.9')", "expect": "1"},
    ],
    {"mod.py": """
        def compare_versions(a, b):
            xs = [int(p) for p in a.split('.')]
            ys = [int(p) for p in b.split('.')]
            for x, y in zip(xs, ys):
                if x != y:
                    return -1 if x < y else 1
            return 0
    """},
    {"mod.py": """
        def _parse(version):
            core, _, label = version.partition('-')
            return [int(p) for p in core.split('.')], label

        def compare_versions(a, b):
            xs, la = _parse(a)
            ys, lb = _parse(b)
            n = max(len(xs), len(ys))
            xs += [0] * (n - len(xs))
            ys += [0] * (n - len(ys))
            if xs != ys:
                return -1 if xs < ys else 1
            if la == lb:
                return 0
            if not la:
                return 1
            if not lb:
                return -1
            return -1 if la < lb else 1
    """},
    tests("""
    from mod import compare_versions
    class T(unittest.TestCase):
        def test_numeric(self):
            self.assertEqual(compare_versions('1.10', '1.9'), 1)
            self.assertEqual(compare_versions('1.2.3', '1.2.3'), 0)
            self.assertEqual(compare_versions('0.9', '1.0'), -1)
    """),
    tests("""
    from mod import compare_versions
    class T(unittest.TestCase):
        def test_padding(self):
            self.assertEqual(compare_versions('1.2.1', '1.2'), 1)
            self.assertEqual(compare_versions('1.2', '1.2.0'), 0)
            self.assertEqual(compare_versions('1', '1.0.0.1'), -1)
        def test_prerelease_before_release(self):
            self.assertEqual(compare_versions('1.0.0-beta', '1.0.0'), -1)
            self.assertEqual(compare_versions('1.0.0', '1.0.0-beta'), 1)
            self.assertEqual(compare_versions('2.0-rc1', '1.9.9'), 1)
        def test_labels(self):
            self.assertEqual(compare_versions('1.0.0-alpha', '1.0.0-beta'), -1)
            self.assertEqual(compare_versions('1.0.0-rc', '1.0.0-rc'), 0)
            self.assertEqual(compare_versions('1.0-b', '1.0.0-a'), 1)
    """),
    {
        "prerelease_after": {"mod.py": """
            def _parse(version):
                core, _, label = version.partition('-')
                return [int(p) for p in core.split('.')], label

            def compare_versions(a, b):
                xs, la = _parse(a)
                ys, lb = _parse(b)
                n = max(len(xs), len(ys))
                xs += [0] * (n - len(xs))
                ys += [0] * (n - len(ys))
                if xs != ys:
                    return -1 if xs < ys else 1
                if la == lb:
                    return 0
                return -1 if la < lb else 1
        """},
        "label_ignored": {"mod.py": """
            def compare_versions(a, b):
                xs = [int(p) for p in a.split('-')[0].split('.')]
                ys = [int(p) for p in b.split('-')[0].split('.')]
                n = max(len(xs), len(ys))
                xs += [0] * (n - len(xs))
                ys += [0] * (n - len(ys))
                if xs != ys:
                    return -1 if xs < ys else 1
                return 0
        """},
    },
    max_turns=8,
)

# --------------------------------------------------------------------------- 4
rung(
    "intervals", 4, "Intervals", "algorithm invariants",
    """
    merge(intervals) takes a list of (start, end) tuples with start <= end, in any
    order, and returns a new sorted list of tuples in which every group of overlapping
    or touching intervals has become one tuple. Touching means one interval ends where
    another starts. The input list is left as it was.
    """,
    [
        {"call": "merge([(1, 3), (2, 6), (8, 10)])", "expect": "[(1, 6), (8, 10)]"},
        {"call": "merge([(5, 6), (1, 2)])", "expect": "[(1, 2), (5, 6)]"},
        {"call": "merge([(1, 3), (3, 5)])", "expect": "[(1, 5)]"},
        {"call": "merge([])", "expect": "[]"},
    ],
    {"mod.py": """
        def merge(intervals):
            out = []
            for start, end in intervals:
                if out and start < out[-1][1]:
                    out[-1] = (out[-1][0], max(out[-1][1], end))
                else:
                    out.append((start, end))
            return out
    """},
    {"mod.py": """
        def merge(intervals):
            out = []
            for start, end in sorted(intervals):
                if out and start <= out[-1][1]:
                    out[-1] = (out[-1][0], max(out[-1][1], end))
                else:
                    out.append((start, end))
            return out
    """},
    tests("""
    from mod import merge
    class T(unittest.TestCase):
        def test_overlap(self):
            self.assertEqual(merge([(1, 3), (2, 6), (8, 10)]), [(1, 6), (8, 10)])
            self.assertEqual(merge([(1, 4), (2, 3)]), [(1, 4)])
    """),
    tests("""
    from mod import merge
    class T(unittest.TestCase):
        def test_touch(self):
            self.assertEqual(merge([(1, 3), (3, 5)]), [(1, 5)])
            self.assertEqual(merge([(1, 2), (2, 3), (3, 4)]), [(1, 4)])
        def test_unsorted(self):
            self.assertEqual(merge([(5, 6), (1, 2)]), [(1, 2), (5, 6)])
            self.assertEqual(merge([(4, 6), (1, 5)]), [(1, 6)])
            self.assertEqual(merge([(7, 9), (1, 2), (8, 12), (2, 3)]), [(1, 3), (7, 12)])
        def test_empty(self):
            self.assertEqual(merge([]), [])
        def test_input_untouched(self):
            xs = [(5, 6), (1, 2)]
            merge(xs)
            self.assertEqual(xs, [(5, 6), (1, 2)])
    """),
    {
        "strict": {"mod.py": """
            def merge(intervals):
                out = []
                for start, end in sorted(intervals):
                    if out and start < out[-1][1]:
                        out[-1] = (out[-1][0], max(out[-1][1], end))
                    else:
                        out.append((start, end))
                return out
        """},
        "no_sort": {"mod.py": """
            def merge(intervals):
                out = []
                for start, end in intervals:
                    if out and start <= out[-1][1]:
                        out[-1] = (out[-1][0], max(out[-1][1], end))
                    else:
                        out.append((start, end))
                return out
        """},
        "in_place": {"mod.py": """
            def merge(intervals):
                intervals.sort()
                out = []
                for start, end in intervals:
                    if out and start <= out[-1][1]:
                        out[-1] = (out[-1][0], max(out[-1][1], end))
                    else:
                        out.append((start, end))
                return out
        """},
    },
    max_turns=8,
)

# --------------------------------------------------------------------------- 5
rung(
    "lru", 5, "LRU cache", "stateful semantics",
    """
    LRU(capacity) is a cache holding at most capacity entries; capacity is at least 1.
    put(key, value) stores a value. get(key) returns the stored value, or None when the
    key is absent. A get of a present key and every put make that key the most recently
    used. When put adds a new key to a full cache, the least recently used key is
    removed first. Updating a key that is already present never removes anything.
    A get of an absent key changes nothing. keys() lists the keys from least recently
    used to most recently used.
    """,
    [
        {"setup": "c = LRU(2); c.put('a', 1); c.put('b', 2); c.get('a'); c.put('c', 3)",
         "call": "c.keys()", "expect": "['a', 'c']"},
        {"setup": "c = LRU(2); c.put('a', 1); c.put('b', 2); c.get('a'); c.put('c', 3)",
         "call": "c.get('b')", "expect": "None"},
        {"setup": "c = LRU(2); c.put('a', 1); c.put('b', 2); c.put('a', 9); c.put('c', 3)",
         "call": "c.keys()", "expect": "['a', 'c']"},
        {"setup": "c = LRU(1); c.put('a', 1); c.put('b', 2)", "call": "c.get('a')", "expect": "None"},
    ],
    {"mod.py": """
        class LRU:
            def __init__(self, capacity):
                self.capacity = capacity
                self.data = {}

            def get(self, key):
                return self.data.get(key)

            def put(self, key, value):
                self.data[key] = value
                if len(self.data) > self.capacity:
                    oldest = next(iter(self.data))
                    del self.data[oldest]

            def keys(self):
                return list(self.data)
    """},
    {"mod.py": """
        from collections import OrderedDict


        class LRU:
            def __init__(self, capacity):
                self.capacity = capacity
                self.data = OrderedDict()

            def get(self, key):
                if key not in self.data:
                    return None
                self.data.move_to_end(key)
                return self.data[key]

            def put(self, key, value):
                self.data[key] = value
                self.data.move_to_end(key)
                if len(self.data) > self.capacity:
                    self.data.popitem(last=False)

            def keys(self):
                return list(self.data)
    """},
    tests("""
    from mod import LRU
    class T(unittest.TestCase):
        def test_evicts_oldest(self):
            c = LRU(2)
            c.put('a', 1)
            c.put('b', 2)
            c.put('c', 3)
            self.assertIsNone(c.get('a'))
            self.assertEqual(c.get('c'), 3)
            self.assertEqual(c.keys(), ['b', 'c'])
    """),
    tests("""
    from mod import LRU
    class T(unittest.TestCase):
        def test_get_refreshes(self):
            c = LRU(2)
            c.put('a', 1)
            c.put('b', 2)
            self.assertEqual(c.get('a'), 1)
            c.put('c', 3)
            self.assertIsNone(c.get('b'))
            self.assertEqual(c.keys(), ['a', 'c'])
        def test_put_refreshes_existing(self):
            c = LRU(2)
            c.put('a', 1)
            c.put('b', 2)
            c.put('a', 9)
            self.assertEqual(c.keys(), ['b', 'a'])
            c.put('c', 3)
            self.assertEqual(c.keys(), ['a', 'c'])
            self.assertEqual(c.get('a'), 9)
        def test_capacity_one(self):
            c = LRU(1)
            c.put('a', 1)
            c.put('b', 2)
            self.assertIsNone(c.get('a'))
            self.assertEqual(c.get('b'), 2)
        def test_missing_get_has_no_side_effect(self):
            c = LRU(2)
            c.put('a', 1)
            c.put('b', 2)
            self.assertIsNone(c.get('z'))
            c.put('c', 3)
            self.assertEqual(c.keys(), ['b', 'c'])
        def test_update_never_evicts(self):
            c = LRU(2)
            c.put('a', 1)
            c.put('b', 2)
            c.put('a', 9)
            self.assertEqual(len(c.keys()), 2)
            self.assertEqual(c.get('b'), 2)
    """),
    {
        "get_only": {"mod.py": """
            from collections import OrderedDict


            class LRU:
                def __init__(self, capacity):
                    self.capacity = capacity
                    self.data = OrderedDict()

                def get(self, key):
                    if key not in self.data:
                        return None
                    self.data.move_to_end(key)
                    return self.data[key]

                def put(self, key, value):
                    self.data[key] = value
                    if len(self.data) > self.capacity:
                        self.data.popitem(last=False)

                def keys(self):
                    return list(self.data)
        """},
        "pop_default": {"mod.py": """
            class LRU:
                def __init__(self, capacity):
                    self.capacity = capacity
                    self.data = {}

                def get(self, key):
                    value = self.data.pop(key, None)
                    self.data[key] = value
                    return value

                def put(self, key, value):
                    self.data.pop(key, None)
                    self.data[key] = value
                    if len(self.data) > self.capacity:
                        del self.data[next(iter(self.data))]

                def keys(self):
                    return list(self.data)
        """},
    },
)

# --------------------------------------------------------------------------- 6
rung(
    "bucket", 6, "Token bucket", "time and float accounting",
    """
    Bucket(rate, burst) is a token bucket that starts full with burst tokens and
    refills at rate tokens per second, never holding more than burst.
    allow(now, cost=1) first adds the tokens earned since the previous call, using the
    float timestamp now (calls never go backwards in time), then returns True and
    removes cost tokens when at least cost tokens are present, or returns False and
    removes nothing. The clock starts at 0. Fractions of a token accumulate.
    """,
    [
        {"setup": "b = Bucket(1, 2); b.allow(0); b.allow(0)", "call": "b.allow(0)", "expect": "False"},
        {"setup": "b = Bucket(1, 2); b.allow(0); b.allow(0); b.allow(0.5)", "call": "b.allow(1.0)", "expect": "True"},
        {"setup": "b = Bucket(2, 5); b.allow(0, 5); b.allow(1, 3)", "call": "b.allow(1.5, 3)", "expect": "True"},
        {"setup": "b = Bucket(1, 2); b.allow(0, 2)", "call": "b.allow(100, 3)", "expect": "False"},
    ],
    {"mod.py": """
        class Bucket:
            def __init__(self, rate, burst):
                self.rate = rate
                self.burst = burst
                self.tokens = burst
                self.last = 0.0

            def allow(self, now, cost=1):
                self.tokens += int((now - self.last) * self.rate)
                self.last = now
                if self.tokens >= cost:
                    self.tokens -= cost
                    return True
                return False
    """},
    {"mod.py": """
        class Bucket:
            def __init__(self, rate, burst):
                self.rate = rate
                self.burst = burst
                self.tokens = float(burst)
                self.last = 0.0

            def allow(self, now, cost=1):
                self.tokens = min(self.burst, self.tokens + (now - self.last) * self.rate)
                self.last = now
                if self.tokens >= cost:
                    self.tokens -= cost
                    return True
                return False
    """},
    tests("""
    from mod import Bucket
    class T(unittest.TestCase):
        def test_burst_then_refill(self):
            b = Bucket(1, 2)
            self.assertTrue(b.allow(0))
            self.assertTrue(b.allow(0))
            self.assertFalse(b.allow(0))
            self.assertTrue(b.allow(5))
    """),
    tests("""
    from mod import Bucket
    class T(unittest.TestCase):
        def test_fractions_accumulate(self):
            b = Bucket(1, 2)
            b.allow(0)
            b.allow(0)
            self.assertFalse(b.allow(0.5))
            self.assertFalse(b.allow(0.9))
            self.assertTrue(b.allow(1.0))
        def test_cap(self):
            b = Bucket(1, 2)
            b.allow(0)
            b.allow(0)
            self.assertTrue(b.allow(10))
            self.assertTrue(b.allow(10))
            self.assertFalse(b.allow(10))
        def test_cost(self):
            b = Bucket(1, 2)
            self.assertTrue(b.allow(0, 2))
            self.assertFalse(b.allow(0.5, 1))
            self.assertTrue(b.allow(1.0, 1))
            b2 = Bucket(2, 5)
            self.assertTrue(b2.allow(0, 5))
            self.assertFalse(b2.allow(1, 3))
            self.assertTrue(b2.allow(1.5, 3))
        def test_cost_above_burst(self):
            b = Bucket(1, 2)
            self.assertFalse(b.allow(100, 3))
            self.assertTrue(b.allow(100, 2))
        def test_slow_rate(self):
            b = Bucket(0.5, 1)
            self.assertTrue(b.allow(0))
            self.assertFalse(b.allow(1))
            self.assertTrue(b.allow(2))
    """),
    {
        "no_cap": {"mod.py": """
            class Bucket:
                def __init__(self, rate, burst):
                    self.rate = rate
                    self.burst = burst
                    self.tokens = float(burst)
                    self.last = 0.0

                def allow(self, now, cost=1):
                    self.tokens += (now - self.last) * self.rate
                    self.last = now
                    if self.tokens >= cost:
                        self.tokens -= cost
                        return True
                    return False
        """},
        "charge_on_fail": {"mod.py": """
            class Bucket:
                def __init__(self, rate, burst):
                    self.rate = rate
                    self.burst = burst
                    self.tokens = float(burst)
                    self.last = 0.0

                def allow(self, now, cost=1):
                    self.tokens = min(self.burst, self.tokens + (now - self.last) * self.rate)
                    self.last = now
                    self.tokens -= cost
                    return self.tokens >= 0
        """},

        "double_count": {"mod.py": """
            class Bucket:
                def __init__(self, rate, burst):
                    self.rate = rate
                    self.burst = burst
                    self.tokens = float(burst)
                    self.last = 0.0

                def allow(self, now, cost=1):
                    self.tokens = min(self.burst, self.tokens + (now - self.last) * self.rate)
                    if self.tokens >= cost:
                        self.tokens -= cost
                        self.last = now
                        return True
                    return False
        """},
    },
)

# --------------------------------------------------------------------------- 7
rung(
    "config", 7, "Layered config", "two files, type coercion",
    """
    load(defaults, file_values, env) builds a settings dict with exactly the keys of
    defaults. For each key the value comes from env (a dict keyed by the key in upper
    case, whose values are strings) when present, else from file_values when present,
    else from defaults. Values from file_values are already typed and are used as they
    are. A value from env is converted by coerce(value, like) in coerce.py to the type
    of the default: for a bool default, true, yes, on, and 1 in any letter case mean
    True, and false, no, off, and 0 mean False, and anything else raises ValueError;
    for an int default, int(value); for a str default, the string unchanged. Keys in
    env or file_values that are not in defaults are ignored. The bug is not necessarily
    in mod.py.
    """,
    [
        {"call": "load({'port': 80}, {}, {'PORT': '8080'})", "expect": "{'port': 8080}"},
        {"call": "load({'debug': False}, {}, {'DEBUG': 'yes'})", "expect": "{'debug': True}"},
        {"call": "load({'debug': True}, {}, {'DEBUG': 'FALSE'})", "expect": "{'debug': False}"},
        {"call": "load({'debug': True}, {'debug': False}, {})", "expect": "{'debug': False}"},
        {"call": "load({'name': 'a'}, {'name': 'b'}, {'NAME': 'c'})", "expect": "{'name': 'c'}"},
        {"call": "load({'debug': False}, {}, {'DEBUG': 'maybe'})", "raises": "ValueError"},
    ],
    {
        "mod.py": """
            from coerce import coerce


            def load(defaults, file_values, env):
                out = {}
                for key, default in defaults.items():
                    if key.upper() in env:
                        out[key] = coerce(env[key.upper()], default)
                    elif key in file_values:
                        out[key] = file_values[key]
                    else:
                        out[key] = default
                return out
        """,
        "coerce.py": """
            def coerce(value, like):
                if isinstance(like, int):
                    return int(value)
                if isinstance(like, bool):
                    return bool(value)
                return value
        """,
    },
    {
        "mod.py": """
            from coerce import coerce


            def load(defaults, file_values, env):
                out = {}
                for key, default in defaults.items():
                    if key.upper() in env:
                        out[key] = coerce(env[key.upper()], default)
                    elif key in file_values:
                        out[key] = file_values[key]
                    else:
                        out[key] = default
                return out
        """,
        "coerce.py": """
            TRUE = {'true', 'yes', 'on', '1'}
            FALSE = {'false', 'no', 'off', '0'}


            def coerce(value, like):
                if isinstance(like, bool):
                    word = value.lower()
                    if word in TRUE:
                        return True
                    if word in FALSE:
                        return False
                    raise ValueError(f'not a boolean: {value!r}')
                if isinstance(like, int):
                    return int(value)
                return value
        """,
    },
    tests("""
    from mod import load
    class T(unittest.TestCase):
        def test_int_and_str(self):
            self.assertEqual(load({'port': 80}, {}, {'PORT': '8080'}), {'port': 8080})
            self.assertEqual(load({'name': 'a'}, {'name': 'b'}, {'NAME': 'c'}), {'name': 'c'})
            self.assertEqual(load({'name': 'a'}, {'name': 'b'}, {}), {'name': 'b'})
    """),
    tests("""
    from mod import load
    from coerce import coerce
    class T(unittest.TestCase):
        def test_bool_words(self):
            self.assertEqual(load({'debug': False}, {}, {'DEBUG': 'yes'}), {'debug': True})
            self.assertEqual(load({'debug': True}, {}, {'DEBUG': 'FALSE'}), {'debug': False})
            self.assertEqual(load({'debug': True}, {}, {'DEBUG': 'off'}), {'debug': False})
            self.assertEqual(load({'debug': False}, {}, {'DEBUG': '1'}), {'debug': True})
            self.assertEqual(load({'debug': False}, {}, {'DEBUG': 'On'}), {'debug': True})
        def test_coerce_direct(self):
            self.assertIs(coerce('0', True), False)
            self.assertIs(coerce('Yes', False), True)
            self.assertEqual(coerce('7', 0), 7)
            self.assertEqual(coerce('x', ''), 'x')
        def test_bool_bad_word(self):
            with self.assertRaises(ValueError):
                load({'debug': False}, {}, {'DEBUG': 'maybe'})
        def test_file_bool_used_as_is(self):
            self.assertEqual(load({'debug': True}, {'debug': False}, {}), {'debug': False})
        def test_extra_keys_ignored(self):
            self.assertEqual(load({'a': 1}, {'b': 2}, {'C': '3'}), {'a': 1})
        def test_env_over_file_int(self):
            self.assertEqual(load({'n': 1}, {'n': 2}, {'N': '3'}), {'n': 3})
            self.assertEqual(load({'n': 1}, {'n': 2}, {}), {'n': 2})
    """),
    {
        "bool_builtin": {
            "mod.py": """
                from coerce import coerce


                def load(defaults, file_values, env):
                    out = {}
                    for key, default in defaults.items():
                        if key.upper() in env:
                            out[key] = coerce(env[key.upper()], default)
                        elif key in file_values:
                            out[key] = file_values[key]
                        else:
                            out[key] = default
                    return out
            """,
            "coerce.py": """
                def coerce(value, like):
                    if isinstance(like, bool):
                        return bool(value)
                    if isinstance(like, int):
                        return int(value)
                    return value
            """,
        },
        "true_false_only": {
            "mod.py": """
                from coerce import coerce


                def load(defaults, file_values, env):
                    out = {}
                    for key, default in defaults.items():
                        if key.upper() in env:
                            out[key] = coerce(env[key.upper()], default)
                        elif key in file_values:
                            out[key] = file_values[key]
                        else:
                            out[key] = default
                    return out
            """,
            "coerce.py": """
                def coerce(value, like):
                    if isinstance(like, bool):
                        if value.lower() == 'true':
                            return True
                        if value.lower() == 'false':
                            return False
                        raise ValueError(value)
                    if isinstance(like, int):
                        return int(value)
                    return value
            """,
        },
    },
)

# --------------------------------------------------------------------------- 8
rung(
    "toposort", 8, "Topological order", "graph algorithm, error type, determinism",
    """
    order(deps) takes a dict mapping each node (a string) to the list of nodes it
    depends on. It returns a list containing every node mentioned anywhere, in which
    each node comes after all of its dependencies. When several nodes are ready at the
    same time the smallest string goes first, and readiness is re-evaluated after every
    pick. A dependency cycle, including a node that depends on itself, raises
    CycleError, which mod.py defines.
    """,
    [
        {"call": "order({'b': ['a'], 'c': ['b']})", "expect": "['a', 'b', 'c']"},
        {"call": "order({'c': ['a'], 'b': ['a']})", "expect": "['a', 'b', 'c']"},
        {"call": "order({'x': ['y']})", "expect": "['y', 'x']"},
        {"call": "order({'b': ['a'], 'c': [], 'a': []})", "expect": "['a', 'b', 'c']"},
        {"call": "order({'a': ['b'], 'b': ['a']})", "raises": "CycleError"},
    ],
    {"mod.py": """
        class CycleError(Exception):
            pass


        def order(deps):
            seen, out = set(), []

            def visit(node):
                if node in seen:
                    return
                seen.add(node)
                for dep in deps.get(node, []):
                    visit(dep)
                out.append(node)

            for node in deps:
                visit(node)
            return out
    """},
    {"mod.py": """
        import heapq


        class CycleError(Exception):
            pass


        def order(deps):
            nodes = set(deps)
            for ds in deps.values():
                nodes.update(ds)
            remaining = {n: set(deps.get(n, [])) for n in nodes}
            dependents = {n: set() for n in nodes}
            for n, ds in remaining.items():
                for d in ds:
                    dependents[d].add(n)
            ready = [n for n in nodes if not remaining[n]]
            heapq.heapify(ready)
            out = []
            while ready:
                n = heapq.heappop(ready)
                out.append(n)
                for m in dependents[n]:
                    remaining[m].discard(n)
                    if not remaining[m]:
                        heapq.heappush(ready, m)
            if len(out) != len(nodes):
                raise CycleError('dependency cycle')
            return out
    """},
    tests("""
    from mod import order
    class T(unittest.TestCase):
        def test_chain(self):
            self.assertEqual(order({'b': ['a'], 'c': ['b']}), ['a', 'b', 'c'])
        def test_single(self):
            self.assertEqual(order({'a': []}), ['a'])
    """),
    tests("""
    from mod import order, CycleError
    class T(unittest.TestCase):
        def test_smallest_first(self):
            self.assertEqual(order({'c': ['a'], 'b': ['a']}), ['a', 'b', 'c'])
            self.assertEqual(order({'z': [], 'y': [], 'x': ['z']}), ['y', 'z', 'x'])
        def test_re_evaluated_after_each_pick(self):
            self.assertEqual(order({'b': ['a'], 'c': [], 'a': []}), ['a', 'b', 'c'])
            self.assertEqual(order({'d': ['c'], 'c': ['a'], 'b': [], 'a': []}), ['a', 'b', 'c', 'd'])
        def test_implicit_nodes(self):
            self.assertEqual(order({'x': ['y']}), ['y', 'x'])
            self.assertEqual(order({'x': ['y', 'z']}), ['y', 'z', 'x'])
        def test_cycle(self):
            with self.assertRaises(CycleError):
                order({'a': ['b'], 'b': ['a']})
            with self.assertRaises(CycleError):
                order({'a': ['a']})
            with self.assertRaises(CycleError):
                order({'a': ['b'], 'b': ['c'], 'c': ['a'], 'd': []})
        def test_empty(self):
            self.assertEqual(order({}), [])
    """),
    {
        "fifo": {"mod.py": """
            from collections import deque


            class CycleError(Exception):
                pass


            def order(deps):
                nodes = set(deps)
                for ds in deps.values():
                    nodes.update(ds)
                remaining = {n: set(deps.get(n, [])) for n in nodes}
                dependents = {n: set() for n in nodes}
                for n, ds in remaining.items():
                    for d in ds:
                        dependents[d].add(n)
                queue = deque(sorted(n for n in nodes if not remaining[n]))
                out = []
                while queue:
                    n = queue.popleft()
                    out.append(n)
                    for m in sorted(dependents[n]):
                        remaining[m].discard(n)
                        if not remaining[m]:
                            queue.append(m)
                if len(out) != len(nodes):
                    raise CycleError('dependency cycle')
                return out
        """},
        "dfs_gray": {"mod.py": """
            class CycleError(Exception):
                pass


            def order(deps):
                nodes = set(deps)
                for ds in deps.values():
                    nodes.update(ds)
                done, active, out = set(), set(), []

                def visit(node):
                    if node in done:
                        return
                    if node in active:
                        raise CycleError('dependency cycle')
                    active.add(node)
                    for dep in sorted(deps.get(node, [])):
                        visit(dep)
                    active.discard(node)
                    done.add(node)
                    out.append(node)

                for node in sorted(nodes):
                    visit(node)
                return out
        """},
    },
)

# --------------------------------------------------------------------------- 9
rung(
    "shlex", 9, "Command line words", "tokenizer state machine",
    """
    split(line) splits a command line into a list of words. Whitespace outside quotes
    separates words. Inside single quotes every character is literal until the closing
    single quote. Inside double quotes a backslash followed by a double quote or by
    another backslash yields that one character, and any other backslash is kept as it
    is. Outside quotes a backslash makes the next character literal. Quotes do not
    create word boundaries, so a'b c' is the one word ab c. A quoted empty string is an
    empty word. A backslash at the very end of the line is kept as a character. An
    unterminated quote raises ValueError.
    """,
    [
        {"call": "split('a  b')", "expect": "['a', 'b']"},
        {"call": r"""split("'a b' c")""", "expect": "['a b', 'c']"},
        {"call": r"""split(r'"say \"hi\""')""", "expect": r"""['say "hi"']"""},
        {"call": r"""split(r'a\ b')""", "expect": "['a b']"},
        {"call": r"""split("''")""", "expect": "['']"},
        {"call": r"""split("a'b c'")""", "expect": "['ab c']"},
        {"call": r"""split(r"'a\b'")""", "expect": r"""[r'a\b']"""},
        {"call": r"""split(r'"a\n"')""", "expect": r"""[r'a\n']"""},
        {"call": r"""split('a\\')""", "expect": r"""['a\\']"""},
        {"call": r"""split('"x')""", "raises": "ValueError"},
    ],
    {"mod.py": """
        def split(line):
            out, cur, quoted = [], '', False
            for ch in line:
                if ch == '"':
                    quoted = not quoted
                elif ch.isspace() and not quoted:
                    if cur:
                        out.append(cur)
                        cur = ''
                else:
                    cur += ch
            if cur:
                out.append(cur)
            return out
    """},
    {"mod.py": r'''
        def split(line):
            out, cur, have = [], [], False
            i, n = 0, len(line)
            while i < n:
                ch = line[i]
                if ch == "'":
                    have = True
                    j = line.find("'", i + 1)
                    if j < 0:
                        raise ValueError('unterminated single quote')
                    cur.append(line[i + 1:j])
                    i = j + 1
                elif ch == '"':
                    have = True
                    i += 1
                    closed = False
                    while i < n:
                        c = line[i]
                        if c == '\\' and i + 1 < n and line[i + 1] in '"\\':
                            cur.append(line[i + 1])
                            i += 2
                        elif c == '"':
                            closed = True
                            i += 1
                            break
                        else:
                            cur.append(c)
                            i += 1
                    if not closed:
                        raise ValueError('unterminated double quote')
                elif ch == '\\':
                    have = True
                    if i + 1 < n:
                        cur.append(line[i + 1])
                        i += 2
                    else:
                        cur.append('\\')
                        i += 1
                elif ch.isspace():
                    if have:
                        out.append(''.join(cur))
                        cur, have = [], False
                    i += 1
                else:
                    have = True
                    cur.append(ch)
                    i += 1
            if have:
                out.append(''.join(cur))
            return out
    '''},
    tests(r'''
    from mod import split
    class T(unittest.TestCase):
        def test_plain(self):
            self.assertEqual(split('a  b'), ['a', 'b'])
            self.assertEqual(split('"a b" c'), ['a b', 'c'])
    '''),
    tests(r'''
    from mod import split
    class T(unittest.TestCase):
        def test_single_quotes(self):
            self.assertEqual(split("'a b' c"), ['a b', 'c'])
            self.assertEqual(split("'a\\b'"), ['a\\b'])
            self.assertEqual(split("'a\\\\b'"), ['a\\\\b'])
            self.assertEqual(split("'a\\'"), ['a\\'])
        def test_double_quote_escapes(self):
            self.assertEqual(split('"say \\"hi\\""'), ['say "hi"'])
            self.assertEqual(split('"a\\\\b"'), ['a\\b'])
            self.assertEqual(split('"a\\n"'), ['a\\n'])
        def test_backslash_outside(self):
            self.assertEqual(split('a\\ b'), ['a b'])
            self.assertEqual(split('a\\"b'), ['a"b'])
            self.assertEqual(split('a\\'), ['a\\'])
        def test_empty_words(self):
            self.assertEqual(split("''"), [''])
            self.assertEqual(split('""'), [''])
            self.assertEqual(split("a '' b"), ['a', '', 'b'])
        def test_adjacent(self):
            self.assertEqual(split("a'b c'"), ['ab c'])
            self.assertEqual(split('"a"\'b\''), ['ab'])
        def test_unterminated(self):
            with self.assertRaises(ValueError):
                split('"x')
            with self.assertRaises(ValueError):
                split("'x")
    '''),
    {
        "drop_empty": {"mod.py": r'''
            def split(line):
                out, cur = [], []
                i, n = 0, len(line)
                while i < n:
                    ch = line[i]
                    if ch == "'":
                        j = line.find("'", i + 1)
                        if j < 0:
                            raise ValueError('unterminated single quote')
                        cur.append(line[i + 1:j])
                        i = j + 1
                    elif ch == '"':
                        i += 1
                        closed = False
                        while i < n:
                            c = line[i]
                            if c == '\\' and i + 1 < n and line[i + 1] in '"\\':
                                cur.append(line[i + 1])
                                i += 2
                            elif c == '"':
                                closed = True
                                i += 1
                                break
                            else:
                                cur.append(c)
                                i += 1
                        if not closed:
                            raise ValueError('unterminated double quote')
                    elif ch == '\\':
                        if i + 1 < n:
                            cur.append(line[i + 1])
                            i += 2
                        else:
                            i += 1
                    elif ch.isspace():
                        if cur:
                            out.append(''.join(cur))
                            cur = []
                        i += 1
                    else:
                        cur.append(ch)
                        i += 1
                if cur:
                    out.append(''.join(cur))
                return out
        '''},
        "stdlib": {"mod.py": """
            import shlex


            def split(line):
                return shlex.split(line)
        """},
        "single_escapes": {"mod.py": r'''
            def split(line):
                out, cur, have = [], [], False
                quote = None
                i, n = 0, len(line)
                while i < n:
                    ch = line[i]
                    if quote:
                        if ch == quote:
                            quote = None
                        elif ch == '\\' and i + 1 < n and line[i + 1] in (quote, '\\'):
                            cur.append(line[i + 1])
                            i += 1
                        else:
                            cur.append(ch)
                    elif ch in ('"', "'"):
                        quote = ch
                        have = True
                    elif ch == '\\' and i + 1 < n:
                        cur.append(line[i + 1])
                        have = True
                        i += 1
                    elif ch.isspace():
                        if have:
                            out.append(''.join(cur))
                            cur, have = [], False
                    else:
                        cur.append(ch)
                        have = True
                    i += 1
                if quote:
                    raise ValueError('unterminated quote')
                if have:
                    out.append(''.join(cur))
                return out
        '''},
    },
)

# -------------------------------------------------------------------------- 10
rung(
    "jsonptr", 10, "JSON Pointer", "standard compliance",
    """
    resolve(doc, pointer) returns the value that a JSON Pointer (RFC 6901) names inside
    doc, a structure of dicts, lists, and scalars. The empty pointer names doc itself.
    Otherwise the pointer starts with '/' and each '/'-separated token selects a dict
    key, or a list index written as decimal digits. Inside a token '~1' stands for '/'
    and '~0' stands for '~', decoded in that order, so '~01' means the two characters
    '~1'. A missing key, an index that is not all digits, an index past the end, or a
    step into a scalar raises KeyError. set_at(doc, pointer, value) changes doc in
    place and returns None: it resolves all but the last token the same way, then on a
    dict sets the key, and on a list replaces the index, or appends when the last token
    is '-'. Any other failure raises KeyError.
    """,
    [
        {"call": "resolve({'a': {'b': [10, 20]}}, '/a/b/1')", "expect": "20"},
        {"call": "resolve({'a/b': 1}, '/a~1b')", "expect": "1"},
        {"call": "resolve({'~1': 5}, '/~01')", "expect": "5"},
        {"call": "resolve({'': 3}, '/')", "expect": "3"},
        {"call": "resolve([1, 2], '')", "expect": "[1, 2]"},
        {"call": "resolve({'a': [1]}, '/a/1')", "raises": "KeyError"},
        {"setup": "d = {'a': [1]}; set_at(d, '/a/-', 2)", "call": "d", "expect": "{'a': [1, 2]}"},
        {"setup": "d = {'a': [1]}; set_at(d, '/a/0', 9)", "call": "d", "expect": "{'a': [9]}"},
    ],
    {"mod.py": """
        def _tokens(pointer):
            if not pointer:
                raise KeyError(pointer)
            return [t.replace('~0', '~').replace('~1', '/') for t in pointer[1:].split('/')]


        def _step(node, token):
            if isinstance(node, list):
                return node[int(token)]
            return node[token]


        def resolve(doc, pointer):
            node = doc
            for token in _tokens(pointer):
                node = _step(node, token)
            return node


        def set_at(doc, pointer, value):
            tokens = _tokens(pointer)
            node = doc
            for token in tokens[:-1]:
                node = _step(node, token)
            last = tokens[-1]
            if isinstance(node, list):
                node[int(last)] = value
            else:
                node[last] = value
    """},
    {"mod.py": """
        def _tokens(pointer):
            if pointer == '':
                return []
            if not pointer.startswith('/'):
                raise KeyError(pointer)
            return [t.replace('~1', '/').replace('~0', '~') for t in pointer[1:].split('/')]


        def _index(node, token):
            if not (token.isascii() and token.isdigit()) or int(token) >= len(node):
                raise KeyError(token)
            return int(token)


        def _step(node, token):
            if isinstance(node, list):
                return node[_index(node, token)]
            if isinstance(node, dict):
                if token not in node:
                    raise KeyError(token)
                return node[token]
            raise KeyError(token)


        def resolve(doc, pointer):
            node = doc
            for token in _tokens(pointer):
                node = _step(node, token)
            return node


        def set_at(doc, pointer, value):
            tokens = _tokens(pointer)
            if not tokens:
                raise KeyError(pointer)
            node = doc
            for token in tokens[:-1]:
                node = _step(node, token)
            last = tokens[-1]
            if isinstance(node, list):
                if last == '-':
                    node.append(value)
                else:
                    node[_index(node, last)] = value
            elif isinstance(node, dict):
                node[last] = value
            else:
                raise KeyError(last)
    """},
    tests("""
    from mod import resolve, set_at
    class T(unittest.TestCase):
        def test_basic(self):
            self.assertEqual(resolve({'a': {'b': [10, 20]}}, '/a/b/1'), 20)
            self.assertEqual(resolve({'a/b': 1}, '/a~1b'), 1)
            d = {'a': [1]}
            set_at(d, '/a/0', 9)
            self.assertEqual(d, {'a': [9]})
    """),
    tests("""
    from mod import resolve, set_at
    class T(unittest.TestCase):
        def test_decode_order(self):
            self.assertEqual(resolve({'~1': 5}, '/~01'), 5)
            self.assertEqual(resolve({'~': 1}, '/~0'), 1)
            self.assertEqual(resolve({'/': 2}, '/~1'), 2)
        def test_root_and_empty_key(self):
            self.assertEqual(resolve([1, 2], ''), [1, 2])
            self.assertEqual(resolve({'': 3}, '/'), 3)
            self.assertEqual(resolve({'a': {'': 4}}, '/a/'), 4)
        def test_errors_are_keyerror(self):
            with self.assertRaises(KeyError):
                resolve({'a': 1}, '/b')
            with self.assertRaises(KeyError):
                resolve({'a': [1]}, '/a/x')
            with self.assertRaises(KeyError):
                resolve({'a': [1]}, '/a/1')
            with self.assertRaises(KeyError):
                resolve({'a': [1, 2]}, '/a/-1')
            with self.assertRaises(KeyError):
                resolve({'a': 5}, '/a/b')
        def test_append(self):
            d = {'a': [1]}
            set_at(d, '/a/-', 2)
            self.assertEqual(d, {'a': [1, 2]})
            self.assertIsNone(set_at(d, '/a/-', 3))
            self.assertEqual(d['a'], [1, 2, 3])
        def test_set_dict_and_list(self):
            d = {'a': {}}
            set_at(d, '/a/b', 1)
            self.assertEqual(d, {'a': {'b': 1}})
            set_at(d, '/a/b', 2)
            self.assertEqual(d, {'a': {'b': 2}})
            d2 = {'a': [1, 2]}
            set_at(d2, '/a/1', 9)
            self.assertEqual(d2, {'a': [1, 9]})
            with self.assertRaises(KeyError):
                set_at(d2, '/a/5', 1)
            with self.assertRaises(KeyError):
                set_at(d2, '/zz/5', 1)
    """),
    {
        "no_dash": {"mod.py": """
            def _tokens(pointer):
                if pointer == '':
                    return []
                return [t.replace('~1', '/').replace('~0', '~') for t in pointer[1:].split('/')]


            def _index(node, token):
                if not token.isdigit() or int(token) >= len(node):
                    raise KeyError(token)
                return int(token)


            def _step(node, token):
                if isinstance(node, list):
                    return node[_index(node, token)]
                if isinstance(node, dict):
                    if token not in node:
                        raise KeyError(token)
                    return node[token]
                raise KeyError(token)


            def resolve(doc, pointer):
                node = doc
                for token in _tokens(pointer):
                    node = _step(node, token)
                return node


            def set_at(doc, pointer, value):
                tokens = _tokens(pointer)
                node = doc
                for token in tokens[:-1]:
                    node = _step(node, token)
                last = tokens[-1]
                if isinstance(node, list):
                    node[_index(node, last)] = value
                elif isinstance(node, dict):
                    node[last] = value
                else:
                    raise KeyError(last)
        """},
        "root_raises": {"mod.py": """
            def _tokens(pointer):
                if not pointer:
                    raise KeyError(pointer)
                return [t.replace('~1', '/').replace('~0', '~') for t in pointer[1:].split('/')]


            def _index(node, token):
                if not token.isdigit() or int(token) >= len(node):
                    raise KeyError(token)
                return int(token)


            def _step(node, token):
                if isinstance(node, list):
                    return node[_index(node, token)]
                if isinstance(node, dict):
                    if token not in node:
                        raise KeyError(token)
                    return node[token]
                raise KeyError(token)


            def resolve(doc, pointer):
                node = doc
                for token in _tokens(pointer):
                    node = _step(node, token)
                return node


            def set_at(doc, pointer, value):
                tokens = _tokens(pointer)
                node = doc
                for token in tokens[:-1]:
                    node = _step(node, token)
                last = tokens[-1]
                if isinstance(node, list):
                    if last == '-':
                        node.append(value)
                    else:
                        node[_index(node, last)] = value
                elif isinstance(node, dict):
                    node[last] = value
                else:
                    raise KeyError(last)
        """},
    },
    max_turns=12,
)

# -------------------------------------------------------------------------- 11
rung(
    "cron", 11, "Cron matcher", "two files, dense spec, two bugs",
    """
    matches(expr, when) returns True when the datetime when matches the five-field cron
    expression expr: minute (0-59), hour (0-23), day of month (1-31), month (1-12), and
    day of week (0-7, where both 0 and 7 are Sunday and 1 is Monday), separated by
    whitespace. A field is '*', a number, an inclusive range a-b, a step '*/n' or
    'a-b/n' meaning every nth value counting from the start of that range, or a comma
    list of those. Seconds are ignored. When both the day-of-month and the day-of-week
    fields are restricted (neither is '*'), the date matches when either of them
    matches; when only one is restricted, only it applies. Parsing lives in fields.py:
    parse_field(text, lo, hi) returns the set of integers in lo..hi that the field
    text selects. The bug is not necessarily in mod.py.
    """,
    [
        {"call": "matches('*/15 * * * *', datetime(2026, 1, 1, 10, 30))", "expect": "True"},
        {"call": "matches('0 9 * * 1-5', datetime(2026, 3, 7, 9, 0))", "expect": "False"},
        {"call": "matches('1-10/3 * * * *', datetime(2026, 1, 1, 0, 4))", "expect": "True"},
        {"call": "matches('1-10/3 * * * *', datetime(2026, 1, 1, 0, 3))", "expect": "False"},
        {"call": "matches('* * * * 7', datetime(2026, 3, 1, 0, 0))", "expect": "True"},
        {"call": "matches('0 0 1 * 1', datetime(2026, 6, 8, 0, 0))", "expect": "True"},
        {"call": "matches('0 0 1 * 1', datetime(2026, 5, 1, 0, 0))", "expect": "True"},
        {"call": "matches('0 0 1 * 1', datetime(2026, 6, 10, 0, 0))", "expect": "False"},
        {"call": "matches('0 0 * * 1', datetime(2026, 5, 1, 0, 0))", "expect": "False"},
        {"call": "parse_field('1-10/3', 0, 59)", "expect": "{1, 4, 7, 10}"},
    ],
    {
        "mod.py": """
            from fields import parse_field


            def matches(expr, when):
                f = expr.split()
                minute = parse_field(f[0], 0, 59)
                hour = parse_field(f[1], 0, 23)
                dom = parse_field(f[2], 1, 31)
                month = parse_field(f[3], 1, 12)
                dow = parse_field(f[4], 0, 7)
                weekday = (when.weekday() + 1) % 7
                return (when.minute in minute and when.hour in hour and when.month in month
                        and when.day in dom and weekday in dow)
        """,
        "fields.py": """
            def parse_field(text, lo, hi):
                out = set()
                for part in text.split(','):
                    step = 1
                    if '/' in part:
                        part, step = part.split('/')
                        step = int(step)
                    if part == '*':
                        a, b = lo, hi
                    elif '-' in part:
                        a, b = (int(x) for x in part.split('-'))
                    else:
                        a = b = int(part)
                    for v in range(a, b + 1):
                        if v % step == 0:
                            out.add(v)
                return out
        """,
    },
    {
        "mod.py": """
            from fields import parse_field


            def matches(expr, when):
                f = expr.split()
                minute = parse_field(f[0], 0, 59)
                hour = parse_field(f[1], 0, 23)
                dom = parse_field(f[2], 1, 31)
                month = parse_field(f[3], 1, 12)
                dow = {0 if v == 7 else v for v in parse_field(f[4], 0, 7)}
                weekday = (when.weekday() + 1) % 7
                if not (when.minute in minute and when.hour in hour and when.month in month):
                    return False
                dom_free = f[2] == '*'
                dow_free = f[4] == '*'
                if dom_free and dow_free:
                    return True
                if dom_free:
                    return weekday in dow
                if dow_free:
                    return when.day in dom
                return when.day in dom or weekday in dow
        """,
        "fields.py": """
            def parse_field(text, lo, hi):
                out = set()
                for part in text.split(','):
                    step = 1
                    if '/' in part:
                        part, step = part.split('/')
                        step = int(step)
                    if part == '*':
                        a, b = lo, hi
                    elif '-' in part:
                        a, b = (int(x) for x in part.split('-'))
                    else:
                        a = b = int(part)
                    for v in range(a, b + 1):
                        if (v - a) % step == 0:
                            out.add(v)
                return out
        """,
    },
    tests("""
    from datetime import datetime
    from mod import matches
    class T(unittest.TestCase):
        def test_step_star(self):
            self.assertTrue(matches('*/15 * * * *', datetime(2026, 1, 1, 10, 30)))
            self.assertFalse(matches('*/15 * * * *', datetime(2026, 1, 1, 10, 31)))
        def test_weekdays(self):
            self.assertTrue(matches('0 9 * * 1-5', datetime(2026, 6, 1, 9, 0)))
            self.assertFalse(matches('0 9 * * 1-5', datetime(2026, 3, 7, 9, 0)))
    """),
    tests("""
    from datetime import datetime
    from mod import matches
    from fields import parse_field
    class T(unittest.TestCase):
        def test_range_step_counts_from_range_start(self):
            self.assertTrue(matches('1-10/3 * * * *', datetime(2026, 1, 1, 0, 4)))
            self.assertFalse(matches('1-10/3 * * * *', datetime(2026, 1, 1, 0, 3)))
            self.assertEqual(parse_field('1-10/3', 0, 59), {1, 4, 7, 10})
            self.assertEqual(parse_field('*/20', 0, 59), {0, 20, 40})
            self.assertEqual(parse_field('*/10', 1, 31), {1, 11, 21, 31})
            self.assertTrue(matches('0 0 */10 * *', datetime(2026, 1, 11, 0, 0)))
            self.assertFalse(matches('0 0 */10 * *', datetime(2026, 1, 10, 0, 0)))
            self.assertEqual(parse_field('5-7,20', 0, 59), {5, 6, 7, 20})
        def test_sunday_is_0_and_7(self):
            self.assertTrue(matches('* * * * 7', datetime(2026, 3, 1, 0, 0)))
            self.assertTrue(matches('* * * * 0', datetime(2026, 3, 1, 0, 0)))
            self.assertFalse(matches('* * * * 7', datetime(2026, 3, 2, 0, 0)))
        def test_dom_or_dow_when_both_restricted(self):
            self.assertTrue(matches('0 0 1 * 1', datetime(2026, 6, 8, 0, 0)))
            self.assertTrue(matches('0 0 1 * 1', datetime(2026, 5, 1, 0, 0)))
            self.assertFalse(matches('0 0 1 * 1', datetime(2026, 6, 10, 0, 0)))
        def test_only_one_restricted(self):
            self.assertFalse(matches('0 0 * * 1', datetime(2026, 5, 1, 0, 0)))
            self.assertTrue(matches('0 0 * * 1', datetime(2026, 6, 8, 0, 0)))
            self.assertFalse(matches('0 0 1 * *', datetime(2026, 6, 8, 0, 0)))
            self.assertTrue(matches('0 0 1 * *', datetime(2026, 5, 1, 0, 0)))
        def test_other_fields(self):
            self.assertTrue(matches('0 */6 * * *', datetime(2026, 1, 1, 12, 0)))
            self.assertFalse(matches('0 */6 * * *', datetime(2026, 1, 1, 13, 0)))
            self.assertTrue(matches('30 8 * 1,6 *', datetime(2026, 6, 15, 8, 30)))
            self.assertFalse(matches('30 8 * 1,6 *', datetime(2026, 2, 15, 8, 30)))
            self.assertTrue(matches('0 9-11,14-16 * * *', datetime(2026, 1, 1, 15, 0)))
            self.assertFalse(matches('0 9-11,14-16 * * *', datetime(2026, 1, 1, 12, 0)))
    """),
    {
        "no_seven": {
            "mod.py": """
                from fields import parse_field


                def matches(expr, when):
                    f = expr.split()
                    minute = parse_field(f[0], 0, 59)
                    hour = parse_field(f[1], 0, 23)
                    dom = parse_field(f[2], 1, 31)
                    month = parse_field(f[3], 1, 12)
                    dow = parse_field(f[4], 0, 6)
                    weekday = (when.weekday() + 1) % 7
                    if not (when.minute in minute and when.hour in hour and when.month in month):
                        return False
                    if f[2] == '*' and f[4] == '*':
                        return True
                    if f[2] == '*':
                        return weekday in dow
                    if f[4] == '*':
                        return when.day in dom
                    return when.day in dom or weekday in dow
            """,
            "fields.py": """
                def parse_field(text, lo, hi):
                    out = set()
                    for part in text.split(','):
                        step = 1
                        if '/' in part:
                            part, step = part.split('/')
                            step = int(step)
                        if part == '*':
                            a, b = lo, hi
                        elif '-' in part:
                            a, b = (int(x) for x in part.split('-'))
                        else:
                            a = b = int(part)
                        for v in range(a, b + 1):
                            if (v - a) % step == 0:
                                out.add(v)
                    return out
            """,
        },
        "and_rule": {
            "mod.py": """
                from fields import parse_field


                def matches(expr, when):
                    f = expr.split()
                    minute = parse_field(f[0], 0, 59)
                    hour = parse_field(f[1], 0, 23)
                    dom = parse_field(f[2], 1, 31)
                    month = parse_field(f[3], 1, 12)
                    dow = {0 if v == 7 else v for v in parse_field(f[4], 0, 7)}
                    weekday = (when.weekday() + 1) % 7
                    return (when.minute in minute and when.hour in hour and when.month in month
                            and when.day in dom and weekday in dow)
            """,
            "fields.py": """
                def parse_field(text, lo, hi):
                    out = set()
                    for part in text.split(','):
                        step = 1
                        if '/' in part:
                            part, step = part.split('/')
                            step = int(step)
                        if part == '*':
                            a, b = lo, hi
                        elif '-' in part:
                            a, b = (int(x) for x in part.split('-'))
                        else:
                            a = b = int(part)
                        for v in range(a, b + 1):
                            if (v - a) % step == 0:
                                out.add(v)
                    return out
            """,
        },
        "or_always": {
            "mod.py": """
                from fields import parse_field


                def matches(expr, when):
                    f = expr.split()
                    minute = parse_field(f[0], 0, 59)
                    hour = parse_field(f[1], 0, 23)
                    dom = parse_field(f[2], 1, 31)
                    month = parse_field(f[3], 1, 12)
                    dow = {0 if v == 7 else v for v in parse_field(f[4], 0, 7)}
                    weekday = (when.weekday() + 1) % 7
                    return (when.minute in minute and when.hour in hour and when.month in month
                            and (when.day in dom or weekday in dow))
            """,
            "fields.py": """
                def parse_field(text, lo, hi):
                    out = set()
                    for part in text.split(','):
                        step = 1
                        if '/' in part:
                            part, step = part.split('/')
                            step = int(step)
                        if part == '*':
                            a, b = lo, hi
                        elif '-' in part:
                            a, b = (int(x) for x in part.split('-'))
                        else:
                            a = b = int(part)
                        for v in range(a, b + 1):
                            if (v - a) % step == 0:
                                out.add(v)
                    return out
            """,
        },
    },
    max_turns=12, prelude="from datetime import datetime",
)

# -------------------------------------------------------------------------- 12
rung(
    "expr", 12, "Expression evaluator", "recursive descent, precedence rules",
    """
    evaluate(text) computes an arithmetic expression and returns its value. Numbers
    follow Python: an integer literal is an int, a literal with a decimal point is a
    float, / is true division and always gives a float, and ** of two ints with a
    negative exponent gives a float. Operators are binary + - * / and **, unary minus,
    and parentheses. Precedence from lowest to highest is + and -, then * and /, then
    unary minus, then **, so -2**2 is -4 while 2*-3 is -6. ** groups to the right, so
    2**3**2 is 512, and the exponent may itself carry a unary minus. Whitespace between
    tokens is ignored. Division by zero, an empty expression, unbalanced parentheses,
    a missing operand, or any other character raises ValueError.
    """,
    [
        {"call": "evaluate('1 + 2 * 3')", "expect": "7"},
        {"call": "evaluate('-2**2')", "expect": "-4"},
        {"call": "evaluate('2**3**2')", "expect": "512"},
        {"call": "evaluate('(1+2)*(3+4)')", "expect": "21"},
        {"call": "evaluate('10/4')", "expect": "2.5"},
        {"call": "evaluate('3 - -2')", "expect": "5"},
        {"call": "evaluate('2**-1')", "expect": "0.5"},
        {"call": "evaluate('1/0')", "raises": "ValueError"},
        {"call": "evaluate('2 +')", "raises": "ValueError"},
        {"call": "evaluate('7 % 3')", "raises": "ValueError"},
    ],
    {"mod.py": """
        def _tokens(text):
            out, i, n = [], 0, len(text)
            while i < n:
                ch = text[i]
                if ch.isspace():
                    i += 1
                elif ch.isdigit() or ch == '.':
                    j = i
                    while j < n and (text[j].isdigit() or text[j] == '.'):
                        j += 1
                    num = text[i:j]
                    out.append(float(num) if '.' in num else int(num))
                    i = j
                elif text.startswith('**', i):
                    out.append('**')
                    i += 2
                elif ch in '+-*/()':
                    out.append(ch)
                    i += 1
                else:
                    raise ValueError(f'bad character {ch!r}')
            return out


        class _Parser:
            def __init__(self, tokens):
                self.tokens = tokens
                self.i = 0

            def peek(self):
                return self.tokens[self.i] if self.i < len(self.tokens) else None

            def take(self):
                tok = self.peek()
                self.i += 1
                return tok

            def expr(self):
                value = self.term()
                while self.peek() in ('+', '-'):
                    op = self.take()
                    right = self.term()
                    value = value + right if op == '+' else value - right
                return value

            def term(self):
                value = self.power()
                while self.peek() in ('*', '/'):
                    op = self.take()
                    right = self.power()
                    value = value * right if op == '*' else value / right
                return value

            def power(self):
                value = self.atom()
                while self.peek() == '**':
                    self.take()
                    value = value ** self.atom()
                return value

            def atom(self):
                tok = self.take()
                if tok == '-':
                    return -self.atom()
                if tok == '(':
                    value = self.expr()
                    if self.take() != ')':
                        raise ValueError('expected )')
                    return value
                if isinstance(tok, (int, float)):
                    return tok
                raise ValueError('expected a number')


        def evaluate(text):
            return _Parser(_tokens(text)).expr()
    """},
    {"mod.py": """
        def _tokens(text):
            out, i, n = [], 0, len(text)
            while i < n:
                ch = text[i]
                if ch.isspace():
                    i += 1
                elif ch.isdigit() or ch == '.':
                    j = i
                    while j < n and (text[j].isdigit() or text[j] == '.'):
                        j += 1
                    num = text[i:j]
                    try:
                        out.append(float(num) if '.' in num else int(num))
                    except ValueError:
                        raise ValueError(f'bad number {num!r}')
                    i = j
                elif text.startswith('**', i):
                    out.append('**')
                    i += 2
                elif ch in '+-*/()':
                    out.append(ch)
                    i += 1
                else:
                    raise ValueError(f'bad character {ch!r}')
            return out


        class _Parser:
            def __init__(self, tokens):
                self.tokens = tokens
                self.i = 0

            def peek(self):
                return self.tokens[self.i] if self.i < len(self.tokens) else None

            def take(self):
                tok = self.peek()
                self.i += 1
                return tok

            def expr(self):
                value = self.term()
                while self.peek() in ('+', '-'):
                    op = self.take()
                    right = self.term()
                    value = value + right if op == '+' else value - right
                return value

            def term(self):
                value = self.factor()
                while self.peek() in ('*', '/'):
                    op = self.take()
                    right = self.factor()
                    if op == '*':
                        value = value * right
                    else:
                        if right == 0:
                            raise ValueError('division by zero')
                        value = value / right
                return value

            def factor(self):
                if self.peek() == '-':
                    self.take()
                    return -self.factor()
                return self.power()

            def power(self):
                value = self.atom()
                if self.peek() == '**':
                    self.take()
                    exponent = self.factor()
                    try:
                        return value ** exponent
                    except ZeroDivisionError:
                        raise ValueError('division by zero')
                return value

            def atom(self):
                tok = self.take()
                if tok == '(':
                    value = self.expr()
                    if self.take() != ')':
                        raise ValueError('expected )')
                    return value
                if isinstance(tok, (int, float)) and not isinstance(tok, bool):
                    return tok
                raise ValueError('expected a number')


        def evaluate(text):
            parser = _Parser(_tokens(text))
            if not parser.tokens:
                raise ValueError('empty expression')
            value = parser.expr()
            if parser.peek() is not None:
                raise ValueError('unexpected token')
            return value
    """},
    tests("""
    from mod import evaluate
    class T(unittest.TestCase):
        def test_basic(self):
            self.assertEqual(evaluate('1 + 2 * 3'), 7)
            self.assertEqual(evaluate('(1+2)*(3+4)'), 21)
            self.assertEqual(evaluate('10/4'), 2.5)
    """),
    tests("""
    from mod import evaluate
    class T(unittest.TestCase):
        def test_unary_minus_below_power(self):
            self.assertEqual(evaluate('-2**2'), -4)
            self.assertEqual(evaluate('(-2)**2'), 4)
            self.assertEqual(evaluate('2**-1'), 0.5)
            self.assertEqual(evaluate('-(-3)'), 3)
        def test_power_groups_right(self):
            self.assertEqual(evaluate('2**3**2'), 512)
            self.assertEqual(evaluate('(2**3)**2'), 64)
        def test_errors(self):
            for bad in ('1/0', '2 +', '(1', '1)', '7 % 3', '', '   ', '2 3', '0**-1', '1..2'):
                with self.assertRaises(ValueError, msg=bad):
                    evaluate(bad)
        def test_types(self):
            self.assertIsInstance(evaluate('2*3'), int)
            self.assertEqual(evaluate('2*3'), 6)
            self.assertIsInstance(evaluate('2.0*3'), float)
            self.assertIsInstance(evaluate('6/3'), float)
            self.assertEqual(evaluate('6/3'), 2.0)
        def test_spacing_and_mixing(self):
            self.assertEqual(evaluate(' 3 - -2 '), 5)
            self.assertEqual(evaluate('2*-3'), -6)
            self.assertEqual(evaluate('1 - 2 - 3'), -4)
            self.assertEqual(evaluate('8 / 2 / 2'), 2.0)
            self.assertEqual(evaluate('2 + 3 * 4 ** 2 / 8'), 8.0)
    """),
    {
        "power_left": {"mod.py": """
            def _tokens(text):
                out, i, n = [], 0, len(text)
                while i < n:
                    ch = text[i]
                    if ch.isspace():
                        i += 1
                    elif ch.isdigit() or ch == '.':
                        j = i
                        while j < n and (text[j].isdigit() or text[j] == '.'):
                            j += 1
                        num = text[i:j]
                        try:
                            out.append(float(num) if '.' in num else int(num))
                        except ValueError:
                            raise ValueError(num)
                        i = j
                    elif text.startswith('**', i):
                        out.append('**')
                        i += 2
                    elif ch in '+-*/()':
                        out.append(ch)
                        i += 1
                    else:
                        raise ValueError(ch)
                return out


            class _Parser:
                def __init__(self, tokens):
                    self.tokens = tokens
                    self.i = 0

                def peek(self):
                    return self.tokens[self.i] if self.i < len(self.tokens) else None

                def take(self):
                    tok = self.peek()
                    self.i += 1
                    return tok

                def expr(self):
                    value = self.term()
                    while self.peek() in ('+', '-'):
                        op = self.take()
                        right = self.term()
                        value = value + right if op == '+' else value - right
                    return value

                def term(self):
                    value = self.factor()
                    while self.peek() in ('*', '/'):
                        op = self.take()
                        right = self.factor()
                        if op == '*':
                            value = value * right
                        else:
                            if right == 0:
                                raise ValueError('division by zero')
                            value = value / right
                    return value

                def factor(self):
                    if self.peek() == '-':
                        self.take()
                        return -self.factor()
                    return self.power()

                def power(self):
                    value = self.atom()
                    while self.peek() == '**':
                        self.take()
                        negate = False
                        if self.peek() == '-':
                            self.take()
                            negate = True
                        exponent = self.atom()
                        if negate:
                            exponent = -exponent
                        try:
                            value = value ** exponent
                        except ZeroDivisionError:
                            raise ValueError('division by zero')
                    return value

                def atom(self):
                    tok = self.take()
                    if tok == '(':
                        value = self.expr()
                        if self.take() != ')':
                            raise ValueError('expected )')
                        return value
                    if isinstance(tok, (int, float)):
                        return tok
                    raise ValueError('expected a number')


            def evaluate(text):
                parser = _Parser(_tokens(text))
                if not parser.tokens:
                    raise ValueError('empty')
                value = parser.expr()
                if parser.peek() is not None:
                    raise ValueError('trailing')
                return value
        """},
        "unary_tight": {"mod.py": """
            def _tokens(text):
                out, i, n = [], 0, len(text)
                while i < n:
                    ch = text[i]
                    if ch.isspace():
                        i += 1
                    elif ch.isdigit() or ch == '.':
                        j = i
                        while j < n and (text[j].isdigit() or text[j] == '.'):
                            j += 1
                        num = text[i:j]
                        try:
                            out.append(float(num) if '.' in num else int(num))
                        except ValueError:
                            raise ValueError(num)
                        i = j
                    elif text.startswith('**', i):
                        out.append('**')
                        i += 2
                    elif ch in '+-*/()':
                        out.append(ch)
                        i += 1
                    else:
                        raise ValueError(ch)
                return out


            class _Parser:
                def __init__(self, tokens):
                    self.tokens = tokens
                    self.i = 0

                def peek(self):
                    return self.tokens[self.i] if self.i < len(self.tokens) else None

                def take(self):
                    tok = self.peek()
                    self.i += 1
                    return tok

                def expr(self):
                    value = self.term()
                    while self.peek() in ('+', '-'):
                        op = self.take()
                        right = self.term()
                        value = value + right if op == '+' else value - right
                    return value

                def term(self):
                    value = self.power()
                    while self.peek() in ('*', '/'):
                        op = self.take()
                        right = self.power()
                        if op == '*':
                            value = value * right
                        else:
                            if right == 0:
                                raise ValueError('division by zero')
                            value = value / right
                    return value

                def power(self):
                    value = self.atom()
                    if self.peek() == '**':
                        self.take()
                        exponent = self.power()
                        try:
                            return value ** exponent
                        except ZeroDivisionError:
                            raise ValueError('division by zero')
                    return value

                def atom(self):
                    tok = self.take()
                    if tok == '-':
                        return -self.atom()
                    if tok == '(':
                        value = self.expr()
                        if self.take() != ')':
                            raise ValueError('expected )')
                        return value
                    if isinstance(tok, (int, float)):
                        return tok
                    raise ValueError('expected a number')


            def evaluate(text):
                parser = _Parser(_tokens(text))
                if not parser.tokens:
                    raise ValueError('empty')
                value = parser.expr()
                if parser.peek() is not None:
                    raise ValueError('trailing')
                return value
        """},
        "no_end_check": {"mod.py": """
            def _tokens(text):
                out, i, n = [], 0, len(text)
                while i < n:
                    ch = text[i]
                    if ch.isspace():
                        i += 1
                    elif ch.isdigit() or ch == '.':
                        j = i
                        while j < n and (text[j].isdigit() or text[j] == '.'):
                            j += 1
                        num = text[i:j]
                        try:
                            out.append(float(num) if '.' in num else int(num))
                        except ValueError:
                            raise ValueError(num)
                        i = j
                    elif text.startswith('**', i):
                        out.append('**')
                        i += 2
                    elif ch in '+-*/()':
                        out.append(ch)
                        i += 1
                    else:
                        raise ValueError(ch)
                return out


            class _Parser:
                def __init__(self, tokens):
                    self.tokens = tokens
                    self.i = 0

                def peek(self):
                    return self.tokens[self.i] if self.i < len(self.tokens) else None

                def take(self):
                    tok = self.peek()
                    self.i += 1
                    return tok

                def expr(self):
                    value = self.term()
                    while self.peek() in ('+', '-'):
                        op = self.take()
                        right = self.term()
                        value = value + right if op == '+' else value - right
                    return value

                def term(self):
                    value = self.factor()
                    while self.peek() in ('*', '/'):
                        op = self.take()
                        right = self.factor()
                        if op == '*':
                            value = value * right
                        else:
                            if right == 0:
                                raise ValueError('division by zero')
                            value = value / right
                    return value

                def factor(self):
                    if self.peek() == '-':
                        self.take()
                        return -self.factor()
                    return self.power()

                def power(self):
                    value = self.atom()
                    if self.peek() == '**':
                        self.take()
                        exponent = self.factor()
                        try:
                            return value ** exponent
                        except ZeroDivisionError:
                            raise ValueError('division by zero')
                    return value

                def atom(self):
                    tok = self.take()
                    if tok == '(':
                        value = self.expr()
                        if self.take() != ')':
                            raise ValueError('expected )')
                        return value
                    if isinstance(tok, (int, float)):
                        return tok
                    raise ValueError('expected a number')


            def evaluate(text):
                parser = _Parser(_tokens(text))
                if not parser.tokens:
                    raise ValueError('empty')
                return parser.expr()
        """},
    },
    max_turns=12,
)

# -------------------------------------------------------------------------- 13
rung(
    "undo", 13, "Grouped undo", "nested state, history semantics",
    """
    Doc() is a text document that starts empty. insert(pos, s) inserts s at index pos,
    where pos may equal the current length. delete(pos, n) removes the n characters
    starting at pos. text() returns the content. Positions outside the text raise
    IndexError and change nothing. undo() reverses the most recent step that is not
    already undone; redo() re-applies the most recently undone step. A step is one
    edit, or one group: the edits made between begin_group() and its matching
    end_group() form a single step, and groups may nest, in which case only the
    outermost pair forms a step. Calling undo() or redo() while a group is open raises
    RuntimeError. A new edit made after an undo discards the steps that could still
    have been redone. undo() with nothing to undo, and redo() with nothing to redo, do
    nothing.
    """,
    [
        {"setup": "d = Doc(); d.insert(0, 'ab'); d.insert(2, 'c'); d.undo()", "call": "d.text()", "expect": "'ab'"},
        {"setup": "d = Doc(); d.insert(0, 'ab'); d.insert(2, 'c'); d.undo(); d.redo()", "call": "d.text()", "expect": "'abc'"},
        {"setup": "d = Doc(); d.begin_group(); d.insert(0, 'x'); d.insert(1, 'y'); d.end_group(); d.undo()",
         "call": "d.text()", "expect": "''"},
        {"setup": "d = Doc(); d.insert(0, 'a'); d.undo(); d.insert(0, 'b'); d.redo()", "call": "d.text()", "expect": "'b'"},
        {"setup": "d = Doc(); d.insert(0, 'abcd'); d.delete(1, 2)", "call": "d.text()", "expect": "'ad'"},
        {"setup": "d = Doc(); d.begin_group(); d.insert(0, 'x')", "call": "d.undo()", "raises": "RuntimeError"},
    ],
    {"mod.py": """
        class Doc:
            def __init__(self):
                self._text = ''
                self._done = []
                self._undone = []
                self._depth = 0

            def text(self):
                return self._text

            def begin_group(self):
                self._depth += 1

            def end_group(self):
                self._depth -= 1

            def _apply(self, edit):
                kind, pos, s = edit
                if kind == 'insert':
                    self._text = self._text[:pos] + s + self._text[pos:]
                else:
                    self._text = self._text[:pos] + self._text[pos + len(s):]

            def _invert(self, edit):
                kind, pos, s = edit
                return ('delete' if kind == 'insert' else 'insert', pos, s)

            def insert(self, pos, s):
                if pos < 0 or pos > len(self._text):
                    raise IndexError(pos)
                edit = ('insert', pos, s)
                self._apply(edit)
                self._done.append(edit)

            def delete(self, pos, n):
                if pos < 0 or pos + n > len(self._text):
                    raise IndexError(pos)
                edit = ('delete', pos, self._text[pos:pos + n])
                self._apply(edit)
                self._done.append(edit)

            def undo(self):
                if not self._done:
                    return
                edit = self._done.pop()
                self._apply(self._invert(edit))
                self._undone.append(edit)

            def redo(self):
                if not self._undone:
                    return
                edit = self._undone.pop()
                self._apply(edit)
                self._done.append(edit)
    """},
    {"mod.py": """
        class Doc:
            def __init__(self):
                self._text = ''
                self._done = []
                self._undone = []
                self._depth = 0
                self._open = None

            def text(self):
                return self._text

            def begin_group(self):
                if self._depth == 0:
                    self._open = []
                self._depth += 1

            def end_group(self):
                if self._depth == 0:
                    raise RuntimeError('no open group')
                self._depth -= 1
                if self._depth == 0:
                    if self._open:
                        self._done.append(self._open)
                    self._open = None

            def _apply(self, edit):
                kind, pos, s = edit
                if kind == 'insert':
                    self._text = self._text[:pos] + s + self._text[pos:]
                else:
                    self._text = self._text[:pos] + self._text[pos + len(s):]

            def _invert(self, edit):
                kind, pos, s = edit
                return ('delete' if kind == 'insert' else 'insert', pos, s)

            def _record(self, edit):
                self._apply(edit)
                self._undone.clear()
                if self._depth:
                    self._open.append(edit)
                else:
                    self._done.append([edit])

            def insert(self, pos, s):
                if pos < 0 or pos > len(self._text):
                    raise IndexError(pos)
                self._record(('insert', pos, s))

            def delete(self, pos, n):
                if pos < 0 or n < 0 or pos + n > len(self._text):
                    raise IndexError(pos)
                self._record(('delete', pos, self._text[pos:pos + n]))

            def undo(self):
                if self._depth:
                    raise RuntimeError('group is open')
                if not self._done:
                    return
                step = self._done.pop()
                for edit in reversed(step):
                    self._apply(self._invert(edit))
                self._undone.append(step)

            def redo(self):
                if self._depth:
                    raise RuntimeError('group is open')
                if not self._undone:
                    return
                step = self._undone.pop()
                for edit in step:
                    self._apply(edit)
                self._done.append(step)
    """},
    tests("""
    from mod import Doc
    class T(unittest.TestCase):
        def test_single_steps(self):
            d = Doc()
            d.insert(0, 'ab')
            d.insert(2, 'c')
            d.undo()
            self.assertEqual(d.text(), 'ab')
            d.redo()
            self.assertEqual(d.text(), 'abc')
            d.delete(0, 1)
            self.assertEqual(d.text(), 'bc')
            d.undo()
            self.assertEqual(d.text(), 'abc')
    """),
    tests("""
    from mod import Doc
    class T(unittest.TestCase):
        def test_group_is_one_step(self):
            d = Doc()
            d.insert(0, 'a')
            d.begin_group()
            d.insert(1, 'x')
            d.insert(2, 'y')
            d.delete(0, 1)
            d.end_group()
            self.assertEqual(d.text(), 'xy')
            d.undo()
            self.assertEqual(d.text(), 'a')
            d.redo()
            self.assertEqual(d.text(), 'xy')
        def test_nested_groups_outermost_only(self):
            d = Doc()
            d.begin_group()
            d.insert(0, 'a')
            d.begin_group()
            d.insert(1, 'b')
            d.end_group()
            d.insert(2, 'c')
            d.end_group()
            self.assertEqual(d.text(), 'abc')
            d.undo()
            self.assertEqual(d.text(), '')
            d.redo()
            self.assertEqual(d.text(), 'abc')
        def test_new_edit_discards_redo(self):
            d = Doc()
            d.insert(0, 'a')
            d.insert(1, 'b')
            d.undo()
            d.insert(1, 'c')
            d.redo()
            self.assertEqual(d.text(), 'ac')
            d.undo()
            d.undo()
            d.undo()
            self.assertEqual(d.text(), '')
        def test_open_group_blocks_history(self):
            d = Doc()
            d.insert(0, 'a')
            d.begin_group()
            d.insert(1, 'b')
            with self.assertRaises(RuntimeError):
                d.undo()
            with self.assertRaises(RuntimeError):
                d.redo()
            d.end_group()
            d.undo()
            self.assertEqual(d.text(), 'a')
        def test_bounds_change_nothing(self):
            d = Doc()
            d.insert(0, 'ab')
            with self.assertRaises(IndexError):
                d.insert(3, 'x')
            with self.assertRaises(IndexError):
                d.delete(1, 5)
            self.assertEqual(d.text(), 'ab')
            d.undo()
            self.assertEqual(d.text(), '')
        def test_nothing_to_do(self):
            d = Doc()
            d.undo()
            d.redo()
            self.assertEqual(d.text(), '')
            d.insert(0, 'a')
            d.undo()
            d.undo()
            d.redo()
            d.redo()
            self.assertEqual(d.text(), 'a')
    """),
    {
        "flat_groups": {"mod.py": """
            class Doc:
                def __init__(self):
                    self._text = ''
                    self._done = []
                    self._undone = []
                    self._depth = 0

                def text(self):
                    return self._text

                def begin_group(self):
                    self._depth += 1

                def end_group(self):
                    self._depth -= 1

                def _apply(self, edit):
                    kind, pos, s = edit
                    if kind == 'insert':
                        self._text = self._text[:pos] + s + self._text[pos:]
                    else:
                        self._text = self._text[:pos] + self._text[pos + len(s):]

                def _invert(self, edit):
                    kind, pos, s = edit
                    return ('delete' if kind == 'insert' else 'insert', pos, s)

                def _record(self, edit):
                    self._apply(edit)
                    self._undone.clear()
                    self._done.append(edit)

                def insert(self, pos, s):
                    if pos < 0 or pos > len(self._text):
                        raise IndexError(pos)
                    self._record(('insert', pos, s))

                def delete(self, pos, n):
                    if pos < 0 or pos + n > len(self._text):
                        raise IndexError(pos)
                    self._record(('delete', pos, self._text[pos:pos + n]))

                def undo(self):
                    if self._depth:
                        raise RuntimeError('group is open')
                    if not self._done:
                        return
                    edit = self._done.pop()
                    self._apply(self._invert(edit))
                    self._undone.append(edit)

                def redo(self):
                    if self._depth:
                        raise RuntimeError('group is open')
                    if not self._undone:
                        return
                    edit = self._undone.pop()
                    self._apply(edit)
                    self._done.append(edit)
        """},
        "redo_kept": {"mod.py": """
            class Doc:
                def __init__(self):
                    self._text = ''
                    self._done = []
                    self._undone = []
                    self._depth = 0
                    self._open = None

                def text(self):
                    return self._text

                def begin_group(self):
                    if self._depth == 0:
                        self._open = []
                    self._depth += 1

                def end_group(self):
                    self._depth -= 1
                    if self._depth == 0:
                        if self._open:
                            self._done.append(self._open)
                        self._open = None

                def _apply(self, edit):
                    kind, pos, s = edit
                    if kind == 'insert':
                        self._text = self._text[:pos] + s + self._text[pos:]
                    else:
                        self._text = self._text[:pos] + self._text[pos + len(s):]

                def _invert(self, edit):
                    kind, pos, s = edit
                    return ('delete' if kind == 'insert' else 'insert', pos, s)

                def _record(self, edit):
                    self._apply(edit)
                    if self._depth:
                        self._open.append(edit)
                    else:
                        self._done.append([edit])

                def insert(self, pos, s):
                    if pos < 0 or pos > len(self._text):
                        raise IndexError(pos)
                    self._record(('insert', pos, s))

                def delete(self, pos, n):
                    if pos < 0 or pos + n > len(self._text):
                        raise IndexError(pos)
                    self._record(('delete', pos, self._text[pos:pos + n]))

                def undo(self):
                    if self._depth:
                        raise RuntimeError('group is open')
                    if not self._done:
                        return
                    step = self._done.pop()
                    for edit in reversed(step):
                        self._apply(self._invert(edit))
                    self._undone.append(step)

                def redo(self):
                    if self._depth:
                        raise RuntimeError('group is open')
                    if not self._undone:
                        return
                    step = self._undone.pop()
                    for edit in step:
                        self._apply(edit)
                    self._done.append(step)
        """},
        "inner_groups_split": {"mod.py": """
            class Doc:
                def __init__(self):
                    self._text = ''
                    self._done = []
                    self._undone = []
                    self._stack = []

                def text(self):
                    return self._text

                def begin_group(self):
                    self._stack.append([])

                def end_group(self):
                    group = self._stack.pop()
                    if group:
                        self._done.append(group)

                def _apply(self, edit):
                    kind, pos, s = edit
                    if kind == 'insert':
                        self._text = self._text[:pos] + s + self._text[pos:]
                    else:
                        self._text = self._text[:pos] + self._text[pos + len(s):]

                def _invert(self, edit):
                    kind, pos, s = edit
                    return ('delete' if kind == 'insert' else 'insert', pos, s)

                def _record(self, edit):
                    self._apply(edit)
                    self._undone.clear()
                    if self._stack:
                        self._stack[-1].append(edit)
                    else:
                        self._done.append([edit])

                def insert(self, pos, s):
                    if pos < 0 or pos > len(self._text):
                        raise IndexError(pos)
                    self._record(('insert', pos, s))

                def delete(self, pos, n):
                    if pos < 0 or pos + n > len(self._text):
                        raise IndexError(pos)
                    self._record(('delete', pos, self._text[pos:pos + n]))

                def undo(self):
                    if self._stack:
                        raise RuntimeError('group is open')
                    if not self._done:
                        return
                    step = self._done.pop()
                    for edit in reversed(step):
                        self._apply(self._invert(edit))
                    self._undone.append(step)

                def redo(self):
                    if self._stack:
                        raise RuntimeError('group is open')
                    if not self._undone:
                        return
                    step = self._undone.pop()
                    for edit in step:
                        self._apply(edit)
                    self._done.append(step)
        """},
    },
    max_turns=12,
)

# -------------------------------------------------------------------------- 14
rung(
    "reconcile", 14, "Reconciliation", "two files, greedy matching with tie-breaks",
    """
    match(bank, ledger) pairs bank rows with ledger rows. Each row is a dict with
    'amount' (an int of cents), 'date' (a 'YYYY-MM-DD' string), and an optional 'ref'
    string. A bank row may pair with a ledger row only when the amounts are equal, the
    dates are at most 3 days apart in either direction, which rules.close_enough(a, b)
    in rules.py decides, and, when both rows carry a ref, the refs are equal. A row
    with no ref can pair with any ref. Each row is used at most once. Bank rows are
    processed in order, and each takes the allowed ledger row with the smallest date
    gap, and on a tie the one that comes first in ledger. The result is a tuple
    (pairs, unmatched_bank, unmatched_ledger): pairs is a list of (bank_index,
    ledger_index) tuples in bank order, and the two unmatched lists hold indexes in
    rising order. The bug is not necessarily in mod.py.
    """,
    [
        {"call": "match([{'amount': 5, 'date': '2026-01-10'}], [{'amount': 5, 'date': '2026-01-13'}])",
         "expect": "([(0, 0)], [], [])"},
        {"call": "match([{'amount': 5, 'date': '2026-01-10'}], [{'amount': 5, 'date': '2026-01-14'}])",
         "expect": "([], [0], [0])"},
        {"call": "match([{'amount': 5, 'date': '2026-01-10'}], [{'amount': 5, 'date': '2026-01-12'}, {'amount': 5, 'date': '2026-01-10'}])",
         "expect": "([(0, 1)], [], [0])"},
        {"call": "match([{'amount': 5, 'date': '2026-01-10'}], [{'amount': 5, 'date': '2026-01-11'}, {'amount': 5, 'date': '2026-01-09'}])",
         "expect": "([(0, 0)], [], [1])"},
        {"call": "match([{'amount': 5, 'date': '2026-01-10', 'ref': 'A'}], [{'amount': 5, 'date': '2026-01-10', 'ref': 'B'}, {'amount': 5, 'date': '2026-01-10'}])",
         "expect": "([(0, 1)], [], [0])"},
    ],
    {
        "mod.py": """
            from rules import close_enough


            def match(bank, ledger):
                used = set()
                pairs = []
                for i, row in enumerate(bank):
                    for j, entry in enumerate(ledger):
                        if j in used:
                            continue
                        if row['amount'] != entry['amount']:
                            continue
                        if not close_enough(row['date'], entry['date']):
                            continue
                        used.add(j)
                        pairs.append((i, j))
                        break
                matched_bank = {i for i, _ in pairs}
                unmatched_bank = [i for i in range(len(bank)) if i not in matched_bank]
                unmatched_ledger = [j for j in range(len(ledger)) if j not in used]
                return pairs, unmatched_bank, unmatched_ledger
        """,
        "rules.py": """
            from datetime import date


            def gap_days(a, b):
                return abs((date.fromisoformat(a) - date.fromisoformat(b)).days)


            def close_enough(a, b):
                return gap_days(a, b) < 3
        """,
    },
    {
        "mod.py": """
            from rules import close_enough, gap_days


            def _allowed(row, entry):
                if row['amount'] != entry['amount']:
                    return False
                if not close_enough(row['date'], entry['date']):
                    return False
                if 'ref' in row and 'ref' in entry and row['ref'] != entry['ref']:
                    return False
                return True


            def match(bank, ledger):
                used = set()
                pairs = []
                for i, row in enumerate(bank):
                    best = None
                    for j, entry in enumerate(ledger):
                        if j in used or not _allowed(row, entry):
                            continue
                        gap = gap_days(row['date'], entry['date'])
                        if best is None or gap < best[0]:
                            best = (gap, j)
                    if best is not None:
                        used.add(best[1])
                        pairs.append((i, best[1]))
                matched_bank = {i for i, _ in pairs}
                unmatched_bank = [i for i in range(len(bank)) if i not in matched_bank]
                unmatched_ledger = [j for j in range(len(ledger)) if j not in used]
                return pairs, unmatched_bank, unmatched_ledger
        """,
        "rules.py": """
            from datetime import date


            def gap_days(a, b):
                return abs((date.fromisoformat(a) - date.fromisoformat(b)).days)


            def close_enough(a, b):
                return gap_days(a, b) <= 3
        """,
    },
    tests("""
    from mod import match
    class T(unittest.TestCase):
        def test_exact(self):
            bank = [{'amount': 5, 'date': '2026-01-10'}, {'amount': 7, 'date': '2026-01-11'}]
            ledger = [{'amount': 7, 'date': '2026-01-11'}, {'amount': 5, 'date': '2026-01-10'}, {'amount': 9, 'date': '2026-01-11'}]
            self.assertEqual(match(bank, ledger), ([(0, 1), (1, 0)], [], [2]))
            self.assertEqual(match([{'amount': 5, 'date': '2026-01-10'}], [{'amount': 5, 'date': '2026-01-12'}]), ([(0, 0)], [], []))
    """),
    tests("""
    from mod import match
    from rules import close_enough
    class T(unittest.TestCase):
        def test_three_days_inclusive(self):
            self.assertEqual(match([{'amount': 5, 'date': '2026-01-10'}], [{'amount': 5, 'date': '2026-01-13'}]), ([(0, 0)], [], []))
            self.assertEqual(match([{'amount': 5, 'date': '2026-01-10'}], [{'amount': 5, 'date': '2026-01-07'}]), ([(0, 0)], [], []))
            self.assertEqual(match([{'amount': 5, 'date': '2026-01-10'}], [{'amount': 5, 'date': '2026-01-14'}]), ([], [0], [0]))
            self.assertTrue(close_enough('2026-01-31', '2026-02-03'))
            self.assertFalse(close_enough('2026-01-31', '2026-02-04'))
        def test_closest_wins(self):
            ledger = [{'amount': 5, 'date': '2026-01-12'}, {'amount': 5, 'date': '2026-01-10'}]
            self.assertEqual(match([{'amount': 5, 'date': '2026-01-10'}], ledger), ([(0, 1)], [], [0]))
        def test_tie_goes_to_first_in_ledger(self):
            ledger = [{'amount': 5, 'date': '2026-01-11'}, {'amount': 5, 'date': '2026-01-09'}]
            self.assertEqual(match([{'amount': 5, 'date': '2026-01-10'}], ledger), ([(0, 0)], [], [1]))
            ledger = [{'amount': 5, 'date': '2026-01-09'}, {'amount': 5, 'date': '2026-01-11'}]
            self.assertEqual(match([{'amount': 5, 'date': '2026-01-10'}], ledger), ([(0, 0)], [], [1]))
        def test_refs(self):
            ledger = [{'amount': 5, 'date': '2026-01-10', 'ref': 'B'}, {'amount': 5, 'date': '2026-01-10'}]
            self.assertEqual(match([{'amount': 5, 'date': '2026-01-10', 'ref': 'A'}], ledger), ([(0, 1)], [], [0]))
            ledger = [{'amount': 5, 'date': '2026-01-10', 'ref': 'B'}, {'amount': 5, 'date': '2026-01-10', 'ref': 'A'}]
            self.assertEqual(match([{'amount': 5, 'date': '2026-01-12', 'ref': 'A'}], ledger), ([(0, 1)], [], [0]))
            self.assertEqual(match([{'amount': 5, 'date': '2026-01-12'}], ledger), ([(0, 0)], [], [1]))
            self.assertEqual(match([{'amount': 5, 'date': '2026-01-12', 'ref': 'C'}], ledger), ([], [0], [0, 1]))
        def test_each_row_once_and_order(self):
            bank = [{'amount': 5, 'date': '2026-01-10'}, {'amount': 5, 'date': '2026-01-10'}, {'amount': 5, 'date': '2026-01-20'}]
            ledger = [{'amount': 5, 'date': '2026-01-10'}, {'amount': 1, 'date': '2026-01-10'}]
            self.assertEqual(match(bank, ledger), ([(0, 0)], [1, 2], [1]))
            bank = [{'amount': 5, 'date': '2026-01-10'}, {'amount': 5, 'date': '2026-01-10'}]
            ledger = [{'amount': 5, 'date': '2026-01-12'}, {'amount': 5, 'date': '2026-01-10'}]
            self.assertEqual(match(bank, ledger), ([(0, 1), (1, 0)], [], []))
    """),
    {
        "exclusive_days": {
            "mod.py": """
                from rules import close_enough, gap_days


                def _allowed(row, entry):
                    if row['amount'] != entry['amount']:
                        return False
                    if not close_enough(row['date'], entry['date']):
                        return False
                    if 'ref' in row and 'ref' in entry and row['ref'] != entry['ref']:
                        return False
                    return True


                def match(bank, ledger):
                    used = set()
                    pairs = []
                    for i, row in enumerate(bank):
                        best = None
                        for j, entry in enumerate(ledger):
                            if j in used or not _allowed(row, entry):
                                continue
                            gap = gap_days(row['date'], entry['date'])
                            if best is None or gap < best[0]:
                                best = (gap, j)
                        if best is not None:
                            used.add(best[1])
                            pairs.append((i, best[1]))
                    matched_bank = {i for i, _ in pairs}
                    unmatched_bank = [i for i in range(len(bank)) if i not in matched_bank]
                    unmatched_ledger = [j for j in range(len(ledger)) if j not in used]
                    return pairs, unmatched_bank, unmatched_ledger
            """,
            "rules.py": """
                from datetime import date


                def gap_days(a, b):
                    return abs((date.fromisoformat(a) - date.fromisoformat(b)).days)


                def close_enough(a, b):
                    return gap_days(a, b) < 3
            """,
        },
        "first_candidate": {
            "mod.py": """
                from rules import close_enough


                def _allowed(row, entry):
                    if row['amount'] != entry['amount']:
                        return False
                    if not close_enough(row['date'], entry['date']):
                        return False
                    if 'ref' in row and 'ref' in entry and row['ref'] != entry['ref']:
                        return False
                    return True


                def match(bank, ledger):
                    used = set()
                    pairs = []
                    for i, row in enumerate(bank):
                        for j, entry in enumerate(ledger):
                            if j in used or not _allowed(row, entry):
                                continue
                            used.add(j)
                            pairs.append((i, j))
                            break
                    matched_bank = {i for i, _ in pairs}
                    unmatched_bank = [i for i in range(len(bank)) if i not in matched_bank]
                    unmatched_ledger = [j for j in range(len(ledger)) if j not in used]
                    return pairs, unmatched_bank, unmatched_ledger
            """,
            "rules.py": """
                from datetime import date


                def gap_days(a, b):
                    return abs((date.fromisoformat(a) - date.fromisoformat(b)).days)


                def close_enough(a, b):
                    return gap_days(a, b) <= 3
            """,
        },
        "ref_required": {
            "mod.py": """
                from rules import close_enough, gap_days


                def _allowed(row, entry):
                    if row['amount'] != entry['amount']:
                        return False
                    if not close_enough(row['date'], entry['date']):
                        return False
                    if row.get('ref') != entry.get('ref'):
                        return False
                    return True


                def match(bank, ledger):
                    used = set()
                    pairs = []
                    for i, row in enumerate(bank):
                        best = None
                        for j, entry in enumerate(ledger):
                            if j in used or not _allowed(row, entry):
                                continue
                            gap = gap_days(row['date'], entry['date'])
                            if best is None or gap < best[0]:
                                best = (gap, j)
                        if best is not None:
                            used.add(best[1])
                            pairs.append((i, best[1]))
                    matched_bank = {i for i, _ in pairs}
                    unmatched_bank = [i for i in range(len(bank)) if i not in matched_bank]
                    unmatched_ledger = [j for j in range(len(ledger)) if j not in used]
                    return pairs, unmatched_bank, unmatched_ledger
            """,
            "rules.py": """
                from datetime import date


                def gap_days(a, b):
                    return abs((date.fromisoformat(a) - date.fromisoformat(b)).days)


                def close_enough(a, b):
                    return gap_days(a, b) <= 3
            """,
        },
    },
    max_turns=12,
)

# -------------------------------------------------------------------------- 15
rung(
    "ranges", 15, "Range counting at scale", "non-functional requirement, green tests",
    """
    count_in_ranges(points, ranges) takes a list of integers and a list of (lo, hi)
    pairs and returns a list with, for each pair in order, how many points p satisfy
    lo <= p <= hi. Points are unsorted and may repeat. A pair with hi below lo counts
    zero. The input lists are left as they were. Each list can hold 100000 entries and
    that size must finish in under 2 seconds on an ordinary machine. The public tests
    are small, but the hidden tests include the large size and time the call, so a
    loop over every point for every pair will fail.
    """,
    [
        {"call": "count_in_ranges([1, 5, 5, 9], [(1, 5), (6, 8), (5, 5)])", "expect": "[3, 0, 2]"},
        {"call": "count_in_ranges([], [(0, 1)])", "expect": "[0]"},
        {"call": "count_in_ranges([3], [(5, 1)])", "expect": "[0]"},
        {"call": "count_in_ranges([2, 4], [])", "expect": "[]"},
    ],
    {"mod.py": """
        def count_in_ranges(points, ranges):
            out = []
            for lo, hi in ranges:
                n = 0
                for p in points:
                    if lo <= p <= hi:
                        n += 1
                out.append(n)
            return out
    """},
    {"mod.py": """
        from bisect import bisect_left, bisect_right


        def count_in_ranges(points, ranges):
            xs = sorted(points)
            return [max(0, bisect_right(xs, hi) - bisect_left(xs, lo)) for lo, hi in ranges]
    """},
    tests("""
    from mod import count_in_ranges
    class T(unittest.TestCase):
        def test_small(self):
            self.assertEqual(count_in_ranges([1, 5, 5, 9], [(1, 5), (6, 8), (5, 5)]), [3, 0, 2])
            self.assertEqual(count_in_ranges([], [(0, 1)]), [0])
    """),
    tests("""
    import hashlib, json, random, time
    from mod import count_in_ranges
    class T(unittest.TestCase):
        def test_small(self):
            self.assertEqual(count_in_ranges([1, 5, 5, 9], [(1, 5), (6, 8), (5, 5)]), [3, 0, 2])
            self.assertEqual(count_in_ranges([3], [(5, 1)]), [0])
            self.assertEqual(count_in_ranges([2, 4], []), [])
            self.assertEqual(count_in_ranges([-5, 0, 5], [(-5, -5), (-10, 10), (1, 4)]), [1, 3, 0])
        def test_inputs_untouched(self):
            points = [9, 1, 5]
            ranges = [(1, 5)]
            self.assertEqual(count_in_ranges(points, ranges), [2])
            self.assertEqual(points, [9, 1, 5])
            self.assertEqual(ranges, [(1, 5)])
        def test_large_is_fast(self):
            rng = random.Random(7)
            n = 100000
            points = [rng.randint(0, 10 ** 6) for _ in range(n)]
            ranges = []
            for _ in range(n):
                a, b = rng.randint(0, 10 ** 6), rng.randint(0, 10 ** 6)
                ranges.append((min(a, b), max(a, b)))
            t0 = time.perf_counter()
            got = count_in_ranges(points, ranges)
            elapsed = time.perf_counter() - t0
            self.assertEqual(len(got), n)
            for i in range(0, n, n // 10):
                lo, hi = ranges[i]
                self.assertEqual(got[i], sum(1 for p in points if lo <= p <= hi))
            digest = hashlib.sha256(json.dumps([int(x) for x in got]).encode()).hexdigest()
            self.assertEqual(digest, '84f31c35062b05d6d46607b35f554f8cb99a91bee76b6a366277a2c42a63ddde')
            self.assertLess(elapsed, 2.0)
    """),
    {
        "sort_in_place": {"mod.py": """
            from bisect import bisect_left, bisect_right


            def count_in_ranges(points, ranges):
                points.sort()
                return [max(0, bisect_right(points, hi) - bisect_left(points, lo)) for lo, hi in ranges]
        """},
        "left_left": {"mod.py": """
            from bisect import bisect_left


            def count_in_ranges(points, ranges):
                xs = sorted(points)
                return [max(0, bisect_left(xs, hi) - bisect_left(xs, lo)) for lo, hi in ranges]
        """},
        "sorted_scan": {"mod.py": """
            def count_in_ranges(points, ranges):
                xs = sorted(points)
                out = []
                for lo, hi in ranges:
                    n = 0
                    for p in xs:
                        if p > hi:
                            break
                        if p >= lo:
                            n += 1
                    out.append(n)
                return out
        """},
    },
    max_turns=12, test_timeout=12.0,
)

# -------------------------------------------------------------------------- 16
rung(
    "allocate", 16, "Largest remainder", "spec above a wrong public test",
    """
    allocate(total, weights) splits the non-negative integer total into len(weights)
    non-negative integers that sum to total and are proportional to the weights, which
    are non-negative numbers that are not all zero. It uses the largest-remainder
    method: each part first gets the floor of its exact share, then the leftover units
    go one at a time to the parts with the largest fractional remainders. A tie between
    remainders goes to the earlier index. A weight of zero always gets zero.
    """,
    [
        {"call": "allocate(100, [1, 1, 1])", "expect": "[34, 33, 33]"},
        {"call": "allocate(10, [3, 3, 3])", "expect": "[4, 3, 3]"},
        {"call": "allocate(7, [0, 1])", "expect": "[0, 7]"},
        {"call": "allocate(7, [1, 1, 2])", "expect": "[2, 2, 3]"},
        {"call": "allocate(0, [1, 2])", "expect": "[0, 0]"},
    ],
    {"mod.py": """
        def allocate(total, weights):
            s = sum(weights)
            return [round(total * w / s) for w in weights]
    """},
    {"mod.py": """
        from fractions import Fraction


        def allocate(total, weights):
            s = sum(weights)
            exact = [Fraction(total) * Fraction(w) / Fraction(s) for w in weights]
            parts = [int(x) for x in exact]
            left = total - sum(parts)
            order = sorted(range(len(weights)), key=lambda i: (-(exact[i] - parts[i]), i))
            for i in order[:left]:
                parts[i] += 1
            return parts
    """},
    tests("""
    from mod import allocate
    class T(unittest.TestCase):
        def test_half(self):
            self.assertEqual(allocate(10, [1, 1]), [5, 5])
        def test_split(self):
            self.assertEqual(allocate(100, [1, 1, 1]), [33, 33, 34])
    """),
    tests("""
    from mod import allocate
    class T(unittest.TestCase):
        def test_tie_goes_to_earlier_index(self):
            self.assertEqual(allocate(100, [1, 1, 1]), [34, 33, 33])
            self.assertEqual(allocate(10, [3, 3, 3]), [4, 3, 3])
        def test_zero_weight_and_ties(self):
            self.assertEqual(allocate(7, [0, 1]), [0, 7])
            self.assertEqual(allocate(5, [0, 1, 1]), [0, 3, 2])
        def test_remainders(self):
            self.assertEqual(allocate(7, [1, 1, 2]), [2, 2, 3])
            self.assertEqual(allocate(10, [1, 2, 3]), [2, 3, 5])
            self.assertEqual(allocate(11, [1, 2, 3]), [2, 4, 5])
        def test_sum_and_bounds(self):
            parts = allocate(1000, [7, 13, 29])
            self.assertEqual(sum(parts), 1000)
            self.assertTrue(all(p >= 0 for p in parts))
            self.assertEqual(allocate(0, [1, 2]), [0, 0])
            self.assertEqual(allocate(9, [5]), [9])
    """),
    {
        "last_index_tie": {"mod.py": """
            from fractions import Fraction


            def allocate(total, weights):
                s = sum(weights)
                exact = [Fraction(total) * Fraction(w) / Fraction(s) for w in weights]
                parts = [int(x) for x in exact]
                left = total - sum(parts)
                order = sorted(range(len(weights)), key=lambda i: (-(exact[i] - parts[i]), -i))
                for i in order[:left]:
                    parts[i] += 1
                return parts
        """},
        "round_then_fixup": {"mod.py": """
            def allocate(total, weights):
                s = sum(weights)
                parts = [round(total * w / s) for w in weights]
                parts[0] += total - sum(parts)
                return parts
        """},
    },
    public_passes_on_bug=False, gold_passes_public=False, max_turns=12,
    note="One assertion in test_public.py contradicts SPEC.txt. The spec is the authority and "
         "tests cannot be edited. Make the code match the spec, then stop even though that one "
         "public assertion stays red.",
)


# Hidden cases that already pass on the untouched bug. Partial credit is reported
# as gain above this floor. --check verifies the list against the bug.
BUG_PASSES = {
    "pages": ["test_exact", "test_zero"],
    "slug": [],
    "semver": [],
    "intervals": ["test_empty", "test_input_untouched"],
    "lru": ["test_capacity_one", "test_missing_get_has_no_side_effect", "test_update_never_evicts"],
    "bucket": [],
    "config": ["test_bool_bad_word", "test_env_over_file_int", "test_extra_keys_ignored", "test_file_bool_used_as_is"],
    "toposort": ["test_empty", "test_implicit_nodes"],
    "shlex": [],
    "jsonptr": [],
    "cron": ["test_only_one_restricted", "test_other_fields"],
    "expr": ["test_spacing_and_mixing", "test_types"],
    "undo": ["test_bounds_change_nothing", "test_nothing_to_do"],
    "reconcile": ["test_tie_goes_to_first_in_ledger"],
    "ranges": ["test_inputs_untouched", "test_small"],
    "allocate": ["test_sum_and_bounds"],
}
for _r in RUNGS:
    _r["bug_passes"] = BUG_PASSES[_r["id"]]


def ladder_hash() -> str:
    """Hash of everything that affects a score, so results say which ladder they ran."""
    h = hashlib.sha256()
    for r in RUNGS:
        for key in ("id", "level", "spec", "files_buggy", "public", "hidden", "note", "max_turns",
                    "test_timeout", "gold_passes_public"):
            h.update(json.dumps(r[key], sort_keys=True).encode())
    return h.hexdigest()[:12]


def by_id(ids: list[str]) -> list[dict]:
    want = set(ids)
    return [r for r in RUNGS if r["id"] in want or str(r["level"]) in want]


assert [r["level"] for r in RUNGS] == list(range(1, len(RUNGS) + 1)), "levels must be 1..n in order"
