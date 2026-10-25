#!/usr/bin/env python3
"""Eight repairs, each harder than the last. Hidden tests are the score."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import loop

MAX_TURNS = 6
HOST = None
MODEL = None

TASKS = []


def add(id, level, spec, files_buggy, files_gold, public, hidden, public_passes):
    TASKS.append({
        "id": id,
        "level": level,
        "spec": spec,
        "files_buggy": files_buggy,
        "files_gold": files_gold,
        "public": public,
        "hidden": hidden,
        "public_passes_on_bug": public_passes,
    })


add(
    "clamp", 1,
    "clamp(x, lo, hi) brings x into the closed range. "
    "A value inside, including the two ends, stays as it is. "
    "A value past an end becomes that end. "
    "clamp(5, 0, 10) is 5. clamp(0, 0, 10) is 0. clamp(10, 0, 10) is 10. clamp(-3, 0, 10) is 0.",
    {"mod.py":
     "def clamp(x, lo, hi):\n"
     "    if lo < x < hi:\n"
     "        return x\n"
     "    if x > hi:\n"
     "        return hi\n"
     "    if x < lo:\n"
     "        return lo\n"
     "    return None\n"},
    {"mod.py":
     "def clamp(x, lo, hi):\n"
     "    if x < lo:\n"
     "        return lo\n"
     "    if x > hi:\n"
     "        return hi\n"
     "    return x\n"},
    "import unittest\nfrom mod import clamp\n"
    "class T(unittest.TestCase):\n"
    "    def test_mid(self):\n"
    "        self.assertEqual(clamp(5, 0, 10), 5)\n"
    "        self.assertEqual(clamp(-3, 0, 10), 0)\n"
    "        self.assertEqual(clamp(15, 0, 10), 10)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import clamp\n"
    "class T(unittest.TestCase):\n"
    "    def test_ends(self):\n"
    "        self.assertEqual(clamp(0, 0, 10), 0)\n"
    "        self.assertEqual(clamp(10, 0, 10), 10)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    True,
)

add(
    "csv", 2,
    "parse_row(line) splits one CSV line into fields. A comma inside double quotes is not a separator. "
    "A doubled quote inside quotes is one quote character. "
    "parse_row('a,b,c') is ['a','b','c']. "
    "parse_row('\"a,b\",c') is ['a,b','c']. "
    "parse_row('\"say \"\"hi\"\"\",z') is ['say \"hi\"','z'].",
    {"mod.py": "def parse_row(line):\n    return line.split(',')\n"},
    {"mod.py":
     "def parse_row(line):\n"
     "    out, cur, q, i = [], [], False, 0\n"
     "    while i < len(line):\n"
     "        ch = line[i]\n"
     "        if q:\n"
     "            if ch == '\"':\n"
     "                if i + 1 < len(line) and line[i + 1] == '\"':\n"
     "                    cur.append('\"')\n"
     "                    i += 2\n"
     "                    continue\n"
     "                q = False\n"
     "            else:\n"
     "                cur.append(ch)\n"
     "        elif ch == '\"':\n"
     "            q = True\n"
     "        elif ch == ',':\n"
     "            out.append(''.join(cur))\n"
     "            cur = []\n"
     "        else:\n"
     "            cur.append(ch)\n"
     "        i += 1\n"
     "    out.append(''.join(cur))\n"
     "    return out\n"},
    "import unittest\nfrom mod import parse_row\n"
    "class T(unittest.TestCase):\n"
    "    def test_plain(self):\n"
    "        self.assertEqual(parse_row('a,b,c'), ['a', 'b', 'c'])\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import parse_row\n"
    "class T(unittest.TestCase):\n"
    "    def test_quotes(self):\n"
    "        self.assertEqual(parse_row('\"a,b\",c'), ['a,b', 'c'])\n"
    "        self.assertEqual(parse_row('\"say \"\"hi\"\"\",z'), ['say \"hi\"', 'z'])\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    True,
)

add(
    "comment", 3,
    "normalize(line) strips ends and removes a comment. "
    "A comment starts at the first # that is not inside double quotes. "
    "normalize('  hello  ') is 'hello'. normalize('x # c') is 'x'. "
    "normalize('say \"#\" there') is 'say \"#\" there'.",
    {"mod.py":
     "def strip_comment(line):\n"
     "    if '#' in line:\n"
     "        return line.split('#', 1)[0].rstrip()\n"
     "    return line\n"
     "def normalize(line):\n"
     "    return strip_comment(line).strip()\n"},
    {"mod.py":
     "def strip_comment(line):\n"
     "    out, q = [], False\n"
     "    for ch in line:\n"
     "        if ch == '\"':\n"
     "            q = not q\n"
     "            out.append(ch)\n"
     "        elif ch == '#' and not q:\n"
     "            break\n"
     "        else:\n"
     "            out.append(ch)\n"
     "    return ''.join(out).rstrip()\n"
     "def normalize(line):\n"
     "    return strip_comment(line).strip()\n"},
    "import unittest\nfrom mod import normalize\n"
    "class T(unittest.TestCase):\n"
    "    def test_plain(self):\n"
    "        self.assertEqual(normalize('  hello  '), 'hello')\n"
    "        self.assertEqual(normalize('x # c'), 'x')\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import normalize\n"
    "class T(unittest.TestCase):\n"
    "    def test_quote(self):\n"
    "        self.assertEqual(normalize('say \"#\" there'), 'say \"#\" there')\n"
    "        self.assertEqual(normalize('  a # b'), 'a')\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    True,
)

add(
    "rolling", 4,
    "Rolling(n) keeps the last n values. add(x) records x. "
    "mean() is the average of the values still kept. Before n values exist, average the ones you have. "
    "After more than n, the oldest leaves. "
    "Rolling(2) then add 10, add 10, mean is 10. "
    "Rolling(2) then add 0, add 0, add 10, mean is 5.",
    {"mod.py":
     "class Rolling:\n"
     "    def __init__(self, n):\n"
     "        self.n = n\n"
     "        self.xs = []\n"
     "    def add(self, x):\n"
     "        self.xs.append(x)\n"
     "    def mean(self):\n"
     "        return sum(self.xs) / len(self.xs)\n"},
    {"mod.py":
     "class Rolling:\n"
     "    def __init__(self, n):\n"
     "        self.n = n\n"
     "        self.xs = []\n"
     "    def add(self, x):\n"
     "        self.xs.append(x)\n"
     "        if len(self.xs) > self.n:\n"
     "            self.xs.pop(0)\n"
     "    def mean(self):\n"
     "        return sum(self.xs) / len(self.xs)\n"},
    "import unittest\nfrom mod import Rolling\n"
    "class T(unittest.TestCase):\n"
    "    def test_same(self):\n"
    "        r = Rolling(2)\n"
    "        r.add(10)\n"
    "        r.add(10)\n"
    "        self.assertEqual(r.mean(), 10)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import Rolling\n"
    "class T(unittest.TestCase):\n"
    "    def test_drop(self):\n"
    "        r = Rolling(2)\n"
    "        r.add(0)\n"
    "        r.add(0)\n"
    "        r.add(10)\n"
    "        self.assertEqual(r.mean(), 5)\n"
    "    def test_three(self):\n"
    "        r = Rolling(3)\n"
    "        for x in (1, 2, 3, 6):\n"
    "            r.add(x)\n"
    "        self.assertEqual(r.mean(), 11 / 3)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    True,
)

add(
    "tax", 5,
    "Two files. mod.total(cents) returns cents plus tax. rates.tax(cents) is 8 percent of cents, "
    "rounded half up to the nearest cent. Positive amounts only. "
    "total(100) is 108. total(19) is 21. total(44) is 48. The bug is not necessarily in mod.py.",
    {
        "mod.py": "from rates import tax\ndef total(cents):\n    return cents + tax(cents)\n",
        "rates.py": "def tax(cents):\n    return int(cents * 0.08)\n",
    },
    {
        "mod.py": "from rates import tax\ndef total(cents):\n    return cents + tax(cents)\n",
        "rates.py": "def tax(cents):\n    return int(cents * 8 / 100 + 0.5)\n",
    },
    "import unittest\nfrom mod import total\n"
    "class T(unittest.TestCase):\n"
    "    def test_even(self):\n"
    "        self.assertEqual(total(100), 108)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import total\n"
    "class T(unittest.TestCase):\n"
    "    def test_half(self):\n"
    "        self.assertEqual(total(19), 21)\n"
    "        self.assertEqual(total(44), 48)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    True,
)

add(
    "rooms", 6,
    "can_book(booked, start, end) is true when [start, end) does not overlap any booked pair. "
    "Each pair is half-open too. A meeting that starts when another ends is allowed. "
    "can_book([], 1, 2) is True. can_book([(0, 1)], 2, 3) is True. "
    "can_book([(0, 2)], 2, 4) is True. can_book([(0, 3)], 2, 4) is False.",
    {"mod.py":
     "def can_book(booked, start, end):\n"
     "    for a, b in booked:\n"
     "        if not (end < a or start > b):\n"
     "            return False\n"
     "    return True\n"},
    {"mod.py":
     "def can_book(booked, start, end):\n"
     "    for a, b in booked:\n"
     "        if start < b and end > a:\n"
     "            return False\n"
     "    return True\n"},
    "import unittest\nfrom mod import can_book\n"
    "class T(unittest.TestCase):\n"
    "    def test_gap(self):\n"
    "        self.assertTrue(can_book([], 1, 2))\n"
    "        self.assertTrue(can_book([(0, 1)], 2, 3))\n"
    "        self.assertFalse(can_book([(0, 3)], 1, 2))\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import can_book\n"
    "class T(unittest.TestCase):\n"
    "    def test_touch(self):\n"
    "        self.assertTrue(can_book([(0, 2)], 2, 4))\n"
    "        self.assertFalse(can_book([(0, 3)], 2, 4))\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    True,
)

add(
    "transfer", 7,
    "transfer(src, dst, amount) moves amount from src to dst when src has at least amount. "
    "It returns the two balances. If src cannot cover amount, it moves nothing and subtracts a fee of 1 from src. "
    "The fee may make src negative. dst is unchanged in that case. "
    "transfer(10, 5, 3) is (7, 8). transfer(2, 5, 3) is (1, 5).",
    {"mod.py":
     "def transfer(src, dst, amount):\n"
     "    if src >= amount:\n"
     "        return src - amount, dst + amount\n"
     "    return src, dst - 1\n"},
    {"mod.py":
     "def transfer(src, dst, amount):\n"
     "    if src >= amount:\n"
     "        return src - amount, dst + amount\n"
     "    return src - 1, dst\n"},
    "import unittest\nfrom mod import transfer\n"
    "class T(unittest.TestCase):\n"
    "    def test_ok(self):\n"
    "        self.assertEqual(transfer(10, 5, 3), (7, 8))\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import transfer\n"
    "class T(unittest.TestCase):\n"
    "    def test_fee(self):\n"
    "        self.assertEqual(transfer(2, 5, 3), (1, 5))\n"
    "        self.assertEqual(transfer(0, 4, 1), (-1, 4))\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    True,
)

add(
    "backoff", 8,
    "delays(tries, base, cap) returns `tries` wait times. The first is base. Each next doubles. "
    "No wait is above cap. Once the doubled value would pass cap, later waits stay at cap. "
    "delays(3, 1, 100) is [1, 2, 4]. delays(5, 1, 6) is [1, 2, 4, 6, 6]. "
    "delays(1, 2, 10) is [2]. delays(0, 1, 10) is [].",
    {"mod.py":
     "def delays(tries, base, cap):\n"
     "    out, cur = [], base\n"
     "    for _ in range(tries):\n"
     "        out.append(cur)\n"
     "        cur *= 2\n"
     "    return out\n"},
    {"mod.py":
     "def delays(tries, base, cap):\n"
     "    out, cur = [], base\n"
     "    for _ in range(tries):\n"
     "        out.append(min(cur, cap))\n"
     "        cur = min(cur * 2, cap)\n"
     "    return out\n"},
    "import unittest\nfrom mod import delays\n"
    "class T(unittest.TestCase):\n"
    "    def test_under(self):\n"
    "        self.assertEqual(delays(3, 1, 100), [1, 2, 4])\n"
    "        self.assertEqual(delays(0, 1, 10), [])\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import delays\n"
    "class T(unittest.TestCase):\n"
    "    def test_cap(self):\n"
    "        self.assertEqual(delays(5, 1, 6), [1, 2, 4, 6, 6])\n"
    "        self.assertEqual(delays(1, 2, 10), [2])\n"
    "        self.assertEqual(delays(4, 3, 3), [3, 3, 3, 3])\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    True,
)


def materialize(task, files, root: Path) -> Path:
    wd = root / task["id"]
    if wd.exists():
        shutil.rmtree(wd)
    wd.mkdir(parents=True)
    for name, src in files.items():
        path = wd / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(src)
    (wd / "SPEC.txt").write_text(task["spec"] + "\n")
    (wd / "test_public.py").write_text(task["public"])
    return wd


def grade(task, files) -> dict:
    root = Path(tempfile.mkdtemp(prefix="grade2-"))
    try:
        wd = materialize(task, files, root)
        pub, _ = loop.run_py(wd, task["public"])
        hid, hid_text = loop.run_py(wd, task["hidden"])
        return {"public": pub, "hidden": hid, "hidden_tail": hid_text[-500:]}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def chat(messages):
    body = {
        "model": MODEL,
        "stream": False,
        "think": False,
        "keep_alive": "20m",
        "options": {"temperature": 0, "num_predict": 2400},
        "messages": messages,
        "tools": loop.TOOLS,
    }
    req = urllib.request.Request(
        HOST.rstrip("/") + "/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.load(resp)
    msg = data.get("message") or {}
    return msg, round(time.perf_counter() - t0, 2)


def one(task) -> dict:
    root = Path(tempfile.mkdtemp(prefix="repair2-"))
    wd = materialize(task, task["files_buggy"], root)
    names = ", ".join(task["files_buggy"])
    user = (
        f"Level {task['level']} of 8. Fix the project so it matches SPEC.txt. "
        f"Source files: {names}. "
        "Use read_file, write_file, and run_tests. "
        "Public tests are test_public.py. Do not stop while run_tests still fails. "
        "A green public run can still leave the spec wrong.\n\n"
        + task["spec"]
    )
    messages = [
        {"role": "system", "content": "You repair this small Python project. Call tools. Do not write the tests."},
        {"role": "user", "content": user},
    ]
    t0 = time.perf_counter()
    turns = 0
    try:
        for n in range(1, MAX_TURNS + 1):
            msg, seconds = chat(messages)
            calls = msg.get("tool_calls") or []
            assistant = {"role": "assistant", "content": msg.get("content") or ""}
            if calls:
                assistant["tool_calls"] = calls
            messages.append(assistant)
            turns = n
            if not calls:
                print(f"  turn {n} stop {seconds}s", flush=True)
                break
            names_called = []
            for call in calls:
                fn = call.get("function") or call
                name = fn.get("name")
                names_called.append(name)
                result = loop.dispatch(wd, name, fn.get("arguments") or {})
                messages.append({"role": "tool", "content": result[:4000], "tool_name": name})
            print(f"  turn {n} tools={names_called} {seconds}s", flush=True)
        files = {name: (wd / name).read_text() for name in task["files_buggy"]}
        scored = grade(task, files)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return {
        "id": task["id"],
        "level": task["level"],
        "turns": turns,
        "seconds": round(time.perf_counter() - t0, 2),
        "public": scored["public"],
        "hidden": scored["hidden"],
        "hidden_tail": scored["hidden_tail"],
    }


def check() -> int:
    fails = 0
    for task in TASKS:
        bug = grade(task, task["files_buggy"])
        gold = grade(task, task["files_gold"])
        ok = gold["public"] and gold["hidden"] and not bug["hidden"]
        ok = ok and bug["public"] == task["public_passes_on_bug"]
        print(("ok" if ok else "FAIL"), f"L{task['level']}", task["id"],
              "bug_public", bug["public"], "bug_hidden", bug["hidden"])
        if not ok:
            fails += 1
            print(bug["hidden_tail"][:400])
            print("GOLD", gold)
    print("fails", fails)
    return fails


def main():
    global HOST, MODEL
    if "--check" in sys.argv:
        sys.exit(1 if check() else 0)
    HOST, MODEL = sys.argv[1], sys.argv[2]
    rows = []
    for task in TASKS:
        print(f"== L{task['level']} {task['id']}", flush=True)
        try:
            row = one(task)
        except Exception as exc:
            row = {"id": task["id"], "level": task["level"], "error": str(exc)[:400], "hidden": False}
        rows.append(row)
        print(task["id"], "hidden" if row.get("hidden") else "MISS", "turns", row.get("turns"), "s", row.get("seconds"), flush=True)
    passed = sum(1 for r in rows if r.get("hidden"))
    safe = MODEL.replace(":", "-").replace("/", "-")
    path = Path(__file__).resolve().parent / "results" / f"results2-{safe}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"model": MODEL, "passed": passed, "n": len(rows), "rows": rows}, indent=2))
    print("WROTE", path, "PASSED", passed, "/", len(rows))


if __name__ == "__main__":
    main()
