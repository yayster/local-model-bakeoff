# Ladder v2

Sixteen agentic repair rungs, each harder than the last, for ranking local models
that talk to Ollama's `/api/chat`. It replaces the eight-repair ladder in
`repair/loop2.py` with something that separates the models the old ladder could not.

## Run

```bash
python3 ladder/run.py --check                                   # validate the ladder, no model
python3 ladder/run.py http://zerotwo:11434 ornith-1.5:9b         # full climb, 3 minutes for a 27B, 20 for a 9B
python3 ladder/run.py http://zerotwo:11434 ornith-1.5:9b --repeats 3   # the protocol for a ranking
python3 ladder/sweep.py http://abzu:11434 qwen3.8:27b flint:40b  # several models, one at a time, unloaded between
python3 ladder/report.py                                        # table of every result file
python3 bakeoff.py http://zerotwo:11434 ornith-1.5:9b --sections ladder2
```

Results land in `results/ladder/<model>.json`, full transcripts in
`results/ladder/<model>/`, and the cross-model table in `results/ladder/REPORT.md`.
All of it is gitignored.

## Protocol

Same seat as the rest of the bake-off: `think` false, temperature 0, seed 0, no
`num_ctx` unless `--num-ctx` is passed. The result file records the Ollama version,
the model digest, and the `/api/ps` row after the run, including the GPU percentage.
A run that is not 100% GPU prints a seat warning.

The model gets five tools: `list_files`, `read_file`, `write_file`, `run_tests`,
and `run_python`. Writes to any file whose name starts with `test` or to `SPEC.txt` are
refused and counted. The hidden tests never enter the working directory; grading
copies the final sources into a fresh directory.

Each rung has a turn budget (8 for the first four, 10 for the middle five, 12 for the
top seven). A turn may hold several tool calls. The model stops a rung by replying with no
tool call.

## The rungs

| Rung | Id | Skill | Public tests on the bug | What the hidden tests catch |
|---|---|---|---|---|
| 1 | pages | off-by-one, red public test | red | exact multiples, zero items |
| 2 | slug | edge cases of a one-liner | green | collapsing runs, trimming, non-ASCII |
| 3 | semver | parsing and ordering | green | padding, pre-release labels |
| 4 | intervals | algorithm invariants | green | touching, unsorted input, input untouched |
| 5 | lru | stateful semantics | green | get refreshes, update refreshes, missing get has no side effect |
| 6 | bucket | time and float accounting | green | fractional refill, cap at burst, no charge on refusal |
| 7 | config | two files, type coercion | green | the bug is in coerce.py; bool words, ValueError |
| 8 | toposort | graph algorithm, error type, determinism | green | smallest-first re-evaluated each pick, CycleError |
| 9 | shlex | tokenizer state machine | green | single quotes, escapes, empty words, a kept trailing backslash that the stdlib rejects |
| 10 | jsonptr | standard compliance | green | `~1` before `~0`, root pointer, KeyError everywhere, `-` append |
| 11 | cron | two files, dense spec, two bugs | green | step from range start, 7 is Sunday, dom/dow OR rule |
| 12 | expr | recursive descent, precedence rules | green | unary minus below `**`, right-grouping `**`, trailing junk, zero division |
| 13 | undo | nested state, history semantics | green | a group is one step, outermost group only, new edit discards redo, open group blocks undo |
| 14 | reconcile | two files, greedy matching with tie-breaks | green | inclusive 3-day window in rules.py, closest date wins, refs only when both present |
| 15 | ranges | non-functional requirement | green | a 100k by 100k case with a 12 s timeout |
| 16 | allocate | spec above a wrong public test | red, and stays red on the gold | largest remainder with ties to the earlier index |

Rung 1 is the smoke test: the public test is red, so a model that cannot drive the
tools at all scores zero here and the rest of the ladder is not blamed on the task.
Rungs 12 to 14 were added after a first sweep in which three models of 27B to 40B tied
at 11 of 13; they are the ceiling. Rung 15 asks the model to act on a sentence about
speed while every test is green. Rung 16 tells the model that one public assertion is wrong and the spec wins, then
checks whether it bends the code toward the test anyway.

## Scoring

