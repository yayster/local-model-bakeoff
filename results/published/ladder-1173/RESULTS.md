# Ladder results, hash 117324ad4fa1

Five models on the same 16-rung coding ladder (73 hidden test cases), same grader, same protocol (temperature 0, seed 0).

| model | where it ran | rungs passed | hidden cases | seconds per climb | output tokens | repeats |
|---|---|---|---|---|---|---|
| qwen3.8:27b (public download) | local, llama.cpp, two 16 GB cards | 12 of 16 | 66 of 73 | 952 | 21,240 | 3 |
| qwen3.8-u:27b (the previous house model) | local, llama.cpp, two 16 GB cards | 13 of 16 | 70 of 73 | 725 | 16,070 | 3 |
| Qwen3.8-Flash-Next IQ3_XXS on Strata | local, Strata, one 16 GB card | 15 of 16 | 72 of 73 | 240 | 18,891 | 1 |
| deepseek-v4.1-flash | cloud | 15 of 16 | 72 of 73 | 62 | 10,914 | 3 |
| glm-5.3-flash | cloud | 16 of 16 | 73 of 73 | 252 | 36,285 | 3 |

Notes:

- The Strata row is a single climb; the others are the protocol's three repeats. Treat a one-rung difference between Strata and the rows beside it as within noise until it is repeated.
- Seconds are wall-clock for one climb and depend on the serving setup as much as on the model: the two local 27B rows shared their server with other clients and had no prompt cache for the harness; the cloud rows include network time.
- The local rows ran on one machine with two 16 GB consumer GPUs. The 27B models used both cards; the Strata model used one.
- glm-5.3-flash's result carries the caveat described in `ladder/README.md` (its reasoning leaks into answers on the classic sections; the ladder score is unaffected).
- Per-rung transcripts for the Strata climb are in the folder beside this file. Transcripts for the other four are under `results/bundles/bakeoff-story-2026-11-03/results/ladder/`.
