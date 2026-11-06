"""Turns a plan into a delivery folder: slides, previews, reports and a recipe."""
from __future__ import annotations

import copy
from datetime import date
import hashlib
from pathlib import Path
import shutil
import zipfile

from PIL import Image

from .audit import GRID_CROP, audit_deck, summarize
from .core import HEIGHT, PlanError, ROOT, WIDTH, asset_path, read_json, write_json
from .images import prompts_markdown
from .layouts import render_slide
from .lint import has_failures, lint_plan, score_cover
from .memory import remember_from_plan
from .plan import validate
from .styles import house_of


def build(plan):
    """Validate and compose every slide in memory. Writes nothing to disk."""
    brand, body, title = validate(plan)
    total = len(plan['slides'])
    sequence = plan.get('format', 'carousel') == 'carousel'
    canvases = [render_slide(spec, brand, i, total, (body, title), sequence) for i, spec in enumerate(plan['slides'], 1)]
    return brand, canvases


def check(plan):
    """Run lint and the pixel audit without producing files. The agent's fast loop."""
    lint = lint_plan(plan)
    brand, canvases = build(plan)
    audit = audit_deck(canvases, brand, plan.get('product_variant_exception', False), plan.get('format', 'carousel'))
    return {'lint': lint, 'audit': audit, 'lint_summary': summarize(lint) if lint else summarize([]),
            'audit_summary': summarize(audit), 'ok': not (has_failures(lint) or has_failures(audit))}


