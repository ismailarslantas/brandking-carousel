# Use Brandking in Codex

Brandking installs as a Codex plugin. In Codex it acts as a creative director: it writes the idea, copy and placement, designs with **ChatGPT image generation**, sets type with the local engine and checks the result.

## Requirements

| You need | Why |
| --- | --- |
| **ChatGPT Plus or higher** (Plus, Pro, Business, Edu or Enterprise) | Image generation in this workflow is built for these plans. Brandking's gate refuses Free and Go |
| **Codex, signed in with ChatGPT** | The image tool runs inside Codex under your plan, with no API key |
| **Python 3.10 or newer** | Runs the local engine. Two packages install automatically on first use, which needs network access once |

Images draw on your plan's Codex allowance, several times faster than ordinary turns. Check `/status` in Codex or your usage dashboard, particularly before a nine-post grid. OpenAI sets those limits and can change them.

### What the plan gate does and does not do

The director asks which plan you have and records your answer in `.brandking/chatgpt-plan.json`, using `brandking gate confirm`. It refuses Free and Go, and it stops the workflow before any image call.

**It records what you state; it cannot verify a subscription.** It does not read your Codex credentials, and this is open-source code anyone can change. What an account can really do is decided by OpenAI. Rendering, auditing, writing copy and writing prompts need no plan.

The director never uses the API-key fallback in Codex's image tool, since that would bill API rates instead of your plan.

## Install

In a terminal:

```bash
codex plugin marketplace add ismailarslantas/brandking-carousel
```

```bash
codex plugin add brandking@brandking
```

Or run `codex`, type `/plugins`, and install **Brandking** from the list. The ChatGPT desktop app can also install it once the marketplace is added. Start a new session afterwards so the skills load.

Check the setup from your project folder:

```bash
codex login status
```

It should say you are logged in using ChatGPT. To update later:

```bash
codex plugin marketplace upgrade brandking
```

The Codex IDE extension does not support plugins, according to OpenAI's documentation, so use the CLI or the desktop app.

## Use it

Open your own project folder and ask:

```text
$brandking-director Build a six-slide carousel about choosing a handmade cup.
```

**The first time,** it asks once for your brand, colors, fonts and visual structure, plus a logo and references if you have them. It saves them in `~/.brandking` with copies of your files, and **never asks again**, in any project. Later you only give the topic. To change something, say so, and only that field changes.

```bash
brandking brand list
```

If Codex's sandbox blocks that folder, the brand is saved in `.brandking/` in the current project and the director tells you. Approving the command once outside the sandbox makes it available everywhere.

```text
$brandking-director Set up a nine-post grid for this product. private/assets/product.png
```

```text
$brandking-director Suggest post copy and placement for this photo.
```

| Skill | Use for |
| --- | --- |
| `$brandking-director` | Carousels, single posts, series, nine-grids, stories, photo-to-post, headline restyling and copy |
| `$brandking-brand` | Saving, changing, listing or forgetting a brand |
| `$brandking-learn` | Logging Insights numbers and choosing the next test |

Keep client files in `private/`. Brandking creates `.brandking/` for its setup. Add both to `.gitignore` if your project is a Git repository.

## How images are made

For each post the director chooses one of three paths.

| Path | Best for | Who sets the text | How it is checked |
| --- | --- | --- | --- |
| **Full design** | Covers and key moments, where type and picture interact. The most art-directed result | The image model | A required letter-by-letter read-back, saved to `text-check.md` |
| **Plate** | Long copy, numbers, prices, languages with special characters | The engine | Measured contrast, safe area, collisions, spelling from the plan |
| **No image** | Type-led slides | The engine | Same as plate |

Image models can still misspell, so a full design that fails its read-back is regenerated or moved to a plate. The director holds every deck to [the premium craft standard](../guides/09-premium-craft.md).

The engine prepares and finishes the images:

```bash
brandking prompts plan.json --mode plate
brandking fit raw.png --output post.png --format post --logo logo.png
```

`fit` produces exactly 1080 x 1350, 1080 x 1920 (`--format story`) or 1080 x 1080 (`--format square`). It refuses a crop that could cut text unless you pass `--allow-crop`, which is meant for text-free plates. The built-in image tool does not guarantee an exact pixel size, so always run this step.

In a clone of this repository, the same specialists are also available as Codex custom agents in `.codex/agents/`.

## What has been tested

On Windows 11 with Codex CLI 0.167.0: installing the plugin into a clean Codex home, first-run setup with a Python that had no packages, `$imagegen` under a real ChatGPT Plus sign-in in the normal sandbox with correct Turkish text, then `fit`, `check`, `render` and brand memory on those images.

Not yet tested as one uninterrupted session: on that machine Codex's sandbox denied `python.exe` (see Troubleshooting), so the engine steps ran separately. The approval prompt, the desktop app, macOS and Linux have not been exercised.

## What was ported from the GPT

This plugin carries over the **Visual Post & Carousel Director** GPT, translated into English and extended.

| The GPT | Here |
| --- | --- |
| Identity, ten fixed rules, modes, brief and delivery format | [guides/01-director.md](../guides/01-director.md) |
| Canvas, footer locks, type branches, palette rotation R1-R9, reference palettes | [guides/02-visual-dna.md](../guides/02-visual-dna.md) |
| Three voices, sixteen headline formulas, CTA library, caption structure | [guides/03-copywriting.md](../guides/03-copywriting.md) |
| Nine-grid architecture, carousel flows, story zones | [guides/04-carousel.md](../guides/04-carousel.md) |
| Signature tools and nineteen compositions | [guides/05-visual-tools.md](../guides/05-visual-tools.md) |
| Message and sector matching, no-photo tools | [guides/06-topic-matching.md](../guides/06-topic-matching.md) |

Not carried over: the private reference images the GPT was trained on, since they show other brands' work. Example headlines were rewritten as new, invented English lines.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `gate check` fails | No plan stated yet | Run `gate confirm --plan <plan>`, or let the director ask |
| Image tool unavailable | Signed in with an API key, a plan without image generation, or limits reached | Run `codex login` with ChatGPT and check usage. The director will not switch to an API key |
| `python` says "Access denied" in Codex | On Windows, Python installed for one user under `AppData` is not readable by Codex's sandbox account | Approve the command when Codex asks to run it outside the sandbox. Installing Python for all users may also help |
| First run cannot install packages | The sandbox blocks network access | Approve that one step, or run `python -m pip install -r requirements.txt` yourself |
| "Saved for this project only" | The sandbox blocked `~/.brandking` | Approve the command to run outside the sandbox once, so the brand is available in all your projects |
| `fit` refuses the image | The image has the wrong shape | Generate it again in 4:5. Use `--allow-crop` only for text-free plates |
| Text misspelled in a full design | Image models still make mistakes | Regenerate once with the word spelled out, or switch that post to a plate |
| Skills do not appear | The session started before install | Start a new session. The IDE extension does not support plugins |
