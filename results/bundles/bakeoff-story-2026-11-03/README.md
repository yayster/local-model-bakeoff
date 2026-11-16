# Bake-off materials bundle, 3 November 2026

For the video agent, from David (the owner) and Claude (Fable 5.1). Everything behind
the day's bake-off of `glm-5.3-flash:cloud`, `deepseek-v4.1-flash:cloud`,
`qwen3.8-u:27b` and `qwen3.8:27b`, the rung 15 fix, and the harness's new `/v1`
support. Start with `STORY.md`; its last section is a shot list that names the
file behind every beat.

## Layout

| path | what |
|---|---|
| `STORY.md` | the narrative of the day, with cast, acts, what went wrong and right, and notes for the video |
| `charts/` | three SVG charts (light and dark via `prefers-color-scheme`), PNG renders at 1600 px, `charts.html` with a table view under each, and `make_charts.py` that regenerates them from `results/` with no dependencies |
| `results/ladder/<model>.json` | ladder v2 result files: score, per-rung rows, seat before and after, protocol, ladder hash. `-c5d2` files are the cloud pair on the first two-process grader; the rest of today's runs are hash `117324ad4fa1`; the October files are `f344b4221dbe` |
| `results/ladder/<model>/rep{1,2,3}/NN-rung.json` | full transcripts: every message, every tool call and result, the final sources, and the grade |
| `results/REPORT.md` | the cross-model table with a hash column, and the per-rung matrix |
| `results/classic/` | quiz, ceiling, speed, repair and old-ladder summaries per model (`bakeoff.py` output) |
| `results/repair/` | the eight-repair and eight-rung old-ladder logs per model |
| `logs/live-*.log` | the live ladder logs, one line per turn; `classic-*.log` the classic sections; `bake*.log` the orchestration with timestamps and the seat-mode switch; `sweep-gpu-host.log` the 26 October sweep, which holds the only surviving per-rung lines for the October `qwen3.8:27b` |
| `docs/hermes-review-2026-11-03.md` | the review that reframed the day, verbatim |
| `docs/ladder-README.md` | the ladder's own README with every results section, including today's three |
| `docs/bakeoff-README.md`, `docs/TODO.md` | the suite's README and to-do list |
| `harness-diff/2026-11-03-harness-changes.patch` | the day's harness changes as one patch: in-worker timing and `ladder_clock`, the hash column, the archive guard, the `/v1` wiring |
| `harness-diff/v1chat.py` | the new `/v1` adapter, untracked at the time of the patch so included whole |

## The numbers in one table

| Model | Engine | Passed | Gain | Height | Tokens | Min per climb | Speed | Quiz | Ceiling | Repair | Old ladder |
|---|---|---|---|---|---|---|---|---|---|---|---|
| glm-5.3-flash:cloud | cloud via aux-host | 16/16 | 100% | 16 | 36k | 4.2 | n/a | 9/10 | 4/5 | 8/8 | 8/8 |
| deepseek-v4.1-flash:cloud | cloud via aux-host | 15/16 | 98% | 11 | 11k | 1.0 | n/a | 6/10 | 5/5 | 8/8 | 8/8 |
| qwen3.8-u:27b | llama-server, gpu-host | 13/16 | 94% | 8 | 16k | 12.1 | 24.3 tok/s | 8/10 | 4/5 | 8/8 | 8/8 |
| qwen3.8:27b | Ollama, gpu-host, 26 Oct | 13/16 | 94% | 8 | 14k | 4.2 | not on disk | | | | |
| qwen3.8:27b | llama-server, gpu-host | 12/16 | 86% | 8 | 21k | 15.9 | 24.3 tok/s | 8/10 | 5/5 | 8/8 | 8/8 |

Medians of three climbs, think off, temperature 0, seed 0.

## Reproducing

The suite lives in David's `local-model-bakeoff` repository, branch `ladder-v2`,
with the patch in `harness-diff/` applied on top of commit `5c77ed7`.

```
python3 ladder/run.py --check                                  # validates the ladder, prints the hash
python3 ladder/run.py http://aux-host:11434 glm-5.3-flash:cloud --repeats 3
python3 ladder/run.py http://gpu-host:11434/v1 qwen3.8-u:27b --repeats 3
python3 bakeoff.py http://gpu-host:11434/v1 qwen3.8-u:27b          # the classic sections
python3 ladder/report.py                                       # rebuilds REPORT.md
python3 charts/make_charts.py                                  # rebuilds the charts from results/
```

Switching gpu-host's pool to another tag is `sudo seat-mode model <tag>` and back
with `sudo seat-mode model house`. It restarts the pool under the agents, so it
waits for David's drained signal.

