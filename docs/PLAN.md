# Plan format and supported capabilities

Use `examples/demo.json` as the complete editable example. Paths are relative to the repository root, even when a plan is in `private/`.

## Brand

Required fields: `name`, `primary`, `accent`, `dark`, `light`, `warm`. Colors use six-digit HEX. Optional fields: `handle`, `font`, `title_font`, `logo`, and `evidence`. The default font is bundled Figtree. A separate title font supports a serif heading with a sans body; user-provided fonts need suitable glyph coverage and redistribution rights if included in a delivery. The renderer does not download fonts.

## Slides

Each slide requires `layout`, `rotation`, `headline`, `alt`, and `visual_prompt`. Optional fields: `eyebrow`, `body`, `items`, `image`, and `cta`.

| Layout | Content | Visual behavior |
| --- | --- | --- |
| cover | Headline; optional image | Overlapping graphic cards or a full, uncropped product photo |
| statement | Headline and body, or an image | Open editorial composition |
| split | Headline, optional short body, up to two items | Side-by-side comparison panels |
| steps | Headline, optional short body, up to three items | Numbered horizontal cards |
| checklist | Headline, optional short body, up to three items | Compact review checklist |
| closing | Headline, body, optional CTA | Summary and one action panel |

Rotations: `solid` uses primary; `light` uses light; `dark` uses dark; `warm` uses warm. These are four roles within a brand palette, not four unrelated brand colors. Colors can be changed to fit the user's actual identity. A `product_variant_exception: true` top-level field explicitly permits repeated composition and palette roles for a product family. Normal runs require four roles, three layouts and no adjacent repetition.

Use at most seven words in a headline. A cover has at most eight editorial words total; other slides 25. Footer and page counter are excluded. The renderer rejects overflow instead of silently reducing type size. Item cards need short text to fit one line; split panels support wrapped text. The `body` field is not supported on a cover. Images are supported in cover or statement, with no body or CTA on image statements to protect the image zone. Other layouts reject an image.

Top-level `caption` is required. `sources` is a list of source descriptions/URLs for factual claims. The renderer stores sources but does not fact-check them. `visual_prompt` describes the requested visual, and is exported as a production handoff; it does not call an image generation API. The available layouts are a starting library, not an implementation of every conceptual composition in the creative guides.

## Outputs and limitations

PNG is the authoritative 1080×1350 export. SVG retains editable text and embeds fonts and images; font rendering can differ in external SVG editors. The delivery also includes a portable Python recipe with the plan and referenced assets. Only include fonts/assets whose licenses permit sharing. Bundled Figtree includes its OFL license.

QA measures text bounds, glyph coverage, word counts, solid-color contrast and sequence rules. It does not infer persuasion, guarantee reach, inspect photo contrast or verify factual claims. Visual review remains a separate human/assistant step. No screenshot scraping, Instagram login, automated posting or paid image service is included.
