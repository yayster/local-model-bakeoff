#!/usr/bin/env python3
"""Three SVG charts for the 2026-11-03 bake-off story. No dependencies.
Light tokens by default; a prefers-color-scheme block switches to the dark set.
Palette: the dataviz reference instance (blue sequential ramp, validated --ordinal)."""
import json, pathlib, html

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE.parent / "results" / "ladder"
W = 1600
FONT = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"
STYLE = """
<style>
  :root { --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --grid:#e8e6e1; --bar:#2a78d6;
          --s0:#86b6ef; --s1:#3987e5; --s2:#1c5cab; --s3:#0d366b; --on-dark:#f0efec; --crit:#d03b3b; }
  @media (prefers-color-scheme: dark) {
    :root { --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --grid:#383835; --bar:#3987e5;
            --s0:#184f95; --s1:#3987e5; --s2:#86b6ef; --s3:#cde2fb; --on-dark:#0b0b0b; --crit:#d03b3b; }
  }
  text { font-family: %s; fill: var(--ink); }
  .t2 { fill: var(--ink2); }
  .grid { stroke: var(--grid); stroke-width: 1; }
  .bar { fill: var(--bar); }
  .crit { fill: var(--crit); }
</style>""" % FONT

def bar_path(x, y, w, h, r=4):
    w = max(w, r)
    return (f"M{x:.1f},{y:.1f} h{w-r:.1f} a{r},{r} 0 0 1 {r},{r} v{h-2*r:.1f} "
            f"a{r},{r} 0 0 1 -{r},{r} h-{w-r:.1f} z")

def svg(h, body, title, sub):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{html.escape(title)}">'
            f'{STYLE}<rect width="{W}" height="{h}" style="fill:var(--surface)"/>'
            f'<text x="60" y="64" font-size="34" font-weight="600">{html.escape(title)}</text>'
            f'<text x="60" y="98" font-size="20" class="t2">{html.escape(sub)}</text>{body}</svg>')

# ------------------------------------------------------------------ chart 1
ROWS = [
    ("glm-5.3-flash:cloud", "cloud, via aux-host, 3 Nov", 16, 36.3, 4.2),
    ("deepseek-v4.1-flash:cloud", "cloud, via aux-host, 3 Nov", 15, 10.9, 1.0),
    ("qwen3.8-u:27b", "gpu-host pool, llama-server, 3 Nov", 13, 16.1, 12.1),
    ("qwen3.8:27b", "gpu-host, Ollama, 26 Oct", 13, 14.0, 4.2),
    ("qwen3.8:27b", "gpu-host pool, llama-server, 3 Nov", 12, 21.2, 15.9),
    ("ornith-1.5:35b", "gpu-host, Ollama, 26 Oct", 12, 17.9, 3.3),
    ("laguna-xs-2.1:q4_K_M", "gpu-host, Ollama, 26 Oct", 11, 26.7, 3.9),
    ("flint:40b", "gpu-host, Ollama, 26 Oct", 11, 7.5, 1.6),
    ("ornith-1.5:9b", "aux-host, Ollama, 26 Oct", 10, 41.0, 28.9),
]
def chart1():
    top, rh, bh = 150, 68, 22
    left = 440
    panels = [("Rungs passed, of 16", 2, 16, "{:.0f}"), ("Tokens generated per climb, thousands", 3, 42, "{:.1f}k"),
              ("Minutes per climb", 4, 30, "{:.1f}")]
    pw, gap = 330, 50
    out = []
    for i, (name, seat, *_) in enumerate(ROWS):
        y = top + i * rh
        out.append(f'<text x="{left-16}" y="{y+bh/2+2}" font-size="20" text-anchor="end" font-weight="600">{html.escape(name)}</text>')
        out.append(f'<text x="{left-16}" y="{y+bh/2+24}" font-size="15" text-anchor="end" class="t2">{html.escape(seat)}</text>')
    for p, (label, col, vmax, fmt) in enumerate(panels):
        x0 = left + p * (pw + gap)
        out.append(f'<text x="{x0}" y="{top-18}" font-size="18" class="t2">{html.escape(label)}</text>')
        out.append(f'<line x1="{x0}" y1="{top-6}" x2="{x0}" y2="{top+len(ROWS)*rh-30}" class="grid"/>')
        for i, row in enumerate(ROWS):
            y = top + i * rh
            v = row[col]
            w = pw * v / vmax
            out.append(f'<path d="{bar_path(x0, y, w, bh)}" class="bar"/>')
            out.append(f'<text x="{x0+w+8}" y="{y+bh/2+6}" font-size="17" class="t2">{fmt.format(v)}</text>')
    h = top + len(ROWS) * rh + 60
    out.append(f'<text x="60" y="{h-28}" font-size="15" class="t2">Medians of three climbs each. The October rows ran the first ladder hash (f344); today\'s rows ran 1173, which only changed how rung 15 is timed. Cloud tags report no decode speed.</text>')
    return svg(h, "".join(out), "The ladder gap is one rung; the cost gap is three to four times",
               "Sixteen agentic repair rungs, think off, temperature 0, seed 0. Sorted by rungs passed.")

