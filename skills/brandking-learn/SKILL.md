---
name: brandking-learn
description: Log the results of a posted Instagram carousel or post and decide what to test next from the Brandking ledger. Use when the user shares Insights numbers or asks what is working.
---

# Brandking ledger

`ROOT` means the folder two levels above this file. Run commands from the user's project with `python "ROOT/scripts/bk.py" <command>`.

1. Ask for the numbers from Instagram Insights, about seven days after posting: reach, saves, sends, likes, comments, follows. Never estimate a missing number; leave it out.
2. Read `meta` from the run's `plan.json`, then run: `ledger add <id> --hook-type <type> --format <format> --house <house> --hypothesis "<text>" --reach N --saves N --sends N --likes N --comments N --follows N`
3. Run `ledger report` and show the table.
4. Read it honestly. Groups under five posts are labelled too few, so say that. Results show association, not cause: topic, timing and audience also move them.
5. Propose one next test that changes one variable, written as a hypothesis the next plan can carry in `meta.hypothesis`. Do not rewrite a brand's strategy because of one post.
