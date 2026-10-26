#!/usr/bin/env python3
"""Run ladder v2 against an Ollama model, or check the ladder against itself.

    python3 ladder/run.py http://host:11434 model:tag            # full run
    python3 ladder/run.py --check                                 # self-check, no model
    python3 ladder/run.py --mock gold                             # drive the loop with a fake model

Protocol: think off, temperature 0, seed 0, no num_ctx unless --num-ctx is given.
Score is the hidden test file. Each rung reports every hidden case by name.
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import harness  # noqa: E402
import rungs as rung_defs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LADDER_VERSION = "2026-10-26c"
SCHEMA = 2

SYSTEM = (
    "You are repairing a small Python project. Work only through the tools. "
    "Read SPEC.txt first, then the source. Do not write or edit tests; tests are not the "
    "whole specification. When the code matches the spec and the public tests pass, apart "
    "from any public assertion the task note says is wrong, reply with one line that says "
    "what you changed and make no further tool call."
)


def user_prompt(rung: dict, total: int) -> str:
    names = ", ".join(rung["files_buggy"])
    text = (
        f"Rung {rung['level']} of {total}: {rung['title']}. "
        f"Source files: {names}. Tools: {', '.join(harness.TOOL_NAMES)}. "
        "Public tests are in test_public.py. "
    )
    if rung["gold_passes_public"]:
        text += ("Do not stop while run_tests still fails, and remember that a green public run "
                 "can still leave the spec wrong.")
    else:
        text += ("Do not stop while run_tests still fails, except for the assertion the note "
                 "below says is wrong.")
    if rung["note"]:
        text += "\n\n" + rung["note"]
    text += "\n\nSPEC:\n" + rung["spec"]
    return text


# ----------------------------------------------------------------------------- clients

class MalformedToolCall(Exception):
    """The model produced a tool call the server could not parse. Ollama 0.40 reports
    this as HTTP 500 with "invalid tool call arguments" instead of returning the
    message, so the harness turns it into a bad tool call and lets the model retry."""


class OllamaClient:
    def __init__(self, host: str, model: str, num_predict: int, timeout: float,
                 keep_alive: str, think: bool, num_ctx: int | None, seed: int):
        self.host = host.rstrip("/")
        self.model = model
        self.num_predict = num_predict
        self.timeout = timeout
        self.keep_alive = keep_alive
        self.think = think
        self.num_ctx = num_ctx
        self.seed = seed

    def _get(self, path: str):
        try:
            with urllib.request.urlopen(self.host + path, timeout=15) as resp:
                return json.load(resp)
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)[:200]}

    def _post(self, path: str, body: dict, timeout: float):
        req = urllib.request.Request(
            self.host + path,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)

    def chat(self, messages: list) -> tuple[dict, dict]:
        """One model call. A server-side failure (HTTP 5xx, connection reset) is retried
        twice with a short pause, so one hiccup does not decide a rung."""
        last = None
        for attempt in range(3):
            try:
                return self._chat_once(messages)
            except urllib.error.HTTPError as exc:
                body = ""
                try:
                    body = exc.read().decode(errors="replace")
                except Exception:  # noqa: BLE001
                    pass
                if "invalid tool call" in body:
                    raise MalformedToolCall(body[:300]) from None
                if exc.code < 500:
                    raise
                last = exc
            except (urllib.error.URLError, ConnectionError, TimeoutError) as exc:
                last = exc
            print(f"  retry {attempt + 1} after {type(last).__name__}: {str(last)[:80]}", flush=True)
            time.sleep(5 * (attempt + 1))
        raise last

    def _chat_once(self, messages: list) -> tuple[dict, dict]:
        options = {"temperature": 0, "seed": self.seed, "num_predict": self.num_predict}
        if self.num_ctx:
            options["num_ctx"] = self.num_ctx
        body = {
            "model": self.model,
            "messages": messages,
            "tools": harness.TOOLS,
            "stream": False,
            "think": self.think,
            "keep_alive": self.keep_alive,
            "options": options,
        }
        t0 = time.perf_counter()
        data = self._post("/api/chat", body, self.timeout)
        wall = time.perf_counter() - t0
        msg = data.get("message") or {}
        meta = {
            "wall": round(wall, 2),
            "thinking_chars": len(msg.get("thinking") or ""),
            "content_chars": len(msg.get("content") or ""),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "eval_count": data.get("eval_count"),
            "eval_duration": data.get("eval_duration"),
            "done_reason": data.get("done_reason"),
        }
        return msg, meta

    def seat(self) -> dict:
        """Everything that defines the seat: server, model digest, and how it is loaded."""
        version = self._get("/api/version").get("version")
        tags = self._get("/api/tags")
        digest = size = details = None
        for m in tags.get("models") or []:
            if m.get("name") == self.model:
                digest, size, details = m.get("digest"), m.get("size"), m.get("details")
        ps = self._get("/api/ps")
        loaded = None
        for m in ps.get("models") or []:
            if m.get("name") == self.model:
                total, vram = m.get("size") or 0, m.get("size_vram") or 0
                loaded = {
                    "size": total,
                    "size_vram": vram,
                    "gpu_percent": round(100.0 * vram / total, 1) if total else None,
                    "context_length": m.get("context_length"),
                    "runner": m.get("runner"),
                }
        return {
            "host": self.host, "model": self.model, "ollama_version": version,
            "digest": digest, "size": size, "details": details, "loaded": loaded,
            "think": self.think, "num_ctx": self.num_ctx, "num_predict": self.num_predict,
            "seed": self.seed, "temperature": 0,
        }


class MockClient:
    """A scripted model used to prove the loop, tools, grading, and reports end to end.

    gold:  reads the spec, writes the gold files, runs the tests, stops.
    lazy:  stops at once without touching anything.
    trap:  writes the first trap, runs the tests, stops.
    cheat: tries to rewrite test_public.py, then writes gold, then stops.
    loop:  runs the tests forever and never stops.
    """

    def __init__(self, kind: str, rung: dict | None = None):
        self.kind = kind
        self.rung = rung
        self.turn = 0
        self.model = f"mock-{kind}"

    def bind(self, rung: dict):
        self.rung = rung
        self.turn = 0

    def _calls(self, *items):
        return [{"function": {"name": n, "arguments": a}} for n, a in items]

    def chat(self, messages: list) -> tuple[dict, dict]:
        self.turn += 1
        r = self.rung
        meta = {"wall": 0.0, "prompt_eval_count": 0, "eval_count": 0, "eval_duration": 0, "done_reason": "stop"}
        k, t = self.kind, self.turn
        if k == "lazy":
            return {"role": "assistant", "content": "Looks fine to me."}, meta
        if k == "loop":
            return {"role": "assistant", "content": "", "tool_calls": self._calls(("run_tests", {}))}, meta
        if t == 1:
            return {"role": "assistant", "content": "",
                    "tool_calls": self._calls(("list_files", {}), ("read_file", {"path": "SPEC.txt"}))}, meta
        if k == "cheat" and t == 2:
            return {"role": "assistant", "content": "",
                    "tool_calls": self._calls(("write_file", {"path": "test_public.py", "content": "# nothing\n"}))}, meta
        write_turn = 3 if k == "cheat" else 2
        if t == write_turn:
            files = r["files_gold"] if k in ("gold", "cheat") else next(iter(r["traps"].values()))
            calls = [("write_file", {"path": n, "content": c}) for n, c in files.items()]
            return {"role": "assistant", "content": "", "tool_calls": self._calls(*calls)}, meta
        if t == write_turn + 1:
            return {"role": "assistant", "content": "",
                    "tool_calls": self._calls(("run_tests", {}), ("run_python", {"code": "import mod; print('ok')"}))}, meta
        return {"role": "assistant", "content": "Rewrote the source to follow the spec."}, meta

    def seat(self) -> dict:
        return {"host": "mock", "model": self.model}


# ----------------------------------------------------------------------------- loop

def run_rung(client, rung: dict, total: int, max_turns: int | None, transcript_dir: Path | None) -> dict:
    root = Path(tempfile.mkdtemp(prefix="ladder-run-"))
    ws = harness.Workspace(rung, root)
    if isinstance(client, MockClient):
        client.bind(rung)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_prompt(rung, total)},
    ]
    budget = max_turns or rung["max_turns"]
    turns = []
    stop_reason = "turns"
    error = None
    t0 = time.perf_counter()
    try:
        for n in range(1, budget + 1):
            try:
                msg, meta = client.chat(messages)
            except MalformedToolCall as exc:
                ws.events["bad_tool_calls"] += 1
                ws.events["malformed_tool_calls"] = ws.events.get("malformed_tool_calls", 0) + 1
                messages.append({"role": "user", "content": (
                    "Your previous reply held a tool call whose arguments were not valid JSON, "
                    "so it was dropped. Send the call again with valid JSON arguments. "
                    "Keep run_python snippets short.")})
                turns.append({"n": n, "wall": 0.0, "tools": [], "content": "", "malformed_tool_call": str(exc)[:200]})
                print(f"  turn {n} malformed tool call, nudged", flush=True)
                continue
            except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                error = f"{type(exc).__name__}: {str(exc)[:300]}"
                stop_reason = "error"
                print(f"  turn {n} ERROR {error}", flush=True)
                break
            calls = msg.get("tool_calls") or []
            assistant = {"role": "assistant", "content": msg.get("content") or ""}
            if calls:
                assistant["tool_calls"] = calls
            messages.append(assistant)
            turn = {"n": n, **meta, "tools": [], "content": (msg.get("content") or "")[:300]}
            if not calls and meta.get("done_reason") == "length":
                # The reply hit the generation cap before any tool call. That is not a
                # decision to stop, so it costs a turn and a nudge, like a malformed call.
                ws.events["length_stops"] = ws.events.get("length_stops", 0) + 1
                turn["length_stop"] = True
                turns.append(turn)
                messages.append({"role": "user", "content": (
                    "Your reply hit the length cap before any tool call, so nothing happened. "
                    "Keep prose short and make the tool call now.")})
                print(f"  turn {n} length cap, no tool call, nudged {meta['wall']}s", flush=True)
                continue
            if not calls:
                turns.append(turn)
                stop_reason = "stop"
                print(f"  turn {n} stop {meta['wall']}s", flush=True)
                break
            for call in calls:
                fn = call.get("function") or call
                name = str(fn.get("name"))
                args = fn.get("arguments") or {}
                result = ws.dispatch(name, args)
                turn["tools"].append({"name": name, "args": _short_args(args), "result": result[:200]})
                messages.append({"role": "tool", "content": result[:6000], "tool_name": name})
            turns.append(turn)
            print(f"  turn {n} {[t['name'] for t in turn['tools']]} {meta['wall']}s", flush=True)
        sources = ws.sources()
        scored = harness.grade(rung, sources)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    ev = ws.events
    hidden = scored["hidden"]
    row = {
        "id": rung["id"],
        "level": rung["level"],
        "title": rung["title"],
        "skill": rung["skill"],
        "passed": bool(hidden["ok"]),
        "hidden_passed": len(hidden["passed"]),
        "hidden_total": rung["hidden_n"],
        "baseline": len(rung["bug_passes"]),
        "hidden_failed": hidden["failed"],
        "hidden_timed_out": hidden.get("timed_out", False),
        "hidden_tail": hidden["text"][-600:],
        "public_ok": bool(scored["public"]["ok"]),
        "turns": len(turns),
        "max_turns": budget,
        "stop_reason": stop_reason,
        "error": error,
        "seconds": round(time.perf_counter() - t0, 1),
        "eval_tokens": sum((t.get("eval_count") or 0) for t in turns),
        "prompt_tokens": sum((t.get("prompt_eval_count") or 0) for t in turns),
        "tool_calls": sum(len(t["tools"]) for t in turns),
        "flags": {
            "read_spec": ev["read_spec"],
            "ran_tests": ev["test_runs"] > 0,
            "used_python": ev["python_runs"] > 0,
            "wrote_source": len(ev["writes"]) > 0,
            "writes": len(ev["writes"]),
            "test_write_attempts": ev["test_write_attempts"],
            "bad_tool_calls": ev["bad_tool_calls"],
            "malformed_tool_calls": ev.get("malformed_tool_calls", 0),
            "length_stops": ev.get("length_stops", 0),
            "no_tool_calls": all(not t.get("tools") for t in turns),
            "stopped_red": stop_reason == "stop" and not scored["public"]["ok"] and rung["gold_passes_public"],
            "ran_out_of_turns": stop_reason == "turns",
        },
        "trace": turns,
    }
    if transcript_dir is not None:
        transcript_dir.mkdir(parents=True, exist_ok=True)
        (transcript_dir / f"{rung['level']:02d}-{rung['id']}.json").write_text(
            json.dumps({"messages": messages, "final_sources": sources, "grade": scored}, indent=1))
    return row


def _short_args(args) -> dict:
    if not isinstance(args, dict):
        return {"raw": str(args)[:120]}
    return {k: (v[:120] + "..." if isinstance(v, str) and len(v) > 120 else v) for k, v in args.items()}


# ----------------------------------------------------------------------------- scoring

def score(rows: list[dict]) -> dict:
    by_level = {r["level"]: r for r in rows}
    levels = sorted(by_level)
    height = 0
    for lv in levels:
        if by_level[lv]["passed"] and lv == height + 1:
            height = lv
        else:
            break
    passed = [r for r in rows if r["passed"]]
    cases = sum(r["hidden_passed"] for r in rows)
    total_cases = sum(r["hidden_total"] for r in rows)
    baseline = sum(r["baseline"] for r in rows)
    gain_den = total_cases - baseline
    turn_list = [r["turns"] for r in passed]
    return {
        "height": height,
        "peak": max((r["level"] for r in passed), default=0),
        "passed": len(passed),
        "n": len(rows),
        "case_rate": round(cases / total_cases, 3) if total_cases else 0.0,
        "cases": cases,
        "total_cases": total_cases,
        "baseline_cases": baseline,
        "gain": round(max(0, cases - baseline) / gain_den, 3) if gain_den else 0.0,
        "median_turns_on_pass": statistics.median(turn_list) if turn_list else None,
        "eval_tokens": sum(r["eval_tokens"] for r in rows),
        "prompt_tokens": sum(r["prompt_tokens"] for r in rows),
        "seconds": round(sum(r["seconds"] for r in rows), 1),
        "errors": sum(1 for r in rows if r["error"]),
        "length_stops": sum(r["flags"].get("length_stops", 0) for r in rows),
        "stopped_red": sum(1 for r in rows if r["flags"]["stopped_red"]),
        "test_write_attempts": sum(r["flags"]["test_write_attempts"] for r in rows),
        "ran_out_of_turns": sum(1 for r in rows if r["flags"]["ran_out_of_turns"]),
    }


def summary_line(s: dict) -> str:
    return (f"LADDER height {s['height']}/{s['n']} peak {s['peak']} passed {s['passed']}/{s['n']} "
            f"cases {s['cases']}/{s['total_cases']} gain {s['gain']:.0%} above the {s['baseline_cases']}-case floor "
            f"tokens {s['eval_tokens']} secs {s['seconds']}")


# ----------------------------------------------------------------------------- check

def check_examples(rung: dict) -> list[str]:
    """Evaluate every spec example against the gold files. Returns a list of failures."""
    root = Path(tempfile.mkdtemp(prefix="ladder-ex-"))
    try:
        wd = harness.materialize(rung, rung["files_gold"], root)
        modules = [Path(n).stem for n in rung["files_gold"] if n.endswith(".py")]
        script = [
            "import json, traceback",
            rung["prelude"] or "",
            *[f"from {m} import *" for m in modules],
            f"examples = {json.dumps(rung['examples'])}",
            "bad = []",
            "for ex in examples:",
            "    if 'text' in ex: continue",
            "    ns = dict(globals())",
            "    try:",
            "        if ex.get('setup'): exec(ex['setup'], ns)",
            "        if 'raises' in ex:",
            "            try:",
            "                eval(ex['call'], ns)",
            "                bad.append(ex['call'] + ' did not raise')",
            "            except Exception as exc:",
            "                if type(exc).__name__ != ex['raises']:",
            "                    bad.append(ex['call'] + ' raised ' + type(exc).__name__)",
            "        else:",
            "            got = eval(ex['call'], ns)",
            "            want = eval(ex['expect'], ns)",
            "            if got != want or type(got) != type(want):",
            "                bad.append(f\"{ex['call']} gave {got!r} not {want!r}\")",
            "    except Exception:",
            "        bad.append(ex['call'] + ' crashed: ' + traceback.format_exc().splitlines()[-1])",
            "print('@@EX ' + json.dumps(bad))",
        ]
        (wd / "_ladder_examples.py").write_text("\n".join(script))
        proc = subprocess.run([sys.executable, "_ladder_examples.py"], cwd=wd, text=True,
                              capture_output=True, timeout=rung["test_timeout"])
        for line in proc.stdout.splitlines():
            if line.startswith("@@EX "):
                return json.loads(line[5:])
        return ["example runner crashed: " + (proc.stderr or proc.stdout)[-300:]]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def check(selected: list[dict]) -> int:
    fails = 0
    t_all = time.perf_counter()
    for r in selected:
        t0 = time.perf_counter()
        problems = []
        gold = harness.grade(r, r["files_gold"])
        bug = harness.grade(r, r["files_buggy"])
        if not gold["hidden"]["ok"]:
            problems.append(f"gold fails hidden: {gold['hidden']['failed']} {gold['hidden']['text'][-200:]}")
        if gold["public"]["ok"] != r["gold_passes_public"]:
            problems.append(f"gold public={gold['public']['ok']} expected {r['gold_passes_public']}")
        if bug["hidden"]["ok"]:
            problems.append("bug passes hidden")
        if bug["public"]["ok"] != r["public_passes_on_bug"]:
            problems.append(f"bug public={bug['public']['ok']} expected {r['public_passes_on_bug']}")
        if sorted(bug["hidden"]["passed"]) != sorted(r["bug_passes"]):
            problems.append(f"bug passes {sorted(bug['hidden']['passed'])}, declared {sorted(r['bug_passes'])}")
        if gold["hidden"]["ran"] != r["hidden_n"]:
            problems.append(f"hidden ran {gold['hidden']['ran']} tests, counted {r['hidden_n']}")
        if len(r["traps"]) < 2:
            problems.append("fewer than two traps")
        trap_notes = []
        for name, files in r["traps"].items():
            tr = harness.grade(r, files)
            if tr["hidden"]["ok"]:
                problems.append(f"trap {name} passes hidden")
            else:
                why = "timeout" if tr["hidden"].get("timed_out") else ",".join(tr["hidden"]["failed"])
                trap_notes.append(f"{name}->{why}")
        ex_bad = check_examples(r)
        problems.extend("example: " + e for e in ex_bad)
        status = "ok" if not problems else "FAIL"
        fails += bool(problems)
        print(f"{status:4} L{r['level']:<2} {r['id']:<10} hidden {r['hidden_n']} cases, "
              f"bug_public={bug['public']['ok']} traps[{' '.join(trap_notes)}] {time.perf_counter() - t0:.1f}s")
        for p in problems:
            print("     -", p)
    print(f"fails {fails} of {len(selected)} rungs, hash {rung_defs.ladder_hash()}, {time.perf_counter() - t_all:.1f}s")
    return fails


# ----------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="Run ladder v2 against an Ollama model")
    ap.add_argument("host", nargs="?", help="Ollama base URL, for example http://127.0.0.1:11434")
    ap.add_argument("model", nargs="?", help="Model tag, for example ornith-1.5:9b")
    ap.add_argument("--check", action="store_true", help="Validate rungs, golds, traps, and examples. No model.")
    ap.add_argument("--mock", choices=["gold", "lazy", "trap", "cheat", "loop"], help="Drive the loop with a scripted model")
    ap.add_argument("--rungs", default="", help="Comma list of rung ids or levels, default all")
    ap.add_argument("--repeats", type=int, default=1, help="Run the whole ladder this many times")
    ap.add_argument("--max-turns", type=int, default=None, help="Override every rung's turn budget")
    ap.add_argument("--num-predict", type=int, default=3000)
    ap.add_argument("--num-ctx", type=int, default=None, help="Set num_ctx. Default leaves the server window as the seat")
    ap.add_argument("--timeout", type=float, default=600.0, help="Seconds per model call")
    ap.add_argument("--keep-alive", default="20m")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--think", action="store_true", help="Turn thinking on (off is the protocol)")
    ap.add_argument("--tag", default="", help="Extra label for the result file name")
    ap.add_argument("--no-transcripts", action="store_true")
    args = ap.parse_args()

    selected = rung_defs.by_id(args.rungs.split(",")) if args.rungs else list(rung_defs.RUNGS)
    if not selected:
        print("no rungs matched", file=sys.stderr)
        return 2
    if args.check:
        return 1 if check(selected) else 0
    if args.mock:
        client = MockClient(args.mock)
    else:
        if not (args.host and args.model):
            ap.error("host and model are required unless --check or --mock is given")
        client = OllamaClient(args.host, args.model, args.num_predict, args.timeout,
                              args.keep_alive, args.think, args.num_ctx, args.seed)
    total = len(rung_defs.RUNGS)
    safe = client.model.replace(":", "-").replace("/", "-") + (f"-{args.tag}" if args.tag else "")
    out_dir = ROOT / "results" / "ladder"
    out_dir.mkdir(parents=True, exist_ok=True)
    transcripts = None if args.no_transcripts else out_dir / safe
    seat_before = client.seat()
    runs = []
    for rep in range(1, args.repeats + 1):
        rows = []
        if args.repeats > 1:
            print(f"#### repeat {rep}/{args.repeats}", flush=True)
        for r in selected:
            print(f"== L{r['level']} {r['id']} ({r['skill']})", flush=True)
            tdir = transcripts / (f"rep{rep}" if args.repeats > 1 else "") if transcripts else None
            row = run_rung(client, r, total, args.max_turns, tdir)
            rows.append(row)
            print(f"{r['id']} {'PASS' if row['passed'] else 'MISS'} "
                  f"cases {row['hidden_passed']}/{row['hidden_total']} turns {row['turns']} "
                  f"stop={row['stop_reason']} {row['seconds']}s tokens {row['eval_tokens']}", flush=True)
        s = score(rows)
        print(summary_line(s), flush=True)
        runs.append({"repeat": rep, "score": s, "rows": rows})
    seat_after = client.seat()
    report = {
        "schema": SCHEMA,
        "ladder_version": LADDER_VERSION,
        "ladder_hash": rung_defs.ladder_hash(),
        "model": client.model,
        "host": getattr(client, "host", "mock"),
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "seat_before": seat_before,
        "seat_after": seat_after,
        "protocol": {"temperature": 0, "seed": args.seed, "think": args.think, "num_predict": args.num_predict,
                     "num_ctx": args.num_ctx, "max_turns_override": args.max_turns, "keep_alive": args.keep_alive},
        "rungs": [r["id"] for r in selected],
        "score": runs[0]["score"] if len(runs) == 1 else aggregate([x["score"] for x in runs]),
        "runs": runs,
    }
    path = out_dir / f"{safe}.json"
    path.write_text(json.dumps(report, indent=1))
    print("WROTE", path)
    loaded = (seat_after or {}).get("loaded")
    if loaded and loaded.get("gpu_percent") is not None and loaded["gpu_percent"] < 100:
        print(f"SEAT WARNING: model ran at {loaded['gpu_percent']}% GPU. That is a different seat.")
    return 0


def aggregate(scores: list[dict]) -> dict:
    """Median of each numeric field across repeats, plus the spread of height."""
    out = {}
    for key in scores[0]:
        vals = [s[key] for s in scores if isinstance(s[key], (int, float))]
        if len(vals) == len(scores):
            out[key] = statistics.median(vals)
    out["repeats"] = len(scores)
    out["height_min"] = min(s["height"] for s in scores)
    out["height_max"] = max(s["height"] for s in scores)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
