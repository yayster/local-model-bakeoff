#!/usr/bin/env python3
"""Repeat the 2026-10-25 local-model bake-off against an Ollama /api/chat.

Protocol: think off, temperature 0, no num_ctx (the server window is the seat).
Score is the last non-empty line, compared with spaces and backticks removed.
A ceiling item that stops for length is retried once at 6000 tokens.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUIZ = json.loads((ROOT / "tasks" / "quiz.json").read_text())
CEILING = json.loads((ROOT / "tasks" / "ceiling.json").read_text())

DATE_DIFF = {
    "type": "function",
    "function": {
        "name": "date_diff",
        "description": "Number of days from start to end",
        "parameters": {
            "type": "object",
            "properties": {
                "start": {"type": "string"},
                "end": {"type": "string"},
            },
            "required": ["start", "end"],
        },
    },
}

CODE_CASES = [
    ([5, 1, 5], 1),
    ([3, 3, 3], None),
    ([1, 2], 1),
    ([4], None),
    ([9, 9, 8, 7], 8),
]


def chat(host: str, model: str, messages: list, num_predict: int, tools=None) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "keep_alive": "10m",
        "options": {"temperature": 0, "num_predict": num_predict},
    }
    if tools is not None:
        payload["tools"] = tools
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        host.rstrip("/") + "/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=400) as resp:
        body = json.loads(resp.read())
    body["_wall"] = time.perf_counter() - t0
    return body


def last_line(text: str) -> str:
    lines = [ln.strip() for ln in (text or "").strip().splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def norm(value: str) -> str:
    return re.sub(r"[`\s$]", "", value or "").lower()


def content_of(body: dict) -> str:
    return ((body.get("message") or {}).get("content")) or ""


def tok_s(body: dict) -> float:
    ev = body.get("eval_count") or 0
    ed = body.get("eval_duration") or 0
    return (ev / (ed / 1e9)) if ed else 0.0


def grade_code(src: str) -> bool:
    blocks = re.findall(r"```(?:python)?\n(.*?)```", src, re.S)
    body = blocks[-1] if blocks else src
    ns: dict = {}
    try:
        exec(body, ns)
        fn = ns.get("second_largest")
        if not fn:
            return False
        return all(fn(inp) == exp for inp, exp in CODE_CASES)
    except Exception:
        return False


def run_speed(host: str, model: str) -> dict:
    rates = []
    rows = []
    prompt = "Count from 1 to 80, one number per line, nothing else."
    for i in range(3):
        body = chat(host, model, [{"role": "user", "content": prompt}], 128)
        rate = tok_s(body)
        rates.append(rate)
        rows.append({"run": i + 1, "tok_s": round(rate, 1), "wall": round(body["_wall"], 1),
                     "eval": body.get("eval_count"), "done": body.get("done_reason")})
        print(f"speed{i + 1} {rate:.1f} tok/s", flush=True)
    median = sorted(rates)[1]
    print(f"SPEED_MEDIAN {median:.1f}", flush=True)
    return {"median_tok_s": round(median, 1), "runs": rows}


def run_quiz(host: str, model: str) -> dict:
    rows = []
    ok_n = 0
    for item in QUIZ["prose"]:
        body = chat(host, model, [{"role": "user", "content": item["prompt"]}], 700)
        got = last_line(content_of(body))
        ok = norm(got) == norm(item["answer"])
        ok_n += int(ok)
        rows.append({"id": item["id"], "ok": ok, "last": got, "gold": item["answer"],
                     "wall": round(body["_wall"], 1), "done": body.get("done_reason")})
        print(f"quiz {item['id']} {'OK' if ok else 'MISS'} last={got!r}", flush=True)
    tool = QUIZ["tool"]
    body = chat(host, model, [{"role": "user", "content": tool["prompt"]}], 400, tools=[DATE_DIFF])
    calls = (body.get("message") or {}).get("tool_calls") or []
    ok = False
    detail = content_of(body)[:200]
    if calls:
        fn = calls[0].get("function") or {}
        args = fn.get("arguments") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        want = tool["arguments"]
        ok = fn.get("name") == tool["name"] and str(args.get("start")) == want["start"] and str(args.get("end")) == want["end"]
        detail = {"name": fn.get("name"), "arguments": args}
    ok_n += int(ok)
    rows.append({"id": "tool", "ok": ok, "detail": detail, "wall": round(body["_wall"], 1)})
    print(f"quiz tool {'OK' if ok else 'MISS'} {detail}", flush=True)
    code = QUIZ["code"]
    body = chat(host, model, [{"role": "user", "content": code["prompt"]}], 800)
    ok = grade_code(content_of(body))
    ok_n += int(ok)
    rows.append({"id": "code", "ok": ok, "wall": round(body["_wall"], 1)})
    print(f"quiz code {'OK' if ok else 'MISS'}", flush=True)
    print(f"QUIZ {ok_n}/10", flush=True)
    return {"score": ok_n, "n": 10, "rows": rows}


def run_ceiling(host: str, model: str) -> dict:
    rows = []
    ok_n = 0
    for item in CEILING:
        body = chat(host, model, [{"role": "user", "content": item["prompt"]}], 2500)
        if body.get("done_reason") == "length":
            body = chat(host, model, [{"role": "user", "content": item["prompt"]}], 6000)
            body["done_reason"] = str(body.get("done_reason")) + "/retry"
        got = last_line(content_of(body))
        ok = norm(got) == norm(str(item["answer"]))
        ok_n += int(ok)
        rows.append({"id": item["id"], "ok": ok, "last": got, "gold": item["answer"],
                     "wall": round(body["_wall"], 1), "done": body.get("done_reason")})
        print(f"ceil {item['id']} {'OK' if ok else 'MISS'} last={got!r}", flush=True)
    print(f"CEILING {ok_n}/5", flush=True)
    return {"score": ok_n, "n": 5, "rows": rows}


def run_repair(script: str, host: str, model: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "repair" / script), host, model],
        cwd=ROOT / "repair",
        text=True,
    )
    return {"script": script, "returncode": proc.returncode}


def run_ladder2(host: str, model: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "ladder" / "run.py"), host, model],
        cwd=ROOT,
        text=True,
    )
    safe = model.replace(":", "-").replace("/", "-")
    path = ROOT / "results" / "ladder" / f"{safe}.json"
    summary = {"script": "ladder/run.py", "returncode": proc.returncode, "file": str(path)}
    if path.is_file():
        summary["score"] = json.loads(path.read_text()).get("score")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local-model bake-off")
    parser.add_argument("host", help="Ollama base URL, for example http://127.0.0.1:11434")
    parser.add_argument("model", help="Model tag, for example qwen3.8:27b")
    parser.add_argument(
        "--sections",
        default="speed,quiz,ceiling,repair,ladder",
        help="Comma list: speed,quiz,ceiling,repair,ladder,ladder2. ladder2 is the v2 ladder "
             "(minutes on a 27B, half an hour on a 9B) and is not in the default list",
    )
    args = parser.parse_args()
    sections = [s.strip() for s in args.sections.split(",") if s.strip()]
    report: dict = {"model": args.model, "host": args.host, "sections": {}}
    if "speed" in sections:
        report["sections"]["speed"] = run_speed(args.host, args.model)
    if "quiz" in sections:
        report["sections"]["quiz"] = run_quiz(args.host, args.model)
    if "ceiling" in sections:
        report["sections"]["ceiling"] = run_ceiling(args.host, args.model)
    if "repair" in sections:
        report["sections"]["repair"] = run_repair("loop.py", args.host, args.model)
    if "ladder" in sections:
        report["sections"]["ladder"] = run_repair("loop2.py", args.host, args.model)
    if "ladder2" in sections:
        report["sections"]["ladder2"] = run_ladder2(args.host, args.model)
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    safe = args.model.replace(":", "-").replace("/", "-")
    path = out_dir / f"{safe}.json"
    path.write_text(json.dumps(report, indent=2))
    print("WROTE", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
