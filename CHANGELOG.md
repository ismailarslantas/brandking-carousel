# Changelog

## 2.0.0

A rebuild based on [a study of twelve carousel projects](docs/RESEARCH.md).

### Added

- **Pixel audit.** Contrast is measured against the real pixels behind each line of text. Also checks the safe area, footer collisions, text collisions, type floors, the 3:4 grid crop, seams, rhythm and density.
- **Crown Thread.** One line crosses every seam and ends in a crown. The audit measures that it lines up.
- **Copy lint.** Blocks unsourced numbers, hype, placeholders, brand-banned words and multiple calls to action. Warns on machine-sounding phrases, comment bait, generic covers and thin alt text.
- **Three houses.** Sovereign (Figtree), Editorial (Fraunces) and Poster (Anton).
- **Seven new layouts.** Timeline, versus, myth, stat, quote, bento and photo, for thirteen in total.
- **Brand kits.** Reusable folders with palette, house and voice rules, plus `brand init` and `brand check`.
- **Cover comparison.** `brandking covers` renders options side by side.
- **Run gates.** `brandking run status` reports progress from files on disk. `brandking signoff` records visual review.
- **Results ledger.** Local log of hypotheses and Insights numbers, which refuses to rank groups under five posts.
- **The Court.** Six specialist agents, plus `/carousel-brand` and `/carousel-learn` skills, and `AGENTS.md` for other tools.
- **More delivery files.** PDF deck, swipe strip, grid tile, image prompt pack and upload checklist.
- **New identity.** The crowned king logo, plus avatar, wordmark and lockup assets.

### Changed

- The single script became the `brandking` package with a CLI and `--json` on every command. `python carousel.py` still works.
- Text is drawn at twice the size and scaled down, so corners and curves are smooth.
- Contrast is no longer computed from declared colors. It is measured after rendering.
- A failed audit still writes the folder for inspection but withholds `carousel.zip`.
- Slide limits widened to 3-20, with lint suggesting 5-10.

### Plan compatibility

Plans with an inline `brand` still work with the same fields. Slide content must now also pass copy lint. CTA rows and panels moved up slightly to make room for the thread; set `"thread": false` in the brand to remove it.