def contact_sheet(canvases):
    rows = (len(canvases) + 2) // 3
    sheet = Image.new('RGB', (1080, 450 * rows), '#D9DED8')
    for j, canvas in enumerate(canvases):
        thumb = canvas.im.resize((360, 450), Image.Resampling.LANCZOS)
        sheet.paste(thumb, ((j % 3) * 360, (j // 3) * 450))
    return sheet


def swipe_strip(canvases, height=540):
    """Every slide edge to edge, which is how the Crown Thread reads mid-swipe."""
    width = round(WIDTH * height / HEIGHT)
    strip = Image.new('RGB', (width * len(canvases), height))
    for j, canvas in enumerate(canvases):
        strip.paste(canvas.im.resize((width, height), Image.Resampling.LANCZOS), (j * width, 0))
    return strip


def grid_preview(cover):
    """The cover as a 3:4 profile grid tile, next to two neutral neighbours."""
    crop = round(GRID_CROP)
    tile = cover.crop((crop, 0, WIDTH - crop, HEIGHT)).resize((360, 480), Image.Resampling.LANCZOS)
    sheet = Image.new('RGB', (1096, 480), '#FFFFFF')
    sheet.paste(Image.new('RGB', (360, 480), '#D9DED8'), (0, 0))
    sheet.paste(tile, (368, 0))
    sheet.paste(Image.new('RGB', (360, 480), '#D9DED8'), (736, 0))
    return sheet


def grid_map(canvases):
    """Nine posts as profile tiles in 3:4, so the whole grid can be judged at once."""
    crop = round(GRID_CROP)
    tile = (300, 400)
    sheet = Image.new('RGB', (3 * tile[0] + 16, 3 * tile[1] + 16), '#FFFFFF')
    for j, canvas in enumerate(canvases):
        picture = canvas.im.crop((crop, 0, WIDTH - crop, HEIGHT)).resize(tile, Image.Resampling.LANCZOS)
        sheet.paste(picture, ((j % 3) * (tile[0] + 8), (j // 3) * (tile[1] + 8)))
    return sheet


def upload_checklist(plan, status):
    count = len(plan['slides'])
    fmt = plan.get('format', 'carousel')
    if fmt == 'grid':
        order = [f'- [ ] Upload **in reverse order**, from `slides/{count:02d}.png` to `slides/01.png`, as separate posts. The newest post appears first, so this gives the planned grid.',
                 '- [ ] Check `previews/grid-map.jpg`. Pinned posts and later uploads shift the layout.']
    elif fmt == 'series':
        order = [f'- [ ] Post `slides/01.png` to `slides/{count:02d}.png` separately, each with its own caption from `caption.txt`.']
    elif fmt == 'post':
        order = ['- [ ] Upload `slides/01.png`.']
    else:
        order = ['- [ ] Open `contact-sheet.jpg` and `previews/swipe-strip.jpg` on a phone.',
                 f'- [ ] Upload `slides/01.png` to `slides/{count:02d}.png` in order, as one carousel.']
    return '\n'.join([
        '# Before you post', '',
        f'Automatic checks: **{status}**. Visual review: **pending** until `brandking signoff` records it.', '',
        *order,
        '- [ ] Paste the caption from `caption.txt`. Add the alt text from `alt-texts.md` under Advanced settings.',
        '- [ ] Check every number against `sources.md`.',
        '- [ ] After 7 days, log the results with `brandking ledger add`.', '',
    ])


def _write_recipe(output, plan, brand):
    recipe = output / 'editable' / 'recipe'
    recipe.mkdir()
    shutil.copytree(ROOT / 'brandking', recipe / 'brandking', ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('carousel.py', 'requirements.txt'):
        shutil.copy2(ROOT / name, recipe / name)
    portable = copy.deepcopy(plan)
    portable['brand'] = brand
    write_json(recipe / 'plan.json', portable)
    house = house_of(brand)
    wanted = {brand.get('font'), brand.get('title_font'), brand.get('logo'), house['body_font'], house['title_font']}
    for slide in plan['slides']:
        wanted |= {slide.get('image'), slide.get('background')}
    for value in wanted - {None}:
        target = recipe / value
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset_path(value), target)
    for license_file in (ROOT / 'assets/fonts').glob('OFL*.txt'):
        shutil.copy2(license_file, recipe / 'assets/fonts' / license_file.name)


def render(plan_path, output, remember=True):
    """Render a plan to a new folder. Returns the report; `status` says if it may ship.

    A brand used in a passing render is saved, so it never has to be given again.
    """
    plan_path, output = Path(plan_path), Path(output).resolve()
    plan = read_json(plan_path)
    brand, canvases = build(plan)
    lint = lint_plan(plan)
    # Never mix stale slides from a previous run with a new delivery.
    if output.exists() and any(output.iterdir()):
        raise PlanError('Output must be empty. Choose a new output directory.')
    for folder in (output, output / 'slides', output / 'editable', output / 'previews'):
        folder.mkdir(parents=True, exist_ok=True)

    manifest = []
    for number, canvas in enumerate(canvases, 1):
        name = f'{number:02d}'
        png = output / 'slides' / f'{name}.png'
        canvas.save(png, output / 'editable' / f'{name}.svg')
        manifest.append({'slide': number, 'file': f'slides/{name}.png',
                         'sha256': hashlib.sha256(png.read_bytes()).hexdigest()})
    images = [canvas.im for canvas in canvases]
    images[0].save(output / 'slides.pdf', save_all=True, append_images=images[1:], resolution=144)
    fmt = plan.get('format', 'carousel')
    contact_sheet(canvases).save(output / 'contact-sheet.jpg', quality=92)
    if fmt == 'carousel':
        swipe_strip(canvases).save(output / 'previews' / 'swipe-strip.jpg', quality=90)
    grid_preview(images[0]).save(output / 'previews' / 'grid-tile.jpg', quality=90)
    if fmt == 'grid':
        grid_map(canvases).save(output / 'previews' / 'grid-map.jpg', quality=90)

    audit = audit_deck(canvases, brand, plan.get('product_variant_exception', False), fmt)
    blocked = has_failures(lint) or has_failures(audit)
    status = 'failed' if blocked else 'passed'
    report = {
        'automatic': status, 'visual': 'pending', 'rendered_on': date.today().isoformat(),
        'lint_summary': summarize(lint), 'audit_summary': summarize(audit),
        'lint': lint, 'audit': audit,
        'slides': [{'slide': n, 'size': [WIDTH, HEIGHT],
                    'text_checks': [{'text': op['text'], 'bounds': op['bounds'], 'size': op['size'],
                                     'contrast': op.get('contrast')} for op in c.ops]}
                   for n, c in enumerate(canvases, 1)],
    }
    write_json(output / 'qa-report.json', report)
    write_json(output / 'plan.json', plan)
    write_json(output / 'manifest.json', manifest)
    write_json(output / 'brand-profile.json', brand)
    captions = plan.get('caption') or '\n\n---\n\n'.join(
        f'Post {i}\n\n{s["caption"]}' for i, s in enumerate(plan['slides'], 1))
    (output / 'caption.txt').write_text(captions, encoding='utf-8')
    (output / 'alt-texts.md').write_text('\n\n'.join(f'{i}. {s["alt"]}' for i, s in enumerate(plan['slides'], 1)), encoding='utf-8')
    sources = list(plan.get('sources', [])) + [f'Slide {i}: {s["source"]}' for i, s in enumerate(plan['slides'], 1) if s.get('source')]
    (output / 'sources.md').write_text('\n'.join(sources) or 'No factual claims requiring external sources were declared.', encoding='utf-8')
    (output / 'visual-prompts.md').write_text(prompts_markdown({**plan, 'brand': brand}), encoding='utf-8')
    (output / 'upload-checklist.md').write_text(upload_checklist(plan, status), encoding='utf-8')
    _write_recipe(output, plan, brand)
    if not blocked:
        # A blocked delivery stays inspectable, but it gets no ready-to-send archive.
        archive = output / 'carousel.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
            for path in sorted(output.rglob('*')):
                if path.is_file() and path != archive:
                    bundle.write(path, path.relative_to(output).as_posix())
    saved = remember_from_plan(brand) if remember and not blocked else None
    return {'output': str(output), 'status': status, 'remembered': saved and saved['slug'],
            'lint_summary': report['lint_summary'],
            'audit_summary': report['audit_summary'],
            'problems': [f for f in lint + audit if f['severity'] in {'fail', 'warn'}]}


def covers(plan_path, output):
    """Render every entry of `cover_options` on the real cover and rank them side by side."""
    plan_path, output = Path(plan_path), Path(output).resolve()
    plan = read_json(plan_path)
    options = plan.get('cover_options', [])
    if len(options) < 3:
        raise PlanError('Add at least three headlines to cover_options, then compare them.')
    brand, body, title = validate(plan)
    if output.exists() and any(output.iterdir()):
        raise PlanError('Output must be empty. Choose a new output directory.')
    output.mkdir(parents=True, exist_ok=True)
    results, thumbs = [], []
    for letter, headline in zip('ABCDEFGH', options):
        spec = {**plan['slides'][0], 'headline': headline}
        spec.pop('emphasis', None)
        canvas = render_slide(spec, brand, 1, len(plan['slides']), (body, title))
        canvas.im.save(output / f'cover-{letter}.png')
        results.append({'option': letter, **score_cover(headline)})
        thumbs.append(canvas.im.resize((360, 450), Image.Resampling.LANCZOS))
    sheet = Image.new('RGB', (368 * len(thumbs) - 8, 450), '#FFFFFF')
    for j, thumb in enumerate(thumbs):
        sheet.paste(thumb, (j * 368, 0))
    sheet.save(output / 'cover-sheet.jpg', quality=92)
    results.sort(key=lambda item: -item['score'])
    write_json(output / 'cover-ranking.json', {
        'note': 'A checklist of traits to help you edit. It does not predict reach. Choose by eye at phone size.',
        'ranking': results})
    return results