# ------------------------------------------------------------------ chart 2
RUNGS = ["pages","slug","semver","intervals","lru","bucket","config","toposort","shlex","jsonptr","cron","expr","undo","reconcile","ranges","allocate"]
def counts(path):
    d = json.loads(path.read_text())
    c = {r: 0 for r in RUNGS}
    for run in d["runs"]:
        for row in run["rows"]:
            if row["passed"]:
                c[row["id"]] += 1
    return c
MATRIX = [
    ("glm-5.3-flash:cloud", "1173", counts(RES/"glm-5.3-flash-cloud.json")),
    ("deepseek-v4.1-flash:cloud", "1173", counts(RES/"deepseek-v4.1-flash-cloud.json")),
    ("qwen3.8-u:27b, pool", "1173", counts(RES/"qwen3.8-u-27b.json")),
    ("qwen3.8:27b, pool", "1173", counts(RES/"qwen3.8-27b.json")),
    # the October result file for this tag was overwritten on 3 Nov; counts come from logs/sweep-gpu-host.log
    ("qwen3.8:27b, Ollama, Oct", "f344", {r: (0 if r in ("shlex","expr","allocate") else 3) for r in RUNGS}),
    ("ornith-1.5:35b, Oct", "f344", counts(RES/"ornith-1.5-35b.json")),
    ("laguna-xs-2.1:q4_K_M, Oct", "f344", counts(RES/"laguna-xs-2.1-q4_K_M.json")),
    ("flint:40b, Oct", "f344", counts(RES/"flint-40b.json")),
    ("ornith-1.5:9b, Oct", "f344", counts(RES/"ornith-1.5-9b.json")),
    ("glm-5.3-flash:cloud, first grader", "c5d2", counts(RES/"glm-5.3-flash-cloud-c5d2.json")),
    ("deepseek-v4.1-flash:cloud, first grader", "c5d2", counts(RES/"deepseek-v4.1-flash-cloud-c5d2.json")),
]
def chart2():
    top, left, cw, ch = 190, 470, 64, 46
    out = []
    for j, r in enumerate(RUNGS):
        x = left + j * cw + cw / 2
        out.append(f'<text x="{x}" y="{top-44}" font-size="15" text-anchor="middle" class="t2">{j+1}</text>')
        out.append(f'<text x="{x}" y="{top-22}" font-size="14" text-anchor="middle" class="t2">{r}</text>')
    for i, (name, h, c) in enumerate(MATRIX):
        y = top + i * ch
        out.append(f'<text x="{left-14}" y="{y+ch/2+6}" font-size="17" text-anchor="end">{html.escape(name)}</text>')
        out.append(f'<text x="{left+16*cw+12}" y="{y+ch/2+6}" font-size="14" class="t2">{h}</text>')
        for j, r in enumerate(RUNGS):
            n = c[r]
            x = left + j * cw
            out.append(f'<rect x="{x+1}" y="{y+1}" width="{cw-2}" height="{ch-2}" rx="3" style="fill:var(--s{n})"/>')
            if n < 3:
                ink = "var(--ink)" if n < 2 else "var(--on-dark)"
                out.append(f'<text x="{x+cw/2}" y="{y+ch/2+6}" font-size="15" text-anchor="middle" style="fill:{ink}">{n}/3</text>')
    y = top + len(MATRIX) * ch + 34
    for k, lab in enumerate(["0 of 3 climbs", "1 of 3", "2 of 3", "3 of 3"]):
        x = left + k * 190
        out.append(f'<rect x="{x}" y="{y-16}" width="22" height="22" rx="3" style="fill:var(--s{k})"/>')
        out.append(f'<text x="{x+30}" y="{y+1}" font-size="16" class="t2">{lab}</text>')
    out.append(f'<text x="60" y="{y+46}" font-size="15" class="t2">Rungs 9 and 12 are the ceiling for every local model; the cloud tags clear them. The c5d2 rows are the same two models before rung 15\'s clock was moved into the worker.</text>')
    return svg(y + 70, "".join(out), "Where each model falls: hidden-test passes per rung over three climbs",
               "Rows are runs; a cell is how many of the three climbs passed every hidden case on that rung.")

