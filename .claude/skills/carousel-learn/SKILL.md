---
name: carousel-learn
description: Log the results of a posted carousel and decide what to test next from the Brandking ledger. Use when the user shares carousel Insights or asks what is working.
---

1. Ask for the numbers from Instagram Insights, about seven days after posting: reach, saves, sends, likes, comments, follows. Never estimate a missing number; leave it out.
2. Read `meta` from the run's `plan.json`, then run:
   `python -m brandking ledger add <id> --hook-type <type> --format <format> --house <house> --hypothesis "<text>" --reach N --saves N --sends N --likes N --comments N --follows N`
3. Run `python -m brandking ledger report` and show the table.
4. Read it honestly. Groups under five posts are flagged "too few". Say they are too few. Results are associations; topic, timing and audience also move them.
5. Propose one next test that changes one variable, written as a hypothesis the next plan can carry in `meta.hypothesis`. Do not rewrite the brand's strategy because of one post.
