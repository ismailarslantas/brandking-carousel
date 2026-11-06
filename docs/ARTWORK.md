# Artwork

The logo, hero, Court illustration and demo plate were generated in ChatGPT with the **Görsel Post & Carousel Direktörü** (Visual Post & Carousel Director) GPT, then checked by eye for spelling and fidelity. They are not needed to run the engine. Everything else in the README comes from real engine output, via `scripts/build_readme_images.py`.

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

> GitHub README hero banner. Wide landscape 2:1, solid background #111A17. Left: the exact BRANDKING emblem small, then the large bold headline "Rule every swipe." and one small line, "The carousel engine that measures its own pixels." Right: the same friendly king, large and flat vector, on a throne made of a fanned stack of portrait 4:5 carousel cards in lime, ivory and deep green. A thin lime wavy line runs through all the cards and ends in a small crown. Cards hold only abstract shapes. Only generic social symbols. No gradients, no platform logos, no watermark.

### The Court

> Wide 2:1 illustration titled The Court. Six small flat vector characters on one thin lime line that ends in a small crown, each with one prop and a label: Scout with a magnifying glass, Strategist with a compass, Scribe with a quill, Art Director with a paint brush, Critic with a monocle and raised hand, Herald with a small trumpet. The same crowned king stands in the centre. Use only those words of text.

### Demo plate

> A text-free background plate. Portrait 4:5. A calm, moody, photographic still life: one brass crown on a dark green velvet cushion on a dark stone table, soft window light from the left. The crown sits in the upper half and the lower half is plain dark stone. No text, no lettering, no logos, no watermark, no people.
