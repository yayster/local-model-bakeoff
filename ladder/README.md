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

Every result file carries a hash of the specs, bugs, tests, and turn budgets. Two
results with different hashes ran different ladders and do not belong in one table.

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