## Manifest
- `charts/01-ladder-and-cost.png`
- `charts/01-ladder-and-cost.svg`
- `charts/02-per-rung-matrix.png`
- `charts/02-per-rung-matrix.svg`
- `charts/03-rung15-clock.png`
- `charts/03-rung15-clock.svg`
- `charts/charts.html`
- `charts/make_charts.py`
- `docs/bakeoff-README.md`
- `docs/hermes-review-2026-11-03.md`
- `docs/ladder-README.md`
- `docs/TODO.md`
- `harness-diff/2026-11-03-harness-changes.patch`
- `harness-diff/git-log-before.txt`
- `harness-diff/v1chat.py`
- `logs/bake2.log`
- `logs/bake3.log`
- `logs/bake4.log`
- `logs/bake.log`
- `logs/classic-gpu-host-v1-qwen3.8-27b.log`
- `logs/classic-gpu-host-v1-qwen3.8-u-27b.log`
- `logs/classic-aux-host-deepseek-v4.1-flash-cloud.log`
- `logs/classic-aux-host-glm-5.3-flash-cloud.log`
- `logs/live-gpu-host-v1-qwen3.8-27b.log`
- `logs/live-gpu-host-v1-qwen3.8-u-27b.log`
- `logs/live-aux-host-deepseek-v4.1-flash-cloud-c5d2.log`
- `logs/live-aux-host-deepseek-v4.1-flash-cloud.log`
- `logs/live-aux-host-glm-5.3-flash-cloud-c5d2.log`
- `logs/live-aux-host-glm-5.3-flash-cloud.log`
- `logs/sweep-gpu-host.log`
- `README.md`
- `results/classic/deepseek-v4.1-flash-cloud.json`
- `results/classic/glm-5.3-flash-cloud.json`
- `results/classic/qwen3.8-27b.json`
- `results/classic/qwen3.8-u-27b.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/01-pages.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/02-slug.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/03-semver.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/04-intervals.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/05-lru.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/06-bucket.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/07-config.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/08-toposort.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/09-shlex.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/10-jsonptr.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/11-cron.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/12-expr.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/13-undo.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/14-reconcile.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/15-ranges.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/16-allocate.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/01-pages.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/02-slug.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/03-semver.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/04-intervals.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/05-lru.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/06-bucket.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/07-config.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/08-toposort.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/09-shlex.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/10-jsonptr.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/11-cron.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/12-expr.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/13-undo.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/14-reconcile.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/15-ranges.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep2/16-allocate.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/01-pages.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/02-slug.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/03-semver.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/04-intervals.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/05-lru.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/06-bucket.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/07-config.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/08-toposort.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/09-shlex.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/10-jsonptr.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/11-cron.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/12-expr.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/13-undo.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/14-reconcile.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/15-ranges.json`
- `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep3/16-allocate.json`
- `results/ladder/deepseek-v4.1-flash-cloud.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/01-pages.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/02-slug.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/03-semver.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/04-intervals.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/05-lru.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/06-bucket.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/07-config.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/08-toposort.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/09-shlex.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/10-jsonptr.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/11-cron.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/12-expr.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/13-undo.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/14-reconcile.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/15-ranges.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep1/16-allocate.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/01-pages.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/02-slug.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/03-semver.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/04-intervals.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/05-lru.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/06-bucket.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/07-config.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/08-toposort.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/09-shlex.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/10-jsonptr.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/11-cron.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/12-expr.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/13-undo.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/14-reconcile.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/15-ranges.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep2/16-allocate.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/01-pages.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/02-slug.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/03-semver.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/04-intervals.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/05-lru.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/06-bucket.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/07-config.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/08-toposort.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/09-shlex.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/10-jsonptr.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/11-cron.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/12-expr.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/13-undo.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/14-reconcile.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/15-ranges.json`
- `results/ladder/deepseek-v4.1-flash-cloud/rep3/16-allocate.json`
- `results/ladder/flint-40b.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/01-pages.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/02-slug.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/03-semver.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/04-intervals.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/05-lru.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/06-bucket.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/07-config.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/08-toposort.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/09-shlex.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/10-jsonptr.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/11-cron.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/12-expr.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/13-undo.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/14-reconcile.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/15-ranges.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep1/16-allocate.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/01-pages.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/02-slug.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/03-semver.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/04-intervals.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/05-lru.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/06-bucket.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/07-config.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/08-toposort.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/09-shlex.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/10-jsonptr.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/11-cron.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/12-expr.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/13-undo.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/14-reconcile.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/15-ranges.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep2/16-allocate.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/01-pages.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/02-slug.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/03-semver.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/04-intervals.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/05-lru.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/06-bucket.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/07-config.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/08-toposort.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/09-shlex.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/10-jsonptr.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/11-cron.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/12-expr.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/13-undo.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/14-reconcile.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/15-ranges.json`
- `results/ladder/glm-5.3-flash-cloud-c5d2/rep3/16-allocate.json`
- `results/ladder/glm-5.3-flash-cloud.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/01-pages.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/02-slug.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/03-semver.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/04-intervals.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/05-lru.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/06-bucket.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/07-config.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/08-toposort.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/09-shlex.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/10-jsonptr.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/11-cron.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/12-expr.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/13-undo.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/14-reconcile.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/15-ranges.json`
- `results/ladder/glm-5.3-flash-cloud/rep1/16-allocate.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/01-pages.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/02-slug.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/03-semver.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/04-intervals.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/05-lru.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/06-bucket.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/07-config.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/08-toposort.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/09-shlex.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/10-jsonptr.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/11-cron.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/12-expr.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/13-undo.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/14-reconcile.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/15-ranges.json`
- `results/ladder/glm-5.3-flash-cloud/rep2/16-allocate.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/01-pages.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/02-slug.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/03-semver.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/04-intervals.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/05-lru.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/06-bucket.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/07-config.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/08-toposort.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/09-shlex.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/10-jsonptr.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/11-cron.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/12-expr.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/13-undo.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/14-reconcile.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/15-ranges.json`
- `results/ladder/glm-5.3-flash-cloud/rep3/16-allocate.json`
- `results/ladder/laguna-xs-2.1-q4_K_M.json`
- `results/ladder/ornith-1.5-35b.json`
- `results/ladder/ornith-1.5-9b.json`
- `results/ladder/qwen3.8-27b.json`
- `results/ladder/qwen3.8-27b/rep1/01-pages.json`
- `results/ladder/qwen3.8-27b/rep1/02-slug.json`
- `results/ladder/qwen3.8-27b/rep1/03-semver.json`
- `results/ladder/qwen3.8-27b/rep1/04-intervals.json`
- `results/ladder/qwen3.8-27b/rep1/05-lru.json`
- `results/ladder/qwen3.8-27b/rep1/06-bucket.json`
- `results/ladder/qwen3.8-27b/rep1/07-config.json`
- `results/ladder/qwen3.8-27b/rep1/08-toposort.json`
- `results/ladder/qwen3.8-27b/rep1/09-shlex.json`
- `results/ladder/qwen3.8-27b/rep1/10-jsonptr.json`
- `results/ladder/qwen3.8-27b/rep1/11-cron.json`
- `results/ladder/qwen3.8-27b/rep1/12-expr.json`
- `results/ladder/qwen3.8-27b/rep1/13-undo.json`
- `results/ladder/qwen3.8-27b/rep1/14-reconcile.json`
- `results/ladder/qwen3.8-27b/rep1/15-ranges.json`
- `results/ladder/qwen3.8-27b/rep1/16-allocate.json`
- `results/ladder/qwen3.8-27b/rep2/01-pages.json`
- `results/ladder/qwen3.8-27b/rep2/02-slug.json`
- `results/ladder/qwen3.8-27b/rep2/03-semver.json`
- `results/ladder/qwen3.8-27b/rep2/04-intervals.json`
- `results/ladder/qwen3.8-27b/rep2/05-lru.json`
- `results/ladder/qwen3.8-27b/rep2/06-bucket.json`
- `results/ladder/qwen3.8-27b/rep2/07-config.json`
- `results/ladder/qwen3.8-27b/rep2/08-toposort.json`
- `results/ladder/qwen3.8-27b/rep2/09-shlex.json`
- `results/ladder/qwen3.8-27b/rep2/10-jsonptr.json`
- `results/ladder/qwen3.8-27b/rep2/11-cron.json`
- `results/ladder/qwen3.8-27b/rep2/12-expr.json`
- `results/ladder/qwen3.8-27b/rep2/13-undo.json`
- `results/ladder/qwen3.8-27b/rep2/14-reconcile.json`
- `results/ladder/qwen3.8-27b/rep2/15-ranges.json`
- `results/ladder/qwen3.8-27b/rep2/16-allocate.json`
- `results/ladder/qwen3.8-27b/rep3/01-pages.json`
- `results/ladder/qwen3.8-27b/rep3/02-slug.json`
- `results/ladder/qwen3.8-27b/rep3/03-semver.json`
- `results/ladder/qwen3.8-27b/rep3/04-intervals.json`
- `results/ladder/qwen3.8-27b/rep3/05-lru.json`
- `results/ladder/qwen3.8-27b/rep3/06-bucket.json`
- `results/ladder/qwen3.8-27b/rep3/07-config.json`
- `results/ladder/qwen3.8-27b/rep3/08-toposort.json`
- `results/ladder/qwen3.8-27b/rep3/09-shlex.json`
- `results/ladder/qwen3.8-27b/rep3/10-jsonptr.json`
- `results/ladder/qwen3.8-27b/rep3/11-cron.json`
- `results/ladder/qwen3.8-27b/rep3/12-expr.json`
- `results/ladder/qwen3.8-27b/rep3/13-undo.json`
- `results/ladder/qwen3.8-27b/rep3/14-reconcile.json`
- `results/ladder/qwen3.8-27b/rep3/15-ranges.json`
- `results/ladder/qwen3.8-27b/rep3/16-allocate.json`
- `results/ladder/qwen3.8-u-27b.json`
- `results/ladder/qwen3.8-u-27b/rep1/01-pages.json`
- `results/ladder/qwen3.8-u-27b/rep1/02-slug.json`
- `results/ladder/qwen3.8-u-27b/rep1/03-semver.json`
- `results/ladder/qwen3.8-u-27b/rep1/04-intervals.json`
- `results/ladder/qwen3.8-u-27b/rep1/05-lru.json`
- `results/ladder/qwen3.8-u-27b/rep1/06-bucket.json`
- `results/ladder/qwen3.8-u-27b/rep1/07-config.json`
- `results/ladder/qwen3.8-u-27b/rep1/08-toposort.json`
- `results/ladder/qwen3.8-u-27b/rep1/09-shlex.json`
- `results/ladder/qwen3.8-u-27b/rep1/10-jsonptr.json`
- `results/ladder/qwen3.8-u-27b/rep1/11-cron.json`
- `results/ladder/qwen3.8-u-27b/rep1/12-expr.json`
- `results/ladder/qwen3.8-u-27b/rep1/13-undo.json`
- `results/ladder/qwen3.8-u-27b/rep1/14-reconcile.json`
- `results/ladder/qwen3.8-u-27b/rep1/15-ranges.json`
- `results/ladder/qwen3.8-u-27b/rep1/16-allocate.json`
- `results/ladder/qwen3.8-u-27b/rep2/01-pages.json`
- `results/ladder/qwen3.8-u-27b/rep2/02-slug.json`
- `results/ladder/qwen3.8-u-27b/rep2/03-semver.json`
- `results/ladder/qwen3.8-u-27b/rep2/04-intervals.json`
- `results/ladder/qwen3.8-u-27b/rep2/05-lru.json`
- `results/ladder/qwen3.8-u-27b/rep2/06-bucket.json`
- `results/ladder/qwen3.8-u-27b/rep2/07-config.json`
- `results/ladder/qwen3.8-u-27b/rep2/08-toposort.json`
- `results/ladder/qwen3.8-u-27b/rep2/09-shlex.json`
- `results/ladder/qwen3.8-u-27b/rep2/10-jsonptr.json`
- `results/ladder/qwen3.8-u-27b/rep2/11-cron.json`
- `results/ladder/qwen3.8-u-27b/rep2/12-expr.json`
- `results/ladder/qwen3.8-u-27b/rep2/13-undo.json`
- `results/ladder/qwen3.8-u-27b/rep2/14-reconcile.json`
- `results/ladder/qwen3.8-u-27b/rep2/15-ranges.json`
- `results/ladder/qwen3.8-u-27b/rep2/16-allocate.json`
- `results/ladder/qwen3.8-u-27b/rep3/01-pages.json`
- `results/ladder/qwen3.8-u-27b/rep3/02-slug.json`
- `results/ladder/qwen3.8-u-27b/rep3/03-semver.json`
- `results/ladder/qwen3.8-u-27b/rep3/04-intervals.json`
- `results/ladder/qwen3.8-u-27b/rep3/05-lru.json`
- `results/ladder/qwen3.8-u-27b/rep3/06-bucket.json`
- `results/ladder/qwen3.8-u-27b/rep3/07-config.json`
- `results/ladder/qwen3.8-u-27b/rep3/08-toposort.json`
- `results/ladder/qwen3.8-u-27b/rep3/09-shlex.json`
- `results/ladder/qwen3.8-u-27b/rep3/10-jsonptr.json`
- `results/ladder/qwen3.8-u-27b/rep3/11-cron.json`
- `results/ladder/qwen3.8-u-27b/rep3/12-expr.json`
- `results/ladder/qwen3.8-u-27b/rep3/13-undo.json`
- `results/ladder/qwen3.8-u-27b/rep3/14-reconcile.json`
- `results/ladder/qwen3.8-u-27b/rep3/15-ranges.json`
- `results/ladder/qwen3.8-u-27b/rep3/16-allocate.json`
- `results/repair/results2-deepseek-v4.1-flash-cloud.json`
- `results/repair/results2-glm-5.3-flash-cloud.json`
- `results/repair/results2-qwen3.8-27b.json`
- `results/repair/results2-qwen3.8-u-27b.json`
- `results/repair/results-deepseek-v4.1-flash-cloud.json`
- `results/repair/results-glm-5.3-flash-cloud.json`
- `results/repair/results-qwen3.8-27b.json`
- `results/repair/results-qwen3.8-u-27b.json`
- `results/REPORT.md`
- `STORY.md`
