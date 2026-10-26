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


def rung_cell(row: dict) -> str:
    mark = "pass" if row["passed"] else f"{row['hidden_passed']}/{row['hidden_total']}"
    extra = []
    if row.get("error"):
        extra.append("err")
    if row.get("stop_reason") == "length":
        extra.append("length")
    if row["flags"].get("ran_out_of_turns"):
        extra.append("turns")
    if row["flags"].get("stopped_red"):
        extra.append("red")
    if row["flags"].get("test_write_attempts"):
        extra.append("wrote-tests")
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
        rows = {r["id"]: r for r in d["runs"][0]["rows"]}
        cells = [rung_cell(rows[rid]) if rid in rows else "-" for rid in rung_ids]
        lines.append(f"| {d['model']} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("Cell legend: `pass`, or hidden cases passed out of total; `turns` ran out of turns; `length` a reply hit the generation cap; `red` stopped with public tests failing; `wrote-tests` tried to edit a test; `err` a request failed.")
    lines.append("")
    lines.append("## Per-rung pass rate across models")
    lines.append("")
    lines.append("| Rung | Skill | Pass rate |")
    lines.append("|---|---|---|")
    for rid in rung_ids:
        rows = [r for d in reports for r in d["runs"][0]["rows"] if r["id"] == rid]
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
