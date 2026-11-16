# The afternoon the ladder learned to tell its own noise from a model's

The story of 3 November 2026, in which two cloud models were raced up a
sixteen-rung repair ladder, a reviewer pointed out that the ladder's noise was
as large as the gap it was measuring, the noise turned out to be the grader's
own clock, the harness learned to speak to the new llama.cpp pool on gpu-host, and
the same 27B model turned out to score differently depending on which engine
served it.

Written by Claude (Fable 5.1) the same evening, from the session transcript,
for David's review and then for the video agent, who may turn it into a video. Times
are UTC. Quotes from David and from Hermes are verbatim from the session. Every
number here is in the bundle beside this file; `README.md` says where.

---

## Cast

**The humans and agents**

- David (the owner): owner of the fleet, maker of every decision in this story.
- Claude: the AI doing the work from a terminal on David's laptop.
- Hermes: David's reviewing agent, who read the first report and sent back the
  critique that changed the afternoon.
- the video agent: the agent this bundle is for; author of gpu-mode, first reader of
  the seat-mode handover, and the one who may make the video.
- The Hermes agent fleet: agent-host, laptop-a, edge-box, paperclip-vm-host, laptop-b. They use
  gpu-host's house model all day and were drained for the last act.

**The machines**

| host | what it is | role today |
|---|---|---|
| aux-host | VM with two GTX 1070s, Ollama 0.40.6 pinned to CPU | the proxy through which Ollama's cloud tags were reached |
| gpu-host | VM with two RTX 5060 Ti 16 GB, Ollama stopped since 2 Nov, `llama-pool.service` on :11434 | the local seat, OpenAI `/v1` routes only |

**The models**

- `glm-5.3-flash:cloud` and `deepseek-v4.1-flash:cloud`: Ollama's cloud-proxied
  tags. No GPU seat; the minutes measure the cloud service.
- `qwen3.8-u:27b`: the house model on gpu-host, the Qwen3.8-27B-Uncensored imatrix
  Q4_K_M blob re-tagged. 16 GB plus an 885 MB vision projector.
- `qwen3.8:27b`: the blob from the 26 October bake-off, Qwen3.8 27B 0814, Q4_K_M,
  15 GiB. Same family, different weights.

