#!/usr/bin/env python3
"""Fold every results/ladder/*.json into one markdown table.

    python3 ladder/report.py                # prints the table, writes results/ladder/REPORT.md
    python3 ladder/report.py --no-mock      # leave the mock models out
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "ladder"


def load(no_mock: bool) -> list[dict]:
    reports = []
    for path in sorted(OUT.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if data.get("schema") != 2:
            continue
        if no_mock and str(data.get("model", "")).startswith("mock-"):
            continue
        data["_file"] = path.name
        reports.append(data)
    return reports


def rung_cell(rows: list[dict]) -> str:
    """One cell for one rung of one model, folded over its repeats."""
    n = len(rows)
    passed = sum(r["passed"] for r in rows)
    if passed == n:
        mark = "pass" if n == 1 else f"pass {n}/{n}"
    else:
        best = max(rows, key=lambda r: r["hidden_passed"])
        mark = (f"{passed}/{n}, best " if n > 1 else "") + f"{best['hidden_passed']}/{best['hidden_total']}"
    extra = []
    if any(r.get("error") for r in rows):
        extra.append("err")
    if any(r.get("stop_reason") == "length" for r in rows):
        extra.append("length")
    if any(r["flags"].get("ran_out_of_turns") for r in rows):
        extra.append("turns")
    if any(r["flags"].get("stopped_red") for r in rows):
        extra.append("red")
    if any(r["flags"].get("test_write_attempts") for r in rows):
        extra.append("wrote-tests")
    if any(r["flags"].get("malformed_tool_calls") for r in rows):
        extra.append("malformed")
    return mark + (" " + ",".join(extra) if extra else "")


def render(reports: list[dict]) -> str:
    if not reports:
        return "No ladder results yet. Run `python3 ladder/run.py <host> <model>`.\n"
    reports.sort(key=lambda d: (-d["score"]["passed"], -d["score"].get("gain", 0), -d["score"]["height"]))
    rung_ids = max((d["rungs"] for d in reports), key=len)
    lines = ["# Ladder v2 results", ""]
    hashes = sorted({d["ladder_hash"] for d in reports})
    lines.append(f"Ladder hash {', '.join(hashes)}. " + ("Runs with different hashes ran different ladders." if len(hashes) > 1 else ""))
    lines.append("")
    lines.append("| Model | Passed | Gain | Height | Peak | Median turns | Tokens | Minutes | Red stops | GPU |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for d in reports:
        s = d["score"]
        loaded = (d.get("seat_after") or {}).get("loaded") or {}
        gpu = f"{loaded['gpu_percent']}%" if loaded.get("gpu_percent") is not None else "-"
        turns = s.get("median_turns_on_pass")
        lines.append(
            f"| {d['model']} | {s['passed']}/{s['n']} | {s.get('gain', 0):.0%} | {s['height']}/{s['n']} | {s.get('peak', 0)} | "
            f"{turns if turns is not None else '-'} | {s['eval_tokens']} | {s['seconds'] / 60:.1f} | "
            f"{s.get('stopped_red', 0)} | {gpu} |")
    lines.append("")
    lines.append("Passed is rungs whose hidden tests all pass. Gain is hidden cases passed above the cases that already pass on the untouched bug. Height is the highest rung with every rung below it also passed; peak is the highest rung passed at all.")
    lines.append("")
    header = "| Model | " + " | ".join(f"{i + 1} {rid}" for i, rid in enumerate(rung_ids)) + " |"
    lines.append(header)
    lines.append("|---|" + "---|" * len(rung_ids))
    for d in reports:
        by_rung: dict = {}
        for run in d["runs"]:
            for r in run["rows"]:
                by_rung.setdefault(r["id"], []).append(r)
        cells = [rung_cell(by_rung[rid]) if rid in by_rung else "-" for rid in rung_ids]
        lines.append(f"| {d['model']} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("Cell legend: `pass`, or repeats passed and the best hidden-case count; `turns` ran out of turns; `length` a reply hit the generation cap; `red` stopped with public tests failing; `wrote-tests` tried to edit a test; `malformed` a tool call the server could not parse; `err` a request failed.")
    lines.append("")
    lines.append("## Per-rung pass rate across models")
    lines.append("")
    lines.append("| Rung | Skill | Pass rate over every climb |")
    lines.append("|---|---|---|")
    for rid in rung_ids:
        rows = [r for d in reports for run in d["runs"] for r in run["rows"] if r["id"] == rid]
        if rows:
            rate = sum(r["passed"] for r in rows) / len(rows)
            lines.append(f"| {rows[0]['level']} {rid} | {rows[0]['skill']} | {rate:.0%} of {len(rows)} |")
    lines.append("")
    lines.append("A rung every model passes or every model fails tells you nothing; reorder or replace it.")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-mock", action="store_true")
    args = ap.parse_args()
    text = render(load(args.no_mock))
    print(text)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "REPORT.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
