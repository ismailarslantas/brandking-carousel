# Changelog

## 2.1.0

The full Visual Post & Carousel Director GPT moves into this repository, and Brandking now installs as a Codex plugin that designs with ChatGPT image generation. Give your brand once, and it is never asked for again.

### Added

- **Brand memory.** `brand remember`, `recall`, `list` and `forget`. Name, colors, fonts, visual structure, logo and references are saved in `~/.brandking` on the first use. A passing render saves automatically, and plans can then leave `brand` out.
- **Premium craft standard.** `guides/09-premium-craft.md`: one visual idea per deck, marks of premium work, how to direct an image model, and a critic's test. Art-directed image slides are now the director's first choice.
- **Showcase.** Three art-directed carousels in `assets/showcase/`.
- **Codex plugin.** Install with `codex plugin marketplace add`. Includes `$brandking-director`, `$brandking-brand`, `$brandking-learn` and six custom agents.
- **ChatGPT image generation.** The director uses Codex's built-in image tool. It never falls back to an API key.
- **Plan gate.** Image generation requires a stated ChatGPT Plus plan or higher. `brandking gate` refuses Free and Go. It records what the user states and cannot verify a subscription.
- **The whole GPT in English.** Ten fixed rules, eight modes, nine palette rotations, five footer locks, three voices, sixteen headline formulas, over fifty tools, nineteen compositions, grid and story playbooks, and matching by message type and sector.
- **New formats.** `post`, `series` and `grid`, with two-dimensional neighbour checks for grids, a grid map and reverse upload instructions.
- **`brandking fit`.** Brings a generated image to an exact size, refuses crops that could cut text, and can place a logo.
- **`brandking prompts`.** Builds plate or full-design prompts from the plan's real copy.
- **`brandking doctor`.** Reports Codex sign-in without touching credentials. A plan it cannot verify is reported as skipped.
- **Text read-back.** Full designs need a letter-by-letter `text-check.md`.

### Changed

- The engine now works from any folder: project files first, then bundled fonts and kits. `scripts/bk.py` sets up its dependencies on first use.
- `background` accepts `focus_y` to choose which part of a picture survives the crop.
- `visual-prompts.md` now contains structured prompts for image tools.

### Not carried over

The private reference images behind the GPT, since they show other brands' work. Example headlines were rewritten as new English lines.

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