# ------------------------------------------------------------------ chart 3
TIMES = [("glm, climb 1", 2.306, False), ("glm, climb 2", 1.984, False), ("glm, climb 3", 2.156, False),
         ("deepseek, climb 1", 2.401, False), ("deepseek, climb 2", 2.064, False), ("deepseek, climb 3", 2.758, True),
         ("gold fix, --mock gold", 2.093, False)]
def chart3():
    top, left, rh, bh, pw = 160, 380, 56, 22, 700
    vmax = 3.2
    out = []
    out.append(f'<text x="{left}" y="{top-24}" font-size="18" class="t2">Hidden suite wall seconds under the first two-process grader (hash c5d2); the call\'s own budget is 2.0 s</text>')
    xb = left + pw * 2.0 / vmax
    out.append(f'<line x1="{xb}" y1="{top-8}" x2="{xb}" y2="{top+len(TIMES)*rh-8}" stroke="var(--ink2)" stroke-width="2" stroke-dasharray="6 6"/>')
    out.append(f'<text x="{xb+8}" y="{top-2}" font-size="15" class="t2">2.0 s budget</text>')
    for i, (lab, v, miss) in enumerate(TIMES):
        y = top + i * rh
        out.append(f'<text x="{left-14}" y="{y+bh/2+6}" font-size="18" text-anchor="end">{html.escape(lab)}</text>')
        w = pw * v / vmax
        out.append(f'<path d="{bar_path(left, y, w, bh)}" class="{"crit" if miss else "bar"}"/>')
        tag = f"{v:.2f} s" + ("   ✕ MISS: the timed call alone read 2.20 s" if miss else "")
        out.append(f'<text x="{left+w+8}" y="{y+bh/2+6}" font-size="16" class="t2">{tag}</text>')
    y = top + len(TIMES) * rh + 24
    out.append(f'<text x="{left-14}" y="{y+bh/2+6}" font-size="18" text-anchor="end" font-weight="600">gold fix, clock inside the worker</text>')
    w = pw * 0.234 / vmax
    out.append(f'<path d="{bar_path(left, y, w, bh)}" class="bar"/>')
    out.append(f'<text x="{left+w+8}" y="{y+bh/2+6}" font-size="16" class="t2">0.23 s   (hash 1173, the fix: ladder_clock.last_call_seconds)</text>')
    out.append(f'<text x="60" y="{y+78}" font-size="15" class="t2">All seven c5d2 bars ran the same sort-and-bisect fix. The wall clock in the assertion process was counting the JSON proxy on two 100k-entry lists, not the submission.</text>')
    return svg(y + 100, "".join(out), "Rung 15 was a coin flip: the grader's clock, not the model",
               "deepseek's third climb missed with code byte-identical to its two passes")

for name, fn in (("01-ladder-and-cost", chart1), ("02-per-rung-matrix", chart2), ("03-rung15-clock", chart3)):
    (HERE / f"{name}.svg").write_text(fn())
    print("wrote", name + ".svg")
page = ["<!doctype html><meta charset='utf-8'><title>Bake-off charts</title>",
        "<style>body{margin:0;padding:24px;background:#fcfcfb;color:#0b0b0b;font-family:%s} @media (prefers-color-scheme:dark){body{background:#1a1a19;color:#f0efec}} svg{max-width:100%%;height:auto;display:block;margin:0 0 48px} table{border-collapse:collapse;margin:0 0 56px;font-size:14px} td,th{padding:4px 10px;border-bottom:1px solid #8884}</style>" % FONT]
page.append((HERE / "01-ladder-and-cost.svg").read_text())
page.append("<table><tr><th>Model</th><th>Seat</th><th>Passed</th><th>Tokens (k)</th><th>Minutes</th></tr>" + "".join(f"<tr><td>{n}</td><td>{s}</td><td>{p}</td><td>{t}</td><td>{m}</td></tr>" for n, s, p, t, m in ROWS) + "</table>")
page.append((HERE / "02-per-rung-matrix.svg").read_text())
page.append("<table><tr><th>Run</th><th>Hash</th>" + "".join(f"<th>{r}</th>" for r in RUNGS) + "</tr>" + "".join("<tr><td>%s</td><td>%s</td>%s</tr>" % (n, h, "".join(f"<td>{c[r]}/3</td>" for r in RUNGS)) for n, h, c in MATRIX) + "</table>")
page.append((HERE / "03-rung15-clock.svg").read_text())
page.append("<table><tr><th>Climb</th><th>Hidden suite seconds</th></tr>" + "".join(f"<tr><td>{l}</td><td>{v:.3f}{' (miss)' if m else ''}</td></tr>" for l, v, m in TIMES) + "<tr><td>gold, in-worker clock, hash 1173</td><td>0.234</td></tr></table>")
(HERE / "charts.html").write_text("\n".join(page))
print("wrote charts.html")