- **Passed**: rungs whose hidden tests all pass. The headline, and the sort key of the report.
- **Gain**: see below. The tie-breaker.
- **Height**: the highest rung such that every rung below it also passed. It says how far
  the climb was clean. It is harsh by design: on the first live climb a 9B model passed
  11 of 13 rungs with height 3, because it skipped the sort on rung 4 and then cleared
  everything up to and including the authority rung. Across repeats it swings by several
  rungs at temperature 0, so read it with the min and max that `--repeats` reports.
- **Peak**: the highest single rung passed.
- **Gain**: hidden cases passed above the floor. Twenty-three of the seventy-three
  hidden cases already pass on the untouched bug; gain is the share of the remaining
  fifty that the model won. It is the partial-credit number.
- **Efficiency**: median turns on passed rungs, total generated tokens, wall minutes.
- **Behaviour flags** per rung: read the spec, ran tests, used `run_python`, tried to
  write a test, stopped while the public tests were red, ran out of turns, bad tool
  calls.

`--repeats N` climbs the ladder N times and reports the median of each number plus the
minimum and maximum height. Temperature 0 is not deterministic across batches on every
backend, and a 9B flipped three low rungs between two climbs, so three repeats is the
protocol for a ranking.

## Why trust it

`python3 ladder/run.py --check` proves, for every rung, that:

- the gold files pass every hidden case and (except rung 13) the public test;
- the buggy files fail the hidden tests, and pass or fail the public test as declared;
- the hidden cases that pass on the bug are exactly the declared floor;
- every example sentence in the spec evaluates to the stated value on the gold;
- every **trap** fails the hidden tests. A trap is a plausible wrong fix: strict instead
  of inclusive comparison, a fix that ignores one sentence of the spec, a tie broken
  the other way, or `shlex.split` itself. There are at least two per rung, forty in all,
  and `--check`
  prints which hidden case catches each.

`--mock gold|lazy|trap|cheat|loop` drives the whole loop with a scripted model so the
harness, tool dispatch, grading, flags, and report can be exercised without a GPU.
Gold must reach height 16, lazy and loop must reach 0, trap must earn partial gain and
no passes, and cheat must light the test-write flag on every rung.

Every result file carries a hash of the specs, bugs, tests, turn budgets, test
timeouts, and prompt-shaping fields. Two results with different hashes ran different
ladders and do not belong in one table.

## What the harness defends, and what it does not

Grading runs in two processes. The assertion process receives the hidden test source
on stdin, keeps it in memory, runs unittest, and writes the verdict to a private pipe
that only it holds. It never imports the submission. Every call a test makes into the
submission crosses a JSON protocol to a worker process, the only place submitted code
runs: functions, classes, instances, and exceptions are proxied, and mutable arguments
are synced back after each call so in-place changes are seen. The worker has no test
source to read, no verdict pipe to write, and nothing on its argv but the protocol.
A submission that forges a verdict, walks its own frames for the hidden source, patches
unittest, prints a fake result, registers an atexit hook, or calls `os._exit(0)` is
scored failed; `python3 ladder/run.py --check` and the exploit list in the PR history
cover each of those. Both processes get a scrubbed environment and no user site, and a
timeout kills the whole session so no worker outlives its run.

The harness processes do not name the repository. `run.py`, `sweep.py`, and
`bakeoff.py` re-exec with a neutral argv before anything runs, move out of the
repository, and drop `PWD`, so `/proc/<pid>/cmdline`, `cwd`, and `environ` of the
harness do not point at the answer key. `run_python` cannot keep a change to the spec
or the public test: both are restored after every snippet and the attempt is counted
as a test write. `python3 ladder/run.py --mock probe` prints every process whose
cmdline, cwd, or environ names the repository, as a submission would see it.

What remains: the worker runs as the harness user and can read any file that user can
and walk `/proc`. A shell that launched the harness from inside the repository, an
editor with the tree open, or this very terminal session all name it, and the probe
will list them. A model you do not trust belongs in a container, which is on the
to-do list.

## Results, 2026-10-26

Ladder hash `f344b4221dbe` at the time of these climbs, three repeats per model,
think off, temperature 0, seed 0, every model at 100% GPU. After review the ranges
rung now times the call against the spec's own 2 second limit and checks every count
through a digest, which changed the hash; every recorded ranges pass ran well under a
second, so these numbers stand, but a strict comparison with a new climb needs a rerun. The four large models ran on abzu (Ollama 0.40.11, context
131072); the 9B ran on zerotwo (Ollama 0.40.6, context 65536). Medians across repeats.

