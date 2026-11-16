# Hermes's review of the first report, 3 November 2026

Verbatim, as David pasted it into the session after the first bake-off report.
It is the review that turned a two-model comparison into a harness fix. The one
claim the session corrected: height is not path-dependent; it is the rung below
the first failure, and deepseek failed rung 12 on every climb.

---

☤ Hermes
Good report. Two things in it are stronger than the headline, and one is a hole I'd want plugged before you crown anyone.

Verdict, per axis
- Ladder: the gap is one rung. That is not "wide." What's wide is cost and latency — 11k vs 38k tokens, 1.0 vs 4.6 min. So the honest summary is "deepseek is 3.5x cheaper at essentially equal ladder performance; glm is meaningfully better at the quiz and reasoning under a cap." Not "one is stronger, one is cheaper."
- Height 16 vs 11 with 15/16 passed suggests deepseek took a different/shorter route rather than failing to climb. Worth checking whether height is path-dependent before reading anything into it.

The hole: your noise floor is as big as your signal
Rung 15 is a coin flip inside a 1.98–2.76 s spread, and the measured difference between the models is one rung. You cannot rank two models on a ladder whose own variance equals the delta. Worse, and this is the bit I'd put in the writeup: if deepseek's fix was byte-identical across all three climbs, those climbs are not three independent trials — effective n is closer to 1, and the only randomness in the whole six-climb set is the grader's clock. That reframes everything: "15/16 across three climbs" is one behavior measured three times, and the single miss you're debating is probably the timer, not the model.

So the reliable signals are:
- expr, reproducible on every climb — a real, generalizable gap: handles the obvious case, misses the spec sentence. That's a "first plausible fix, never reconsiders" fingerprint, and the fixed five-turn pattern is exactly what would cause it. Testable: add a rung that needs a second debug cycle after a failed test. My money says deepseek drops it.
- The 3000-token reasoning leak on glm: reproducible, and it's a deployment cost, not a style quirk. It's most of why glm is 3.5x more expensive per climb.
- Quiz formatting misses are irrelevant on the ladder but decisive for anything bot-facing or parser-facing — bold runs and trailing code fences are precisely what breaks Telegram rendering and structured comments.
- Ceiling 5/5 vs 4/5 and quiz 6 vs 9 point in opposite directions on 10 items each. Small n; don't over-read either.

What I'd do
1. Fix rung 15 properly — move the timing case inside the worker or raise the budget — accept the hash change, and re-run both. Then keep both hashes' results side by side. A known coin-flip rung poisons every future bake-off, not just this one.
2. Don't pick one. Route: deepseek-v4.1-flash as the default worker (cheap, fast, tool-disciplined — it cleared shlex and cron, which is the most relevant signal for our infra work); glm-5.3-flash escalated for planning, review, ambiguous specs, and anything where the output is read by a human or a strict parser.
3. Note it as a per-climb spend decision, not a capability one — at 4.6 min and 38k tokens per climb, glm is ~4.5x the wall time in every cron heartbeat that uses it.
