"""Sandbox, tools, and grading for the v2 ladder.

Everything a rung run touches lives in a throwaway directory. The model works
through five tools. Tests run in a subprocess with a timeout and report every
test case by name so a rung can earn partial credit.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List the files in the project.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read one project file. SPEC.txt holds the specification.",
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
            "description": "Replace the whole content of a project source file. Tests cannot be written.",
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
            "description": "Run the public tests in test_public.py. Returns PASS or the failure text.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Run a short Python snippet inside the project directory and return its output. "
                           "Use it to try the code against the spec.",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
            },
        },
    },
]

TOOL_NAMES = [t["function"]["name"] for t in TOOLS]

# The runner imports a test file by path and prints one JSON line naming every
# test that passed or failed. It is written into the workdir for each run and
# removed afterwards.
RUNNER = r'''
import importlib.util, json, sys, unittest
path = sys.argv[1]
spec = importlib.util.spec_from_file_location("_ladder_test", path)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except BaseException as exc:
    print("@@RESULT " + json.dumps({"ran": 0, "passed": [], "failed": [], "import_error": repr(exc)[:400]}))
    sys.exit(1)
only = sys.argv[2] if len(sys.argv) > 2 else None
loaded = unittest.defaultTestLoader.loadTestsFromModule(mod)
names = []
picked = []
def walk(s):
    for t in s:
        if isinstance(t, unittest.TestSuite):
            walk(t)
        else:
            name = t.id().rsplit(".", 1)[-1]
            if only is None or name == only:
                names.append(name)
                picked.append(t)
walk(loaded)
suite = unittest.TestSuite(picked)
res = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(suite)
bad = [t.id().rsplit(".", 1)[-1] for t, _ in res.failures + res.errors]
print("@@RESULT " + json.dumps({"ran": res.testsRun, "passed": [n for n in names if n not in bad], "failed": bad}))
sys.exit(0 if res.wasSuccessful() else 1)
'''


def run_tests(workdir: Path, test_src: str, timeout: float = 10.0, per_case: bool = True) -> dict:
    """Run one unittest file against the project in workdir. Returns a report dict.

    A whole-file timeout hides which cases would have passed, so after one the
    cases are re-run one at a time, each with its own timeout.
    """
    report = _run_file(workdir, test_src, timeout, None)
    if not report.get("timed_out") or not per_case:
        return report
    names = re.findall(r"def (test_\w+)", test_src)
    passed, failed, slow = [], [], []
    for name in names:
        one = _run_file(workdir, test_src, timeout, name)
        if one["ok"]:
            passed.append(name)
        else:
            failed.append(name)
            if one.get("timed_out"):
                slow.append(name)
    return {"ok": False, "ran": len(names), "passed": passed, "failed": failed, "timed_out": True,
            "text": f"timeout after {timeout}s in " + ", ".join(slow)}


def _run_file(workdir: Path, test_src: str, timeout: float, only: str | None) -> dict:
    runner = workdir / "_ladder_runner.py"
    test_path = workdir / "_ladder_test.py"
    runner.write_text(RUNNER)
    test_path.write_text(test_src)
    cmd = [sys.executable, str(runner), str(test_path)] + ([only] if only else [])
    try:
        proc = subprocess.run(cmd, cwd=workdir, text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        names = [only] if only else re.findall(r"def (test_\w+)", test_src)
        return {"ok": False, "ran": 0, "passed": [], "failed": names, "timed_out": True,
                "text": f"timeout after {timeout}s"}
    finally:
        for p in (runner, test_path):
            try:
                p.unlink()
            except OSError:
                pass
    text = (proc.stdout + "\n" + proc.stderr).strip()
    report = {"ok": proc.returncode == 0, "ran": 0, "passed": [], "failed": [], "timed_out": False}
    for line in proc.stdout.splitlines():
        if line.startswith("@@RESULT "):
            try:
                report.update(json.loads(line[len("@@RESULT "):]))
            except json.JSONDecodeError:
                pass
    # Strip the marker from what the model sees.
    shown = "\n".join(ln for ln in text.splitlines() if not ln.startswith("@@RESULT "))
    if len(shown) > 2500:
        shown = shown[-2500:]
    report["text"] = shown or ("pass" if report["ok"] else "fail")
    return report


def materialize(rung: dict, files: dict, root: Path) -> Path:
    wd = root / rung["id"]
    if wd.exists():
        shutil.rmtree(wd)
    wd.mkdir(parents=True)
    for name, src in files.items():
        path = wd / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(src)
    (wd / "SPEC.txt").write_text(rung["spec"] + "\n")
    (wd / "test_public.py").write_text(rung["public"])
    return wd


def grade(rung: dict, files: dict) -> dict:
    """Grade a set of source files in a fresh directory. Never touches the model's workdir."""
    root = Path(tempfile.mkdtemp(prefix="ladder-grade-"))
    try:
        wd = materialize(rung, files, root)
        pub = run_tests(wd, rung["public"], rung.get("test_timeout", 10.0))
        hid = run_tests(wd, rung["hidden"], rung.get("test_timeout", 10.0))
        return {"public": pub, "hidden": hid}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def safe_path(wd: Path, rel: str) -> Path | None:
    try:
        path = (wd / rel).resolve()
    except Exception:
        return None
    base = wd.resolve()
    if path != base and base not in path.parents:
        return None
    return path


