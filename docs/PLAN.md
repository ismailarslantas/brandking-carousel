# Plan format

A plan is one JSON file that describes a whole carousel, post, series or grid. `examples/` holds a complete example of each, and `schemas/plan.schema.json` gives editors autocomplete. Paths are relative to your project folder, the one you run the command from, even when the plan lives in `private/`. Files that are not there are looked up in the engine, which supplies the fonts and demo kit. Paths cannot leave these two folders.

## Top level

| Field | Required | Meaning |
| --- | --- | --- |
| `brand` | no | Leave out or use `"@memory"` for the last saved brand, `"@slug"` for another saved brand, a kit path, or an inline object |
| `format` | no | `carousel` (default), `post`, `series` or `grid` |
| `caption` | yes, except series and grid | Post caption, up to 2,200 characters. In a series or grid each slide has its own `caption` |
| `slides` | yes | Carousel 3-20 (lint suggests 5-10), post 1, series 2-10, grid exactly 9 |
| `promise` | recommended | `{"text": "...", "paid_on": 5}`: what the cover promises and which slide pays it off |
| `meta` | recommended | `concept`, the deck's one-sentence visual idea, plus `hook_type`, `format` and `hypothesis` for the ledger |
| `cover_options` | recommended | At least three headlines for `brandking covers` |
| `sources` | when claims exist | A list of sources that covers the whole plan |
| `product_variant_exception` | no | `true` allows repeated layouts and palette roles for a deliberate product range |

## Formats

| Format | Variety rules | Counter and thread | Extra files |
| --- | --- | --- | --- |
| `carousel` | Adjacent slides change layout and palette role | Yes | `previews/swipe-strip.jpg` |
| `post` | None | No | |
| `series` | Same as carousel. Each post has a caption and may have a CTA | No | |
| `grid` | Posts that touch sideways or vertically never share a palette role. At least four roles. A layout appears at most twice | No | `previews/grid-map.jpg`, reverse upload order |

The eight-word limit applies only to a carousel's cover. Elsewhere the limit is 25 words.

## Brand memory

Give a brand once with `brandking brand remember`, or just use it in a passing `render`, and it is saved in `~/.brandking` (or `BRANDKING_HOME`) on this computer, with copies of its files. Every later plan can leave `brand` out. Inside a sandbox that blocks that folder, it is saved in `.brandking/` in the project instead. Use `brand recall`, `brand list` and `brand forget`. `--no-remember` skips saving on a render. Example brands with `"demo": true` are never saved.

## Brand fields

`brand.json` holds the following. A shareable kit is the same file in any folder, created with `brandking brand init`.

| Field | Meaning |
| --- | --- |
| `name` | Required. Used in the footer when no logo is set |
| `primary`, `accent`, `dark`, `light`, `warm` | Required six-digit HEX colors |
| `house` | `sovereign`, `editorial` or `poster` |
| `font`, `title_font` | Optional font files that override the house. Check you may redistribute them |
| `font_name`, `title_font_name` | Font names used in image prompts, when there is no file |
| `visual_structure` | How the brand should look, in a sentence or two. Leads every image prompt |
| `references` | Saved reference images the director looks at |
| `logo` | Optional image for the footer |
| `handle` | Optional text at the right of the footer |
| `footer` | `split` (lock B: logo left, handle right) or `center` (lock A). Locks C-E need a full-design image |
| `thread` | `false` turns off the Crown Thread |
| `visual_style` | Sentence used in the image prompt pack |
| `voice` | `tone`, `banned_words`, `allowed_words`, `max_hashtags` |
| `evidence` | Where the tokens came from |

## Slides

Every slide needs `layout`, `rotation`, `headline`, `alt` and `visual_prompt`. `rotation` is the palette role: `solid`, `light`, `dark` or `warm`.

Optional on any slide: `eyebrow`, `emphasis` (words from the headline to highlight), `source`, `background` with `focus_y`, and `caption` in a series or grid.

| Layout | Extra fields | Notes |
| --- | --- | --- |
| `cover` | `image` | Swipe card graphic, or an uncropped product image. No body |
| `statement` | `body` or `image` | Open editorial composition |
| `split` | `items` (2), `body` | Two panels |
| `steps` | `items` (3), `body` | Numbered rows. Each item fits one line |
| `checklist` | `items` (3), `body` | Ticked rows |
| `timeline` | `items` (4) | Connected points |
| `versus` | `left_label`, `right_label`, `items` (3) | Items are written `"left \| right"` |
| `myth` | `myth`, `fact` | Struck-through belief and highlighted correction |
| `stat` | `value`, `source`, `body` | Source is required and printed on the slide |
| `quote` | `attribution`, `source` | The headline holds a real quote, up to 18 words |
| `bento` | `items` (4) | Cells of varied size |
| `photo` | `background`, `focus_y`, `panel`, `body` | Full picture above the thread. `focus_y` from 0 to 1 picks which part survives the crop (0 keeps the top). `panel: false` sets type directly on it |
| `closing` | `body`, `cta` | Summary and the one call to action |

## Word limits

The cover holds 8 words. Other slides hold 25, or 30 for `versus` and `quote`. Headlines hold 7, or 18 for `quote`. The footer and page counter do not count. Headlines step down a fixed size ladder when needed, then ask for shorter copy. Nothing shrinks silently.

## What each stage checks

**Structure (`plan.py`), always blocking.** Field types, layout capabilities, word limits, glyph coverage for every character, asset paths inside the project, adjacent slide variety, four palette roles and three layouts per deck.

**Copy lint (`lint.py`).**

| Blocks delivery | Warns |
| --- | --- |
| `unsourced_number`, `hype_claim`, `brand_voice`, `placeholder`, `one_cta` (more than one), `promise_payoff` (invalid slide), `caption_length` | `ai_tell`, `self_praise`, `comment_bait`, `generic_cover`, `cover_about_brand`, `slide_two`, `cta_verb`, `alt_text`, `long_sentence`, `em_dash`, `caption_opening`, `hashtags`, `text_in_plate`, `deck_length`, `promise_payoff` (missing) |

**Pixel audit (`audit.py`), on the rendered image.**

| Check | What is measured |
| --- | --- |
| `measured_contrast` | Each line's color against the real pixels behind its glyphs (5th percentile). Needs 3:1 for large type, 4.5:1 otherwise |
| `safe_area` | Text bounds inside the 80 px margin |
| `footer_collision` | Content text above the footer |
| `phone_legibility` | Type at or above the size floor, 28 px, or 24 px in the footer |
| `grid_crop` | Cover text survives the 3:4 profile grid crop |
| `text_collision` | Text blocks do not overlap |
| `cover_scale` | Cover headline strong enough for a thumbnail (warning) |
| `density` | Share of the slide covered by text (warning) |
| `thread_seams` | The Crown Thread meets within 3 px on both sides of each seam |
| `visual_rhythm` | Adjacent slides differ at thumbnail size (warning) |

## What is not checked

Nothing here judges persuasion, taste or whether a claim is true. `unsourced_number` confirms a source was named, not that it says what you claim. It only detects common number patterns, so a claim in words can pass. Reading these limits is part of the job: visual review stays `pending` until `brandking signoff` records a real review.

The engine's layouts render one size, 1080 x 1350. `brandking fit` brings generated images to 1080 x 1350, 1080 x 1920 or 1080 x 1080. The engine cannot read text inside a generated image, which is why a full design needs a separate read-back. It does not log in to Instagram, read profiles, post, or call any image service; image generation happens in the agent's own tool. PNG is the authoritative export. SVG text stays editable, though fonts can render differently in other editors. Exact pixels can vary between operating systems.
