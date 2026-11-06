# Artwork

The logo, hero, Court illustration and demo plate were generated in ChatGPT with the Visual Post & Carousel Director GPT, then checked by eye for spelling and fidelity. They are not needed to run the engine. Everything else in the README comes from real engine output, via `scripts/build_readme_images.py`.

## Showcase carousels

The three sets in `assets/showcase/` were made in the same GPT, one image per message, with the cover anchoring the rest of the set. `scripts/build_showcase.py` crops them to exactly 1080 x 1350. Each brief named the brand, palette, font direction, visual idea, material and light, plus the exact copy per slide.

| Set | Type direction | Palette | Visual idea |
| --- | --- | --- | --- |
| Maison Verrane | High-contrast refined serif | `#2B1620`, `#E9DCC9`, `#B8915A` | Every slide is lit by a single source |
| Ember & Bun | Brush script over tight condensed capitals | `#D81F26`, `#FFC629`, `#F2E6D0`, `#1A1412` | A boxing poster for a burger |
| Kestrelly | Tight geometric sans, frosted glass cards | `#2A0F6B`, `#7C3AED`, `#E9D5FF`, `#C6F542` | Tabs pile up and clear to a single card |

Example cover brief:

> A five-slide Instagram carousel for a portfolio case study, at the level of a Behance feature by a top creative director. Portrait 4:5. Brand: Maison Verrane, a niche perfume house. Font direction: high-contrast refined serif for headlines, light small tracked capitals for the eyebrow. Palette: deep aubergine #2B1620, warm sand #E9DCC9, antique gold #B8915A. Concept: every slide is lit by a single source, as if the bottle were the only light in the room. Real material: heavy unbranded glass, brushed brass cap, raw silk, warm stone. No text or logo on the bottle. Fixed footer: small tracked serif capitals centered, page marker top right. No lens flare, no glossy plastic, no drop shadows on type, no extra words. Slide 1: eyebrow THE SCENT NOTES, headline Perfume Is / Worn In / Silence, one glowing bottle lower right, a single shaft of window light, huge negative space.

## Logo concept

A friendly crowned king sits inside a speech bubble: Brand plus King, ruling a social feed. The symbols are deliberately generic, a chat bubble, a heart set in the crown and three swipe dots. No platform's trademark is used. The first dot is lime because a carousel starts there.

`scripts/build_brand_assets.py` derives the family from `assets/brand/logo-source.png`:

| File | Use |
| --- | --- |
| `logo-square.png` | Full logo on the brand field |
| `logo-horizontal.png` | Transparent lockup, used in slide footers |
| `mark.png`, `wordmark.png` | Parts with transparent backgrounds |
| `avatar.png`, `favicon.png` | Profile picture and small icon |

Colors: field `#111A17`, ivory `#F4F1E8`, acid lime `#D6F75A`, deep green `#183B32`.

## Prompts

### Logo

> Create the official logo for BRANDKING, an open-source Instagram carousel tool. Square 1:1 canvas, solid flat background #111A17. Concept: a king as the ruler of social media. A single bold, modern, flat vector emblem: a friendly minimal king's head seen from the front, wearing a three-point crown in acid lime #D6F75A, with a neat ivory #F4F1E8 beard, enclosed inside a rounded chat speech bubble shape in ivory so the bubble tail sits at lower left. One small heart replaces the jewel at the centre of the crown, and three small dots under the bubble suggest carousel swipe progress, the first dot lime and the other two ivory. Only generic social symbols: speech bubble, heart, swipe dots. Below the emblem, the wordmark BRANDKING in heavy geometric sans capitals, ivory. Strictly flat two-colour vector look, readable at 64 pixels. No gradients, no 3D, no shadows, no mockup, no platform logos, no extra text, no watermark.

### Hero

> GitHub README hero banner. Wide landscape 2:1, solid background #111A17. Left: the exact BRANDKING emblem small, a big lime badge "100% FREE", the large bold headline "Rule every swipe." and one small line, "Give your brand once. Get premium carousels, forever." Right: the same friendly king, large and flat vector, on a throne made of a fanned stack of portrait 4:5 carousel cards in lime, ivory and deep green. The king holds up a lime price tag reading FREE. Cards hold only abstract shapes. Only generic social symbols. No gradients, no platform logos, no watermark.

### The Court

> Wide 2:1 illustration titled The Court. Six small flat vector characters on one thin lime line that ends in a small crown, each with one prop and a label: Scout with a magnifying glass, Strategist with a compass, Scribe with a quill, Art Director with a paint brush, Critic with a monocle and raised hand, Herald with a small trumpet. The same crowned king stands in the centre. Use only those words of text.

### Demo plate

> A text-free background plate. Portrait 4:5. A calm, moody, photographic still life: one brass crown on a dark green velvet cushion on a dark stone table, soft window light from the left. The crown sits in the upper half and the lower half is plain dark stone. No text, no lettering, no logos, no watermark, no people.
