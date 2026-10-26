# Local model bake-off

The suite behind the 2026-10-25 comparison of `qwen3.8:27b`, `flint:40b`, `ornith-1.5:35b`, and `laguna-xs-2.1:q4_K_M` on a machine with two 16 GB GPUs.

It talks to Ollama's `/api/chat`. Point it at any Ollama that has the tag pulled.

## Run

```bash
python3 bakeoff.py http://127.0.0.1:11434 qwen3.8:27b
```

A single section:

```bash
python3 bakeoff.py http://127.0.0.1:11434 flint:40b --sections speed,quiz
python3 bakeoff.py http://127.0.0.1:11434 ornith-1.5:35b --sections ceiling
python3 repair/loop.py --check
python3 repair/loop2.py --check
python3 ladder/run.py --check
```

`--check` grades the bundled bugs and the gold fixes. It does not call a model. All three should print `fails 0`.

## What it scores

| Section | What | Score |
|---|---|---|
| `speed` | "Count from 1 to 80", three times, 128 token cap | Median decode tok/s |
| `quiz` | 8 short answers, one `date_diff` tool call, one in-place `second_largest` fix | Last line, 10 items |
| `ceiling` | Five long traces from `tasks/ceiling.json` | Last line, 5 items. A length stop is retried once at 6000 tokens |
| `repair` | Eight Python repairs. The model gets `read_file`, `write_file`, and `run_tests`. Five turns | Hidden tests |
| `ladder` | Eight harder repairs. Six turns. Public tests already pass on the bug | Hidden tests |
| `ladder2` | Sixteen rungs of rising difficulty, five tools, traps and a self-check. See `ladder/README.md` | Height, gain, flags |

Settings match the bake-off: `think` false, temperature 0. The request does not set `num_ctx`, so the server's context window is the seat. The published run used 131072.

A right value wrapped in `\boxed{}` or bold counts as a miss. That is how Laguna and Ornith lost short items they had otherwise solved.

## Results

Quiz, ceiling, and speed land in `results/<model>.json`. Repair logs land in `repair/results/`. Ladder v2 results and transcripts land in `results/ladder/`, and `python3 ladder/report.py` folds them into one table. Those directories are gitignored.

## Seat notes from the run this suite repeats

All four models loaded at 100% GPU on two 16 GB cards when nothing else was resident. A 3 GB allocation already on one card is enough to push the dense 27B partly onto the CPU. Record the processor column. A run that is not `100% GPU` is a different seat.
