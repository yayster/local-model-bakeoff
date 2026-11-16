# Ladder v2 results

Ladder hash 117324ad4fa1, c5d23430e675, f344b4221dbe. Runs with different hashes ran different ladders.

| Model | Hash | Passed | Gain | Height | Peak | Median turns | Tokens | Minutes | Red stops | GPU |
|---|---|---|---|---|---|---|---|---|---|---|
| glm-5.3-flash:cloud | c5d2 | 16/16 | 100% | 16/16 | 16 | 6.0 | 37660 | 4.6 | 0 | - |
| glm-5.3-flash:cloud | 1173 | 16/16 | 100% | 16/16 | 16 | 6.0 | 36285 | 4.2 | 0 | - |
| deepseek-v4.1-flash:cloud | c5d2 | 15/16 | 98% | 11/16 | 16 | 5 | 11043 | 1.0 | 0 | - |
| deepseek-v4.1-flash:cloud | 1173 | 15/16 | 98% | 11/16 | 16 | 5 | 10914 | 1.0 | 0 | - |
| qwen3.8-u:27b | 1173 | 13/16 | 94% | 8/16 | 16 | 5 | 16070 | 12.1 | 0 | - |
| qwen3.8:27b | 1173 | 12/16 | 86% | 8/16 | 15 | 4.5 | 21240 | 15.9 | 0 | - |
| ornith-1.5:35b | f344 | 12/16 | 84% | 8/16 | 16 | 6.5 | 17850 | 3.3 | 0 | 100.0% |
| laguna-xs-2.1:q4_K_M | f344 | 11/16 | 86% | 8/16 | 16 | 8 | 26723 | 3.9 | 0 | 100.0% |
| flint:40b | f344 | 11/16 | 74% | 8/16 | 16 | 5 | 7509 | 1.6 | 0 | 100.0% |
| ornith-1.5:9b | f344 | 10/16 | 72% | 3/16 | 16 | 6.0 | 41009 | 28.9 | 0 | 100.0% |

Passed is rungs whose hidden tests all pass. Gain is hidden cases passed above the cases that already pass on the untouched bug. Height is the highest rung with every rung below it also passed; peak is the highest rung passed at all.

| Model | Hash | 1 pages | 2 slug | 3 semver | 4 intervals | 5 lru | 6 bucket | 7 config | 8 toposort | 9 shlex | 10 jsonptr | 11 cron | 12 expr | 13 undo | 14 reconcile | 15 ranges | 16 allocate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| glm-5.3-flash:cloud | c5d2 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 turns | pass 3/3 length | pass 3/3 | pass 3/3 length | pass 3/3 length | pass 3/3 | pass 3/3 | pass 3/3 |
| glm-5.3-flash:cloud | 1173 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 length | pass 3/3 | pass 3/3 length | pass 3/3 length | pass 3/3 | pass 3/3 | pass 3/3 length |
| deepseek-v4.1-flash:cloud | c5d2 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | 0/3, best 4/5 | pass 3/3 | pass 3/3 | 2/3, best 3/3 | pass 3/3 |
| deepseek-v4.1-flash:cloud | 1173 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | 0/3, best 4/5 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 |
| qwen3.8-u:27b | 1173 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 turns | pass 3/3 | pass 3/3 | 0/3, best 5/6 turns | pass 3/3 | 0/3, best 4/5 | 0/3, best 4/5 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 |
| qwen3.8:27b | 1173 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 turns | pass 3/3 | pass 3/3 | 0/3, best 5/6 turns | pass 3/3 | pass 3/3 | 0/3, best 1/5 turns | 0/3, best 5/6 turns | pass 3/3 | pass 3/3 | 0/3, best 3/4 |
| ornith-1.5:35b | f344 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | 0/3, best 3/6 turns | 0/3, best 4/5 | 0/3, best 4/5 | 0/3, best 2/5 turns,malformed | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 turns |
| laguna-xs-2.1:q4_K_M | f344 | pass 3/3 | pass 3/3 turns | pass 3/3 turns | pass 3/3 turns | pass 3/3 turns | pass 3/3 turns | 2/3, best 6/6 turns | pass 3/3 turns | 0/3, best 5/6 turns | 0/3, best 4/5 turns | 0/3, best 4/5 turns | 0/3, best 4/5 turns | pass 3/3 turns | 2/3, best 5/5 turns | pass 3/3 | pass 3/3 |
| flint:40b | f344 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | 0/3, best 1/6 turns | pass 3/3 | 0/3, best 4/5 | 0/3, best 4/5 | 0/3, best 5/6 | 1/3, best 5/5 | pass 3/3 | pass 3/3 |
| ornith-1.5:9b | f344 | pass 3/3 | pass 3/3 | pass 3/3 | 0/3, best 3/4 | pass 3/3 | pass 3/3 | pass 3/3 | pass 3/3 | 0/3, best 2/6 turns | pass 3/3 | 0/3, best 4/5 turns | 0/3, best 4/5 length,turns | 0/3, best 3/6 turns | 1/3, best 5/5 length,turns | pass 3/3 turns | 2/3, best 4/4 |

Cell legend: `pass`, or repeats passed and the best hidden-case count; `turns` ran out of turns; `length` a reply hit the generation cap; `red` stopped with public tests failing; `wrote-tests` tried to edit a test; `malformed` a tool call the server could not parse; `err` a request failed.

## Per-rung pass rate across models

| Rung | Skill | Pass rate over every climb |
|---|---|---|
| 1 pages | off-by-one, red public test | 100% of 30 |
| 2 slug | edge cases of a one-liner | 100% of 30 |
| 3 semver | parsing and ordering | 100% of 30 |
| 4 intervals | algorithm invariants | 90% of 30 |
| 5 lru | stateful semantics | 100% of 30 |
| 6 bucket | time and float accounting | 100% of 30 |
| 7 config | two files, type coercion | 97% of 30 |
| 8 toposort | graph algorithm, error type, determinism | 100% of 30 |
| 9 shlex | tokenizer state machine | 40% of 30 |
| 10 jsonptr | standard compliance | 80% of 30 |
| 11 cron | two files, dense spec, two bugs | 50% of 30 |
| 12 expr | recursive descent, precedence rules | 20% of 30 |
| 13 undo | nested state, history semantics | 70% of 30 |
| 14 reconcile | two files, greedy matching with tie-breaks | 83% of 30 |
| 15 ranges | non-functional requirement, green tests | 97% of 30 |
| 16 allocate | spec above a wrong public test | 87% of 30 |

A rung every model passes or every model fails tells you nothing; reorder or replace it.