def is_test_path(rel: str) -> bool:
    name = Path(rel).name
    return name.startswith("test") or name.startswith("_ladder")


class Workspace:
    """One rung's working directory plus the counters the behaviour flags need."""

    def __init__(self, rung: dict, root: Path):
        self.rung = rung
        self.dir = materialize(rung, rung["files_buggy"], root)
        self.source_names = list(rung["files_buggy"])
        self.events = {
            "reads": [], "writes": [], "test_runs": 0, "python_runs": 0,
            "test_write_attempts": 0, "bad_tool_calls": 0, "last_public_ok": None,
            "read_spec": False,
        }

    def dispatch(self, name: str, args) -> str:
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                self.events["bad_tool_calls"] += 1
                return "error: arguments were not valid JSON"
        args = args or {}
        if not isinstance(args, dict):
            self.events["bad_tool_calls"] += 1
            return "error: arguments must be an object"
        if name == "list_files":
            names = sorted(p.name for p in self.dir.iterdir() if p.is_file() and not p.name.startswith("_ladder"))
            return "\n".join(names)
        if name == "read_file":
            rel = str(args.get("path", ""))
            path = safe_path(self.dir, rel)
            if path is None or not path.is_file() or path.name.startswith("_ladder"):
                self.events["bad_tool_calls"] += 1
                return f"error: no such file: {rel}"
            self.events["reads"].append(path.name)
            if path.name == "SPEC.txt":
                self.events["read_spec"] = True
            return path.read_text()[:12000]
        if name == "write_file":
            rel = str(args.get("path", ""))
            if not rel:
                self.events["bad_tool_calls"] += 1
                return "error: path is required"
            if is_test_path(rel) or Path(rel).name == "SPEC.txt":
                self.events["test_write_attempts"] += 1
                return "refused: tests and the spec cannot be written"
            path = safe_path(self.dir, rel)
            if path is None:
                self.events["bad_tool_calls"] += 1
                return "error: bad path"
            content = args.get("content")
            if not isinstance(content, str):
                self.events["bad_tool_calls"] += 1
                return "error: content must be a string"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            self.events["writes"].append(path.name)
            return f"wrote {path.name} ({len(content.encode())} bytes)"
        if name == "run_tests":
            self.events["test_runs"] += 1
            report = run_tests(self.dir, self.rung["public"], self.rung.get("test_timeout", 10.0))
            self.events["last_public_ok"] = report["ok"]
            return ("PASS\n" if report["ok"] else "FAIL\n") + report["text"]
        if name == "run_python":
            code = args.get("code")
            if not isinstance(code, str):
                self.events["bad_tool_calls"] += 1
                return "error: code must be a string"
            self.events["python_runs"] += 1
            return run_snippet(self.dir, code)
        self.events["bad_tool_calls"] += 1
        return f"error: unknown tool {name}. Tools: {', '.join(TOOL_NAMES)}"

    def sources(self) -> dict:
        out = {}
        for name in self.source_names:
            path = self.dir / name
            out[name] = path.read_text() if path.is_file() else ""
        return out


def run_snippet(wd: Path, code: str, timeout: float = 6.0) -> str:
    path = wd / "_ladder_snippet.py"
    path.write_text(code)
    try:
        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=wd,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"timeout after {timeout}s"
    finally:
        try:
            path.unlink()
        except OSError:
            pass
    text = (proc.stdout + ("\n" + proc.stderr if proc.stderr else "")).strip()
    if len(text) > 3000:
        text = text[-3000:]
    return text or f"(no output, exit {proc.returncode})"
