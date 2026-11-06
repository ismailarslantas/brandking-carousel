# Brandking Carousel

Read `AGENTS.md`; it holds the commands and rules. All repository-facing text is English. Client copy keeps its own language only when the brief asks for it.

The `/carousel` skill runs the brief-to-delivery workflow, with the specialists in `.claude/agents/`. Read `docs/PLAN.md` before changing the plan format. Creative guidance lives in `guides/`, which ports the Visual Post & Carousel Director GPT in full; keep guide changes consistent with `skills/brandking-director/SKILL.md`.

A non-empty output directory is rejected on purpose. Never delete a user's delivery to rerun a command; choose a new folder.
