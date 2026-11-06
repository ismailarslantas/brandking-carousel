# Image plates: pictures without the spelling mistakes

Image models still misspell, and they slip when asked to keep the same type across a set. Brandking splits the job: the model paints a **plate**, a picture with no text in it, and the engine sets every letter on top. Spelling comes from your plan, and contrast is measured on the finished picture.

## Workflow

1. Write a `visual_prompt` per slide that needs a picture. `visual-prompts.md` in each delivery gathers them with a shared style block.
2. Generate slide one in any image tool you already use. Attach it to later prompts so the set shares one look.
3. Save plates in `private/assets/` (or `assets/` for public demos).
4. Reference them in the plan with `"layout": "photo"` and `"background": "private/assets/plate-1.png"`.
5. Run `brandking check`. If type sits on a busy area, the audit reports the measured contrast.

## What makes a good plate

- Say "no text, no lettering, no logos" in every prompt.
- Keep one calm region where the panel or type will sit, and name that region in the prompt.
- Use 4:5 portrait. The engine crops to fit the area above the thread.
- Name the palette in HEX and describe light and material.
- Never ask a model to draw a real product label, screenshot, person or logo. Use the real file with `image`, which never crops it.

## Panel or no panel

`"panel": true` is the default: type sits on a solid card, which is reliably readable. `"panel": false` sets type straight on the picture. The audit then measures the pixels behind each line and fails anything too low, so a bright patch behind three letters is found before your audience finds it.

Do not rescue a failing line by darkening the whole picture. Move to a panel, choose a calmer plate, or switch palette role.
