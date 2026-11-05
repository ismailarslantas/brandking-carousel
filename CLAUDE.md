# Brandking Carousel

All repository-facing text must be English. Preserve client content language only when explicitly requested.

This project renders user-authored or assistant-authored carousel plans using Python, Pillow, FontTools and bundled OFL Figtree. No hosted model, API secret, subscription, browser automation or network request is needed to render after dependencies are installed.

Read `docs/PLAN.md` before changing the JSON format. Creative guidance lives in `guides/`. The `/carousel` skill implements the brief-to-delivery workflow. Profile analysis is performed by the assistant from supplied visual references, not by the deterministic renderer.

Run `python -m unittest discover -s tests -v` and `python carousel.py --output outputs/<fresh-name>` after meaningful renderer changes. A nonempty output directory is rejected intentionally. Never delete a user's delivery to rerun a command.

Assets must live within the project directory; `private/` is ignored by Git. Do not commit customer briefs or image assets without explicit publication authorization. Never claim viral performance, profile access, cross-platform test success or visual review without evidence.
