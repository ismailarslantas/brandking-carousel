# What we studied before building 2.0

In November 2026 we searched GitHub for Instagram carousel generators, agent skills and workflows, sorted by stars, then read the READMEs of twelve projects. We read landing pages and file listings, not every line of source, and did not run them. Star counts move, and these were correct on the day we looked. No code was copied; everything here was written for this repository.

| Project | Stars | Approach | The idea worth noting |
| --- | --- | --- | --- |
| [sergebulaev/instagram-skills](https://github.com/sergebulaev/instagram-skills) | 762 | Agent skills, optional publishing | Approve before publishing; a humanizer that admits its limits |
| [Hainrixz/open-carrusel](https://github.com/Hainrixz/open-carrusel) | 510 | Next.js app, Claude writes HTML | Preview and export share one renderer |
| [itchernetski/threads-carousel-claude-skill](https://github.com/itchernetski/threads-carousel-claude-skill) | 120 | React template | Style as independent axes |
| [Upload-Post/viraloop](https://github.com/Upload-Post/viraloop) | 85 | Website to generated slides to autopost | An analytics and learnings loop |
| [charlesdove977/carousel-builder](https://github.com/charlesdove977/carousel-builder) | 47 | Higgsfield and Canva | Check copy budgets before spending image credits |
| [dean9703111/ig-card-generator](https://github.com/dean9703111/ig-card-generator) | 15 | Markdown DSL, Puppeteer | Lint before build; flags unverified numbers |
| [TheMattBerman/slideshow-kit](https://github.com/TheMattBerman/slideshow-kit) | 14 | Brand DNA, image API | The run packet is the deliverable |
| [cth9191/ref-deck](https://github.com/cth9191/ref-deck) | 9 | Reference deck skeleton | Separate approvals for copy and visuals; three covers first |
| [bleakbelladonnals/elec-sheep-longform](https://github.com/bleakbelladonnals/elec-sheep-longform) | 9 | SVG layers | Text never goes inside the raster |
| [johnnyang0612/bearcarousel](https://github.com/johnnyang0612/bearcarousel) | 3 | Pillow with a pixel audit | Measures rendered output and blocks on red |
| [nopefallacy/carousel-generator-skill](https://github.com/nopefallacy/carousel-generator-skill) | 1 | Prompt packs | Anchor later images to slide one |
| [social-media-skills/instagram-carousel-skill](https://github.com/social-media-skills/instagram-carousel-skill) | 0 | Pillow, spec-driven | Slide two as a second cover; metrics read back |

## Patterns across them

- Most projects are agent skills: the agent writes and a script or model renders.
- Rendering splits into headless browsers, Pillow, image models with text baked in, Canva and SVG.
- Approve-before-publish is common, and auto-posting is the exception.
- Quality checks mostly look at the spec or the copy. Few look at the finished image.

## The gaps we built 2.0 around

| Gap we saw | What Brandking does |
| --- | --- |
| Image models misspell, and few projects verify the output | Plates stay text-free and the engine sets all type, so spelling comes from the plan ([guide](../guides/08-image-plates.md)) |
| Contrast is rarely measured on real pixels, especially over photos | Geometry and text are drawn separately, so each line is measured against the exact pixels behind its glyphs |
| Results rarely feed the next post | The ledger stores a hypothesis with the results, and refuses to rank small groups |
| Brands get re-described for each post | Reusable brand kits with voice rules that block delivery |
| Slides are designed one at a time | The Crown Thread crosses each seam, and the audit measures that it lines up |
| Agents can declare their own work finished | Gates read files on disk, and an isolated Critic reviews the slides cold |

## What we chose not to do

- **No auto-posting.** Publishing stays a human decision, and we did not want a third-party posting service in the core.
- **No headless browser.** A Chromium download is a heavy cost for a tool that should run anywhere with Python.
- **No reach scores.** We cannot predict reach, so the cover ranking is labelled an editing aid.
- **No scraping.** The engine never touches Instagram. You supply screenshots and type in your own numbers.
