"""Build the README proof images from real engine output, so the pictures cannot flatter it.

Run from the repository root after changing layouts or examples.
"""
from pathlib import Path
import sys

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from brandking.audit import audit_contrast  # noqa: E402
from brandking.canvas import load_font  # noqa: E402
from brandking.core import read_json  # noqa: E402
from brandking.deliver import build, swipe_strip  # noqa: E402
from brandking.layouts import render_slide  # noqa: E402
from brandking.plan import validate  # noqa: E402

OUT = ROOT / 'assets' / 'readme'
FIELD, IVORY, LIME, RED = '#111A17', '#F4F1E8', '#D6F75A', '#FF6B5B'
FONT = ROOT / 'assets/fonts/Figtree.ttf'


def label(draw, xy, text, size, fill=IVORY, bold=True):
    draw.text(xy, text, font=load_font(FONT, size, bold), fill=fill, anchor='ls')


def strip_of(example):
    _, canvases = build(read_json(ROOT / 'examples' / example))
    return swipe_strip(canvases, 540)


def houses():
    """Three brands, three houses: first three slides of each example."""
    rows = [('SOVEREIGN', 'demo.json'), ('EDITORIAL', 'editorial.json'), ('POSTER', 'poster.json')]
    tile = (324, 405)
    sheet = Image.new('RGB', (1100, 3 * tile[1] + 4 * 44), FIELD)
    draw = ImageDraw.Draw(sheet)
    y = 44
    for name, example in rows:
        _, canvases = build(read_json(ROOT / 'examples' / example))
        label(draw, (40, y + 8), name, 22, LIME)
        for j, canvas in enumerate(canvases[:3]):
            sheet.paste(canvas.im.resize(tile, Image.Resampling.LANCZOS), (40 + j * (tile[0] + 14), y + 22))
        y += tile[1] + 44
    sheet.save(OUT / 'houses.jpg', quality=90)


def contrast_proof():
    """The same plan on a bright plate and a calm plate, with the audit's real verdict."""
    plan = read_json(ROOT / 'examples/demo.json')
    brand, body, title = validate(plan)
    plate = ROOT / 'examples/plates/throne-room.png'
    base = {'layout': 'photo', 'rotation': 'dark', 'headline': 'Rule the first swipe.', 'eyebrow': 'PIXEL AUDIT',
            'alt': 'x', 'visual_prompt': 'x', 'background': plate.relative_to(ROOT).as_posix(), 'focus_y': 0}
    bright = Image.new('RGB', (1080, 1350), '#F1EEDF')
    temp = ROOT / 'outputs' / '_bright_plate.png'
    temp.parent.mkdir(exist_ok=True)
    bright.paste('#C7C2AC', (0, 700, 1080, 1350))
    bright.save(temp)
    failing = {**base, 'panel': False, 'background': temp.relative_to(ROOT).as_posix()}
    passing = {**base, 'panel': True}
    results = []
    for spec in (failing, passing):
        canvas = render_slide(spec, brand, 2, 6, (body, title))
        findings = audit_contrast(canvas, 2)
        worst = min(op['contrast'] for op in canvas.ops if op.get('contrast') is not None)
        results.append((canvas, any(f['severity'] == 'fail' for f in findings), worst))
    temp.unlink()
    tile = (432, 540)
    sheet = Image.new('RGB', (1000, 690), FIELD)
    draw = ImageDraw.Draw(sheet)
    for j, (canvas, failed, worst) in enumerate(results):
        x = 44 + j * 480
        sheet.paste(canvas.im.resize(tile, Image.Resampling.LANCZOS), (x, 44))
        verdict = 'FAIL' if failed else 'PASS'
        label(draw, (x, 628), f'{verdict}  lowest measured {worst:.2f}:1', 28, RED if failed else LIME)
    sheet.save(OUT / 'contrast-proof.jpg', quality=92)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    strip_of('demo.json').save(OUT / 'swipe-strip.jpg', quality=90)
    houses()
    contrast_proof()
    print('Built', sorted(p.name for p in OUT.iterdir()))


if __name__ == '__main__':
    main()
