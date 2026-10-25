#!/usr/bin/env python3
"""Eight small repairs. The model may read, write, and run public tests.

Hidden tests are the score. They follow the spec and are not in the workdir.
Up to 5 model turns. Thinking off.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HOST = None
MODEL = None
MAX_TURNS = 5

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file in the project.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Replace a project source file. Do not write tests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run the public tests. Returns pass or the failure text.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

TASKS = []  # filled below


def T(id, spec, buggy, gold, public, hidden, public_passes_on_bug):
    TASKS.append({
        "id": id,
        "spec": spec,
        "buggy": buggy,
        "gold": gold,
        "public": public,
        "hidden": hidden,
        "public_passes_on_bug": public_passes_on_bug,
    })


T(
    "chunks",
    "chunks(xs, n) splits xs into lists of length n. The last list may be shorter. "
    "chunks([1,2,3,4,5], 2) is [[1,2],[3,4],[5]]. chunks([], 3) is []. chunks([1,2], 5) is [[1,2]].",
    "def chunks(xs, n):\n"
    "    out = []\n"
    "    i = 0\n"
    "    while i + n <= len(xs):\n"
    "        out.append(xs[i:i + n])\n"
    "        i += n\n"
    "    return out\n",
    "def chunks(xs, n):\n"
    "    return [xs[i:i + n] for i in range(0, len(xs), n)]\n",
    "import unittest\nfrom mod import chunks\n"
    "class T(unittest.TestCase):\n"
    "    def test_even(self):\n"
    "        self.assertEqual(chunks([1, 2, 3, 4], 2), [[1, 2], [3, 4]])\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import chunks\n"
    "class T(unittest.TestCase):\n"
    "    def test_tail(self):\n"
    "        self.assertEqual(chunks([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])\n"
    "    def test_empty(self):\n"
    "        self.assertEqual(chunks([], 3), [])\n"
    "    def test_short(self):\n"
    "        self.assertEqual(chunks([1, 2], 5), [[1, 2]])\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    True,
)

T(
    "median",
    "median(nums) sorts the values. An odd count returns the middle value as a float. "
    "An even count returns the average of the two middle values as a float. "
    "median([1,2,3]) is 2.0. median([1,2,3,4]) is 2.5. median([1]) is 1.0.",
    "def median(nums):\n"
    "    xs = sorted(nums)\n"
    "    return float(xs[len(xs) // 2])\n",
    "def median(nums):\n"
    "    xs = sorted(nums)\n"
    "    n = len(xs)\n"
    "    if n % 2:\n"
    "        return float(xs[n // 2])\n"
    "    return (xs[n // 2 - 1] + xs[n // 2]) / 2\n",
    "import unittest\nfrom mod import median\n"
    "class T(unittest.TestCase):\n"
    "    def test_odd(self):\n"
    "        self.assertEqual(median([1, 2, 3]), 2.0)\n"
    "        self.assertEqual(median([1]), 1.0)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import median\n"
    "class T(unittest.TestCase):\n"
    "    def test_even(self):\n"
    "        self.assertEqual(median([1, 2, 3, 4]), 2.5)\n"
    "        self.assertEqual(median([10, 0]), 5.0)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    True,
)

T(
    "second",
    "second_largest(nums) returns the largest value strictly less than the maximum. "
    "Duplicates of the maximum do not count. second_largest([5,1,5]) is 1. "
    "second_largest([3,3,3]) is None. second_largest([1,2]) is 1.",
    "def second_largest(nums):\n"
    "    a = b = None\n"
    "    for n in nums:\n"
    "        if a is None or n > a:\n"
    "            b = a\n"
    "            a = n\n"
    "        elif b is None or n > b:\n"
    "            b = n\n"
    "    return b\n",
    "def second_largest(nums):\n"
    "    a = b = None\n"
    "    for n in nums:\n"
    "        if a is None or n > a:\n"
    "            b = a\n"
    "            a = n\n"
    "        elif n != a and (b is None or n > b):\n"
    "            b = n\n"
    "    return b\n",
    "import unittest\nfrom mod import second_largest\n"
    "class T(unittest.TestCase):\n"
    "    def test_distinct(self):\n"
    "        self.assertEqual(second_largest([1, 2, 3]), 2)\n"
    "        self.assertEqual(second_largest([1, 2]), 1)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import second_largest\n"
    "class T(unittest.TestCase):\n"
    "    def test_dups(self):\n"
    "        self.assertEqual(second_largest([5, 1, 5]), 1)\n"
    "        self.assertEqual(second_largest([4, 4, 2, 4]), 2)\n"
    "    def test_all_same(self):\n"
    "        self.assertIsNone(second_largest([3, 3, 3]))\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    True,
)

T(
    "holiday",
    "add_business_days(start, n, holidays) returns the date n open days after start. "
    "Do not count start. Skip Saturday, Sunday, and any date in holidays. "
    "Dates are 'YYYY-MM-DD'. holidays is a set of those strings. "
    "add_business_days('2026-10-16', 1, set()) is '2026-10-19'. "
    "add_business_days('2026-11-25', 1, {'2026-11-26', '2026-11-27'}) is '2026-11-30'.",
    "import datetime as dt\n"
    "def add_business_days(start, n, holidays):\n"
    "    d = dt.date.fromisoformat(start)\n"
    "    left = n\n"
    "    while left:\n"
    "        d += dt.timedelta(days=1)\n"
    "        if d.weekday() < 5:\n"
    "            left -= 1\n"
    "    return d.isoformat()\n",
    "import datetime as dt\n"
    "def add_business_days(start, n, holidays):\n"
    "    d = dt.date.fromisoformat(start)\n"
    "    closed = set(holidays)\n"
    "    left = n\n"
    "    while left:\n"
    "        d += dt.timedelta(days=1)\n"
    "        if d.weekday() < 5 and d.isoformat() not in closed:\n"
    "            left -= 1\n"
    "    return d.isoformat()\n",
    "import unittest\nfrom mod import add_business_days\n"
    "class T(unittest.TestCase):\n"
    "    def test_weekend(self):\n"
    "        self.assertEqual(add_business_days('2026-10-16', 1, set()), '2026-10-19')\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import add_business_days\n"
    "class T(unittest.TestCase):\n"
    "    def test_holiday(self):\n"
    "        closed = {'2026-11-26', '2026-11-27'}\n"
    "        self.assertEqual(add_business_days('2026-11-25', 1, closed), '2026-11-30')\n"
    "    def test_two(self):\n"
    "        self.assertEqual(add_business_days('2026-10-16', 5, set()), '2026-10-23')\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    True,
)

T(
    "duration",
    "parse_duration(text) reads hours and minutes. '1h20m' is 80, '45m' is 45, '2h' is 120, '0m' is 0. No seconds.",
    "def parse_duration(text):\n"
    "    hours = minutes = 0\n"
    "    num = ''\n"
    "    for ch in text:\n"
    "        if ch.isdigit():\n"
    "            num += ch\n"
    "        elif ch == 'h':\n"
    "            hours = int(num or 0)\n"
    "            num = ''\n"
    "        elif ch == 'm':\n"
    "            minutes = int(num or 0)\n"
    "            num = ''\n"
    "    return hours * 60\n",
    "def parse_duration(text):\n"
    "    hours = minutes = 0\n"
    "    num = ''\n"
    "    for ch in text:\n"
    "        if ch.isdigit():\n"
    "            num += ch\n"
    "        elif ch == 'h':\n"
    "            hours = int(num or 0)\n"
    "            num = ''\n"
    "        elif ch == 'm':\n"
    "            minutes = int(num or 0)\n"
    "            num = ''\n"
    "    return hours * 60 + minutes\n",
    "import unittest\nfrom mod import parse_duration\n"
    "class T(unittest.TestCase):\n"
    "    def test_both(self):\n"
    "        self.assertEqual(parse_duration('1h20m'), 80)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import parse_duration\n"
    "class T(unittest.TestCase):\n"
    "    def test_edges(self):\n"
    "        self.assertEqual(parse_duration('45m'), 45)\n"
    "        self.assertEqual(parse_duration('2h'), 120)\n"
    "        self.assertEqual(parse_duration('0m'), 0)\n"
    "        self.assertEqual(parse_duration('1h5m'), 65)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    False,
)

T(
    "ledger",
    "apply_ledger(balance, txns) applies each integer in order. "
    "A positive value is a deposit and always applies. "
    "A negative value applies only when the balance would stay zero or above. "
    "If it would go negative, reject it and subtract a fee of 5 instead. The fee may go negative. "
    "apply_ledger(70, [-80]) is 65. apply_ledger(100, [-50]) is 50.",
    "def apply_ledger(balance, txns):\n"
    "    for tx in txns:\n"
    "        balance += tx\n"
    "    return balance\n",
    "def apply_ledger(balance, txns):\n"
    "    for tx in txns:\n"
    "        if tx >= 0 or balance + tx >= 0:\n"
    "            balance += tx\n"
    "        else:\n"
    "            balance -= 5\n"
    "    return balance\n",
    "import unittest\nfrom mod import apply_ledger\n"
    "class T(unittest.TestCase):\n"
    "    def test_reject(self):\n"
    "        self.assertEqual(apply_ledger(70, [-80]), 65)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import apply_ledger\n"
    "class T(unittest.TestCase):\n"
    "    def test_mix(self):\n"
    "        self.assertEqual(apply_ledger(100, [-50, -80, 5]), 50)\n"
    "        self.assertEqual(apply_ledger(10, [-3, -9]), 2)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    False,
)

T(
    "discount",
    "discount_total(rows) sums qty*price. A row with qty of 3 or more is 10 percent off. "
    "Other rows are full price. Return a number. "
    "[{'qty':2,'price':10}] is 20. "
    "[{'qty':2,'price':10},{'qty':3,'price':10},{'qty':5,'price':4}] is 65.",
    "def discount_total(rows):\n"
    "    total = 0\n"
    "    for row in rows:\n"
    "        total += row['qty'] * row['price'] * 0.9\n"
    "    return total\n",
    "def discount_total(rows):\n"
    "    total = 0.0\n"
    "    for row in rows:\n"
    "        line = row['qty'] * row['price']\n"
    "        if row['qty'] >= 3:\n"
    "            line *= 0.9\n"
    "        total += line\n"
    "    return total\n",
    "import unittest\nfrom mod import discount_total\n"
    "class T(unittest.TestCase):\n"
    "    def test_full(self):\n"
    "        self.assertEqual(discount_total([{'qty': 2, 'price': 10}]), 20)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import discount_total\n"
    "class T(unittest.TestCase):\n"
    "    def test_mix(self):\n"
    "        rows = [{'qty': 2, 'price': 10}, {'qty': 3, 'price': 10}, {'qty': 5, 'price': 4}]\n"
    "        self.assertEqual(discount_total(rows), 65)\n"
    "    def test_only_off(self):\n"
    "        self.assertEqual(discount_total([{'qty': 3, 'price': 10}]), 27)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    False,
)

T(
    "garage",
    "stay_charge(start, end) takes 'HH:MM' times. "
    "If end is later the same day, the stay is that day. "
    "If end is earlier, the stay crossed midnight. "
    "If the times are equal, the charge is 0. "
    "Charge 3 for the first hour and 2 for each further hour, capped at 18 per calendar day. The cap resets at midnight. "
    "A partial hour rounds up. "
    "stay_charge('10:10','18:40') is 18. stay_charge('22:00','03:30') is 14. "
    "stay_charge('10:00','10:00') is 0. stay_charge('23:30','00:30') is 6.",
    "def stay_charge(start, end):\n"
    "    def minutes(hhmm):\n"
    "        h, m = hhmm.split(':')\n"
    "        return int(h) * 60 + int(m)\n"
    "    a, b = minutes(start), minutes(end)\n"
    "    if b <= a:\n"
    "        return 0\n"
    "    mins = b - a\n"
    "    hours = (mins + 59) // 60\n"
    "    raw = 3 + 2 * (hours - 1)\n"
    "    return min(raw, 18)\n",
    "def stay_charge(start, end):\n"
    "    def minutes(hhmm):\n"
    "        h, m = hhmm.split(':')\n"
    "        return int(h) * 60 + int(m)\n"
    "    def charge(mins):\n"
    "        if mins <= 0:\n"
    "            return 0\n"
    "        hours = (mins + 59) // 60\n"
    "        return min(18, 3 + 2 * (hours - 1))\n"
    "    a, b = minutes(start), minutes(end)\n"
    "    if a == b:\n"
    "        return 0\n"
    "    if b > a:\n"
    "        return charge(b - a)\n"
    "    return charge(24 * 60 - a) + charge(b)\n",
    "import unittest\nfrom mod import stay_charge\n"
    "class T(unittest.TestCase):\n"
    "    def test_night(self):\n"
    "        self.assertEqual(stay_charge('22:00', '03:30'), 14)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    "import unittest\nfrom mod import stay_charge\n"
    "class T(unittest.TestCase):\n"
    "    def test_more(self):\n"
    "        self.assertEqual(stay_charge('10:10', '18:40'), 18)\n"
    "        self.assertEqual(stay_charge('10:00', '10:00'), 0)\n"
    "        self.assertEqual(stay_charge('23:30', '00:30'), 6)\n"
    "        self.assertEqual(stay_charge('10:00', '10:01'), 3)\n"
    "if __name__ == '__main__':\n    unittest.main()\n",
    False,
)


def run_py(workdir: Path, script: str) -> tuple[bool, str]:
    path = workdir / "_run_test.py"
    path.write_text(script)
    try:
        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=workdir,
            text=True,
            capture_output=True,
            timeout=8,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout"
    text = (proc.stdout + "\n" + proc.stderr).strip()
    ok = proc.returncode == 0
    if len(text) > 2500:
        text = text[-2500:]
    return ok, text or ("pass" if ok else "fail")


def materialize(task, src, root: Path) -> Path:
    wd = root / task["id"]
    if wd.exists():
        shutil.rmtree(wd)
    wd.mkdir(parents=True)
    (wd / "mod.py").write_text(src)
    (wd / "SPEC.txt").write_text(task["spec"] + "\n")
    (wd / "test_public.py").write_text(task["public"])
    return wd


def safe(wd: Path, rel: str) -> Path | None:
    try:
        path = (wd / rel).resolve()
    except Exception:
        return None
    if wd.resolve() not in path.parents and path != wd.resolve():
        return None
    return path


def dispatch(wd: Path, name: str, args: dict) -> str:
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return "arguments were not json"
    args = args or {}
    if name == "run_tests":
        ok, text = run_py(wd, (wd / "test_public.py").read_text())
        return ("PASS\n" if ok else "FAIL\n") + text
    if name == "read_file":
        path = safe(wd, str(args.get("path", "")))
        if path is None or not path.is_file():
            return "no such file"
        if path.name.startswith("test_hidden"):
            return "no such file"
        return path.read_text()[:8000]
    if name == "write_file":
        rel = str(args.get("path", "mod.py"))
        if Path(rel).name.startswith("test"):
            return "refusing to write tests"
        path = safe(wd, rel)
        if path is None:
            return "bad path"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(args.get("content", "")))
        return f"wrote {path.name} ({path.stat().st_size} bytes)"
    return "unknown tool " + name


def chat(messages):
    body = {
        "model": MODEL,
        "stream": False,
        "think": False,
        "keep_alive": "20m",
        "options": {"temperature": 0, "num_predict": 1800},
        "messages": messages,
        "tools": TOOLS,
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
    return msg, round(time.perf_counter() - t0, 2), data.get("eval_count"), data.get("done_reason")


def grade(task, src) -> dict:
    root = Path(tempfile.mkdtemp(prefix="grade-"))
    try:
        wd = materialize(task, src, root)
        pub, pub_text = run_py(wd, task["public"])
        hid, hid_text = run_py(wd, task["hidden"])
        return {"public": pub, "hidden": hid, "hidden_tail": hid_text[-400:]}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def one(task) -> dict:
    root = Path(tempfile.mkdtemp(prefix="repair-"))
    wd = materialize(task, task["buggy"], root)
    user = (
        "Fix mod.py so it matches SPEC.txt. "
        "Use read_file, write_file, and run_tests. "
        "Public tests are test_public.py. "
        "Do not stop while run_tests still fails.\n\n"
        + task["spec"]
    )
    messages = [
        {"role": "system", "content": "You repair Python in this project. Call tools. Do not write the tests."},
        {"role": "user", "content": user},
    ]
    turns = []
    t0 = time.perf_counter()
    try:
        for n in range(1, MAX_TURNS + 1):
            msg, seconds, evals, reason = chat(messages)
            calls = msg.get("tool_calls") or []
            # keep only fields the next request should echo
            assistant = {"role": "assistant", "content": msg.get("content") or ""}
            if calls:
                assistant["tool_calls"] = calls
            messages.append(assistant)
            turn = {"n": n, "seconds": seconds, "eval": evals, "reason": reason, "tools": [], "content": (msg.get("content") or "")[:200]}
            if not calls:
                turns.append(turn)
                break
            for call in calls:
                fn = call.get("function") or call
                name = fn.get("name")
                args = fn.get("arguments") or {}
                result = dispatch(wd, name, args)
                turn["tools"].append(name)
                messages.append({"role": "tool", "content": result[:4000], "tool_name": name})
            turns.append(turn)
            print(f"  turn {n} tools={turn['tools']} {seconds}s", flush=True)
        src = (wd / "mod.py").read_text()
        scored = grade(task, src)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return {
        "id": task["id"],
        "turns": len(turns),
        "seconds": round(time.perf_counter() - t0, 2),
        "public": scored["public"],
        "hidden": scored["hidden"],
        "hidden_tail": scored["hidden_tail"],
        "trace": turns,
        "public_was_green": task["public_passes_on_bug"],
    }


def check() -> int:
    fails = 0
    for task in TASKS:
        bug = grade(task, task["buggy"])
        gold = grade(task, task["gold"])
        ok = gold["public"] and gold["hidden"] and (not bug["hidden"])
        ok = ok and (bug["public"] == task["public_passes_on_bug"])
        print(("ok" if ok else "FAIL"), task["id"], "bug_public", bug["public"], "bug_hidden", bug["hidden"], "gold", gold["public"], gold["hidden"])
        if not ok:
            fails += 1
            print(bug["hidden_tail"][:300])
    print("fails", fails, "tasks", len(TASKS))
    return fails


def main():
    global HOST, MODEL
    if "--check" in sys.argv:
        sys.exit(1 if check() else 0)
    HOST = sys.argv[1]
    MODEL = sys.argv[2]
    rows = []
    for task in TASKS:
        print("==", task["id"], flush=True)
        try:
            row = one(task)
        except Exception as exc:
            row = {"id": task["id"], "error": str(exc)[:400], "hidden": False}
        rows.append(row)
        print(task["id"], "hidden" if row.get("hidden") else "MISS", "turns", row.get("turns"), "s", row.get("seconds"), flush=True)
    passed = sum(1 for r in rows if r.get("hidden"))
    safe = MODEL.replace(":", "-").replace("/", "-")
    path = Path(__file__).resolve().parent / "results" / f"results-{safe}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"model": MODEL, "passed": passed, "n": len(rows), "rows": rows}, indent=2))
    print("WROTE", path, "PASSED", passed, "/", len(rows))


if __name__ == "__main__":
    main()