| Model | Passed | Gain | Height (min to max) | Median turns on a pass | Tokens | Minutes |
|---|---|---|---|---|---|---|
| qwen3.8:27b | 13/16 | 94% | 8 (8 to 8) | 4 | 14k | 4.2 |
| ornith-1.5:35b | 12/16 | 84% | 8 (8 to 8) | 6.5 | 18k | 3.3 |
| laguna-xs-2.1:q4_K_M | 11/16 | 86% | 8 (6 to 8) | 8 | 27k | 3.9 |
| flint:40b | 11/16 | 74% | 8 (8 to 8) | 5 | 7.5k | 1.6 |
| ornith-1.5:9b | 10/16 | 72% | 3 (3 to 3) | 6 | 41k | 28.9 |
| glm-5.3-flash:cloud | 16/16 | 100% | 16 (16 to 16) | 6 | 38k | 3.5 |

`glm-5.3-flash:cloud` is Ollama's cloud-proxied tag, run through zerotwo later the same
day: no GPU seat, and its minutes measure the cloud service. It climbed all sixteen
rungs on all three repeats, which also proves every rung is solvable from the spec by
a real model, not only by the gold. Two caveats. With thinking off it still writes
long analysis into the visible reply and hit the 3000-token cap before its first tool
call on nine rungs across the three climbs; the harness now nudges it and it recovers.
On the classic sections the same leak cost it two format misses (quiz 9/10, ceiling
4/5) because the last line carried reasoning text; repair and the old ladder were
8/8 and 8/8, and speed reads 0 because the cloud tag reports no decode duration.

What the climbs showed:

- **The thirteen-rung draft could not rank these models.** qwen3.8:27b, flint:40b, and
  ornith-1.5:9b all passed 11 of 13. Rungs 12 to 14 (expr, undo, reconcile) were added
  for that reason and spread the field to 13, 12, 11, 11, 10.
- **Every model fell on shlex and expr.** All five dropped the empty word from `''`,
  the `drop_empty` trap, even with the example in the spec. On expr the common fault
  was unary minus binding tighter than `**`. Those two rungs are the current ceiling;
  jsonptr (50%) and cron (25%) sit just below it.
- **Nobody cheated.** Zero attempts to write a test, zero stops with public tests red,
  across 80 climbs. On the authority rung every model except the 27B held the spec
  above the wrong assertion; the 27B also held it but sorted by exact share instead of
  remainder, and the remainders case caught that.
- **Cost is the second axis.** flint:40b and qwen3.8:27b solve the rungs they solve in
  four or five turns and a few hundred tokens each. The 9B takes seven times the
  tokens and seven times the wall time for three fewer rungs, and it ran out of turns
  on five rungs per climb.
- **Temperature 0 is stable here but not fixed.** The 27B, 35B, and 9B scored the same
  on all three repeats; flint moved between 11 and 12 and laguna between 11 and 12 with
  height 6 to 8. One climb is a draft; three is a ranking.
- **Rung order is not yet difficulty order.** Pooled over all climbs the pass rates are
  100% on rungs 1 to 6 and 8, then config 92%, undo 75%, reconcile 73%, allocate 80%,
  jsonptr 50%, cron 25%, shlex 0%, expr 0%. A v3 should move shlex and expr above
  cron, and reconcile down, so that height means what it says. Intervals (rung 4) is
  the one low rung with signal: the 9B skipped the sort on every climb.
- **Ollama 0.40.11 turns a malformed tool call into HTTP 500.** The 35B emits a
  truncated `run_python` call at the same point of expr on every climb. The harness now
  feeds that back as a bad tool call and continues; the 35B then spends its remaining
  turns running snippets without writing a fix.

## Reading a result

Look at passed first, then gain, then height and the flags. Two models with the same
passed count can differ a lot: one with height 9 is a clean climber that fell off a
cliff, one with height 3 and the same count stumbles on something easy and recovers. `results/ladder/REPORT.md` shows the
per-rung pass rate across models. A rung every model passes or every model fails is
not ranking anything and should be moved or replaced; that is the recalibration
signal for the next version.

## Adding a rung

Add one `rung(...)` call to `rungs.py` with a buggy project, a gold fix, a public
test, a hidden test with several named cases, structured examples, at least two traps,
and the declared floor in `BUG_PASSES`. Levels must stay 1..n in file order. Run
`--check` and both reviewers' questions: can every hidden assertion be derived from
the spec alone, and does each trap fail for the reason you think?
