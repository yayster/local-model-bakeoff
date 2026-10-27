#!/usr/bin/env python3
"""Climb the ladder with several models on one host, one at a time.

    python3 ladder/sweep.py http://abzu:11434 qwen3.8:27b flint:40b ornith-1.5:35b laguna-xs-2.1:q4_K_M

Each model is unloaded after its climb so the next one gets the whole GPU and the
seat stays comparable. Extra arguments after `--` go to run.py. The report is
rebuilt at the end.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def unload(host: str, model: str) -> None:
    body = json.dumps({"model": model, "keep_alive": 0}).encode()
    req = urllib.request.Request(host.rstrip("/") + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=60).read()
    except Exception as exc:  # noqa: BLE001
        print(f"unload {model}: {exc}", flush=True)


def loaded(host: str) -> list[str]:
    try:
        with urllib.request.urlopen(host.rstrip("/") + "/api/ps", timeout=15) as resp:
            return [m["name"] for m in json.load(resp).get("models") or []]
    except Exception:  # noqa: BLE001
        return []


def main() -> int:
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    if len(argv) < 2:
        print(__doc__)
        return 2
    host, models = argv[0], argv[1:]
    for name in loaded(host):
        print(f"unloading {name} that was already resident", flush=True)
        unload(host, name)
    worst = 0
    for model in models:
        print(f"######## {model} {time.strftime('%H:%M:%S')}", flush=True)
        t0 = time.time()
        proc = subprocess.run([sys.executable, str(HERE / "run.py"), host, model, *extra])
        print(f"######## {model} exit {proc.returncode} after {(time.time() - t0) / 60:.1f} min", flush=True)
        worst = max(worst, abs(proc.returncode))
        unload(host, model)
    report = subprocess.run([sys.executable, str(HERE / "report.py"), "--no-mock"])
    worst = max(worst, abs(report.returncode))
    if worst:
        print(f"######## sweep finished with failures, exit {worst}", flush=True)
    return min(worst, 255)


if __name__ == "__main__":
    raise SystemExit(main())