**The instrument**: ladder v2, sixteen agentic repair rungs of rising
difficulty. Each rung is a small Python project with a spec, a bug, a public
test, and a hidden test the model never sees. The model gets five tools
(`list_files`, `read_file`, `write_file`, `run_tests`, `run_python`), a turn
budget, and the rule that it may not edit tests. Grading runs the hidden tests
in a separate process that proxies every call into a worker holding the
submission. The protocol is think off, temperature 0, seed 0, three repeats.
Every result file carries a hash of everything that affects a score. Three
hashes appear in this story: `f344` (26 October), `c5d2` (the first
two-process grader), and `1173` (after today's fix).

---

## Prologue: "can you do a bake off"

> on aux-host's ollama, I have two models: glm-5.3-flash:cloud and and
> deepseek-v4.1-flash:cloud
>
> can you do a bake off between them, please?

glm had already been run on 26 October, 16 of 16 on all three climbs, the
proof that every rung is solvable from the spec by a real model. But that
climb was on hash `f344`, and the grader had been rebuilt twice since (hidden
tests in their own process; the worker never sees the test source). So the
fair thing was to rerun both on today's ladder. `run.py --check` validated the
ladder in 80 s, hash `c5d2`, and at 21:16 both models started up the ladder,
glm first.

## Act 1: Two climbs, two temperaments (21:16 to 21:36)

glm reproduced October exactly: 16 of 16, three for three, about 36k tokens
and four and a half minutes a climb. It still writes long analysis into its
visible reply with thinking off and hit the 3000-token cap before its first
tool call on three rungs; the harness nudges it and it recovers.

deepseek finished all three climbs in three minutes. That looked wrong, so the
log got read before anything else. It was right. deepseek works in a fixed
five-turn pattern: list, read, write, test, stop. About 1,100 tokens a rung.
Fifteen of sixteen on the first two climbs, fourteen on the third.

The misses:

- **expr, every climb.** Its parser maps `/` by zero to ValueError, as the spec
  says, but lets `0 ** -1` escape as Python's ZeroDivisionError. The hidden
  `test_errors` case catches it. Fair, and the subtlest sentence on the ladder.
- **ranges, third climb only.** The hidden `test_large_is_fast` case measured
  2.20 s against the spec's 2 s limit. The fix deepseek wrote was byte-identical
  to the fix on its two passes: sort once, bisect per range.

That second miss was the thread to pull. The hidden suite's wall time on all
six cloud climbs was between 1.98 s and 2.76 s, and `--mock gold`, the harness's
own reference fix, came in at 2.09 s. Under the two-process grader the
100k-entry lists cross a JSON proxy to the worker and are synced back after the
call. The test's `perf_counter` in the assertion process was timing the proxy,
not the submission. Rung 15 was a coin flip for every model.

The classic sections ran next: glm quiz 9/10, ceiling 4/5 (the reasoning leak on
the last line), repair 8/8, old ladder 8/8. deepseek quiz 6/10, ceiling 5/5,
repair 8/8, old ladder 8/8. deepseek's four quiz misses were formatting: two
right values in bold, two replies ending on a closing code fence.

The first report went to David at 21:40 with the coin flip flagged and left
alone, because fixing it changes the ladder hash mid-run. David's agent read it.

## Act 2: The review (21:45)

Hermes sent back the critique in full. The parts that mattered:

> Ladder: the gap is one rung. That is not "wide." What's wide is cost and
> latency — 11k vs 38k tokens, 1.0 vs 4.6 min.

> The hole: your noise floor is as big as your signal. Rung 15 is a coin flip
> inside a 1.98–2.76 s spread, and the measured difference between the models is
> one rung. You cannot rank two models on a ladder whose own variance equals the
> delta.

> if deepseek's fix was byte-identical across all three climbs, those climbs are
> not three independent trials — effective n is closer to 1, and the only
> randomness in the whole six-climb set is the grader's clock.

> Fix rung 15 properly — move the timing case inside the worker or raise the
> budget — accept the hash change, and re-run both. Then keep both hashes'
> results side by side.

One claim in the review was wrong and got corrected rather than absorbed:
"Height 16 vs 11 with 15/16 passed suggests deepseek took a different/shorter
route." Height is not a route. It is the rung below the first failure, and
deepseek's first failure was rung 12 on every climb, so 11 follows from that
alone. Everything else was taken.

## Act 3: Moving the clock into the worker (21:45 to 22:13)

The fix is small and in the bundle as a patch. The worker binds
`time.perf_counter` to a local name before the submission loads, so a
submission cannot patch the clock out from under it, and times each proxied
call. The assertion process keeps the seconds of the most recent call and
exposes them as `ladder_clock.last_call_seconds()`. The ranges hidden test
reads that instead of its own wall clock. Measured: the gold fix 0.23 s inside
the worker, the untouched bug still times out, `--check` passes, new hash
`1173`.

Both cloud models reran. Identical outcomes: glm 16 of 16 three times, deepseek
15 of 16 three times with expr the only miss and ranges clean. All five mock
models (gold, lazy, trap, cheat, loop) met their contracts on the new harness.
The old results were set aside under a `-c5d2` suffix and `report.py` grew a
hash column so the two never fold into one row.

## Act 4: "against the same metrics" (22:20 to 23:47)

> Please run qwen3.8:27b from gpu-host:11434/v1 against the same metrics.

gpu-host's :11434 has been `llama-pool.service` since the evening of 2 November,
llama.cpp's `llama-server`, OpenAI `/v1` routes only, serving one model. The
harness spoke only Ollama's `/api/chat`. So the harness learned `/v1`: a new
module, `ladder/v1chat.py`, converts the Ollama message shapes to OpenAI and
back (ids on every tool call, arguments as JSON strings, tool results matched to
their ids in order), turns thinking off through the chat template, reads speed
from the server's `timings`, and reads the seat from `/props`. A host whose path
ends in `/v1` selects it; `ladder/run.py`, `bakeoff.py` and both repair loops run
unchanged against either API. A two-turn tool round trip against gpu-host confirmed
it: both calls parsed, no thinking leak, 24.5 tok/s.

The pool was serving `qwen3.8-u:27b`, the house model, not the October blob.
Switching it means a `seat-mode model` restart under the agents, so the house
model ran first, in everyday use, with the swap offered for later. At 22:58 it
started climbing.

Thirteen of sixteen, three identical climbs: shlex (the empty word from `''`,
like every local model), cron (7 is not Sunday), and expr (the same
`0 ** -1` catch that takes deepseek). It passed allocate, where the October blob
had failed, and failed cron, where the October blob had passed. Twelve minutes a
climb against October's four, at the same decode speed. Classic: 24.3 tok/s,
quiz 8/10, ceiling 4/5, repair 8/8, old ladder 8/8.

## Act 5: "the fleet is drained at this time" (23:50 to 00:52)

> yes, do the exact october blob as well please.  the fleet is drained at this
> time.

`/slots` showed zero of four busy. One command over ssh,
`sudo -n seat-mode model qwen3.8:27b`, and 40 s later the pool was serving the
October blob at 131072 context with 23.9 GB resident, verify PASS. The run
script carried the restore at its end so the pool could not be left on the test
tag.

The October blob, on llama-server, three identical climbs: **twelve** of
sixteen. One below its October score. Same shlex, expr, and allocate as before,
plus undo. The undo transcript is the best thirty seconds of footage in the
bundle: the model writes a fix, runs one self-check snippet that fails on its
own assertion, and then re-runs that exact snippet eight more times, never
touching the source, until its twelve turns are gone. On Ollama in October it
cleared undo in four turns on every climb. On expr its rewrite broke the
tokenizer and it spent the budget re-running the same diagnostic.

Sixteen minutes a climb with nothing else on the server. So the earlier twelve
minutes were not agent contention. A probe after the run settled it: a repeated
2.9k-token prefix reprocesses four tokens, so the prompt cache works. The climb
is decode-bound. 21k generated tokens at 24.3 tok/s is fourteen of the sixteen
minutes. The October sweep log for the same blob on the same two cards under
Ollama shows a median turn of 2.3 s against 5.1 s today, and implies about
60 tok/s. The pool's layer split runs one card at a time.

Classic on the October blob: 24.3 tok/s, quiz 8/10, ceiling 5/5, repair 8/8,
old ladder 8/8. At 00:52 the pool went back to the house model, verify PASS.

## Act 6: The file that got overwritten

The run also overwrote the October result file for `qwen3.8:27b`, because the
runner names results by model alone. The per-rung October lines survive in
`logs/sweep-gpu-host.log` and in the README table, and they are what the matrix
chart's October row is drawn from. The runner now moves an existing result and
its transcripts aside under their hash and date before writing, tested on a
scratch directory. It is the kind of mistake the harness should have refused
to let anyone make, and now it does.

---

## What the day measured

| Model | Engine | Passed | Gain | Height | Tokens | Min per climb | Speed | Quiz | Ceiling | Repair | Old ladder |
|---|---|---|---|---|---|---|---|---|---|---|---|
| glm-5.3-flash:cloud | cloud via aux-host | 16/16 | 100% | 16 | 36k | 4.2 | n/a | 9/10 | 4/5 | 8/8 | 8/8 |
| deepseek-v4.1-flash:cloud | cloud via aux-host | 15/16 | 98% | 11 | 11k | 1.0 | n/a | 6/10 | 5/5 | 8/8 | 8/8 |
| qwen3.8-u:27b | llama-server, gpu-host | 13/16 | 94% | 8 | 16k | 12.1 | 24.3 tok/s | 8/10 | 4/5 | 8/8 | 8/8 |
| qwen3.8:27b | Ollama, gpu-host, 26 Oct | 13/16 | 94% | 8 | 14k | 4.2 | not on disk | | | | |
| qwen3.8:27b | llama-server, gpu-host | 12/16 | 86% | 8 | 21k | 15.9 | 24.3 tok/s | 8/10 | 5/5 | 8/8 | 8/8 |

Medians of three climbs. The cloud rows are hash `1173`; their `c5d2` twins are
in the bundle and differ only on the ranges coin flip.

## What went wrong

- **Rung 15's clock had been measuring the harness since 26 October.** The
  two-process grader is a security feature, and it silently turned a timing
  test into a coin flip. It took a reviewer saying "your noise floor is as big
  as your signal" to make fixing it mid-day the obvious call.
- **The October result file for qwen3.8:27b was overwritten.** Recoverable from
  the sweep log; still, a harness that hashes everything should not have let a
  file be clobbered.
- **"Wide margin on both axes" in the first report.** The ladder margin was one
  rung. Hermes was right to object, and the write-up now says so.

## What went right

- **Reading the log before trusting a fast run.** deepseek's three-minute
  ladder was genuine, but checking cost thirty seconds and the habit is what
  found the identical-fix pattern on ranges.
- **Taking the review and pushing back on the one wrong claim.** Height is not
  path-dependent; the rest of the critique was adopted in full, including the
  framing.
- **Keeping the pool's state safe.** The house model ran first without a
  restart; the swap waited for "the fleet is drained"; the restore was in the
  script, not in anyone's memory.
- **One adapter, four scripts, no changes to the loop.** The `/v1` port touched
  the protocol boundary only.

## What I would do differently

- Fix a known coin-flip rung before any run, not after. The hash exists so that
  results on different ladders cannot be confused; use it.
- Tag every rerun of an existing model name. The archive guard now does this
  for you, but the habit is cheaper.
- Record `nvidia-smi` into the seat for `/v1` hosts automatically, since
  llama-server does not report residency.

## The final shape

- The ladder is on hash `1173`, with `ladder_clock` for timing tests and an
  archive guard on result files.
- The harness runs against Ollama or any OpenAI `/v1` server; gpu-host's pool is
  `http://gpu-host:11434/v1`.
- Four runs today, two hashes for the cloud pair, all in `results/` with
  transcripts, and a report that shows the hash on every row.
- Two open recommendations, both David's to decide: route deepseek as the
  default worker and glm for review and human-facing output (Hermes's
  suggestion), and measure `--split-mode row` in `seat-mode local`, because
  the pool decodes the same blob at under half the October pace.

---

## Notes for the video

A possible spine, with the evidence for each beat:

1. **Cold open: "Done. 16 of 16 against 15 of 16."** Chart 1
   (`charts/01-ladder-and-cost.png`). Then the reviewer's line: "the gap is one
   rung. That is not wide." Cut to the right-hand panels of the same chart.
2. **The three-minute ladder.** Scroll `logs/live-aux-host-deepseek-v4.1-flash-cloud-c5d2.log`:
   the five-turn pattern repeating. Contrast with glm's log and its nudges.
3. **The coin flip.** Chart 3 (`charts/03-rung15-clock.png`). Show the identical
   fix in `results/ladder/deepseek-v4.1-flash-cloud-c5d2/rep1/15-ranges.json`
   and `rep3/15-ranges.json`. Then the patch: `harness-diff/2026-11-03-harness-changes.patch`,
   the `_clock = _time.perf_counter` line and `ladder_clock`.
4. **The review.** `docs/hermes-review-2026-11-03.md` on screen, with the one
   correction about height.
5. **Teaching the harness `/v1`.** `harness-diff/v1chat.py`, the `to_openai`
   function; the smoke test numbers (24.5 tok/s, both tool calls parsed).
6. **The same model, two engines.** Chart 2 (`charts/02-per-rung-matrix.png`),
   rows four and five. Then the undo loop:
   `results/ladder/qwen3.8-27b/rep1/13-undo.json`, assistant turns 5 through 12,
   the same snippet eight times. Then the seat-mode switch lines in
   `logs/bake4.log`, verify PASS both ways.
7. **Close on the cost axis and the two open decisions.** Chart 1 again, right
   panels; the recommendations above.

Every file named here is in this bundle. `README.md` is the index.
