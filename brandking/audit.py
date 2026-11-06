"""Pixel audit. Measures the rendered slides instead of trusting the plan.

Severities: fail blocks delivery, warn needs a human look, pass is measured and
fine, skipped means the check did not run and the reason says why.
A check that did not run is never reported as passed.
"""
from __future__ import annotations

from PIL import Image, ImageDraw

from .canvas import load_font
from .core import FOOTER_TOP, HEIGHT, LINEAR, SAFE_AREA, THREAD_Y, WIDTH, contrast_lum, hex_rgb, rgb_luminance

#: Instagram profile grids show 3:4 tiles, which trims a 4:5 slide at the sides.
GRID_CROP = (WIDTH - HEIGHT * 3 / 4) / 2
MIN_SIZES = {'footer': 24, 'source': 28, 'counter': 28}
DEFAULT_MIN_SIZE = 28
COVER_HEADLINE_MIN = 72


def _finding(check, severity, detail, slide=None, **extra):
    item = {'check': check, 'severity': severity, 'detail': detail}
    if slide is not None:
        item['slide'] = slide
    item.update(extra)
    return item


def measure_contrast(op, plate):
    """Worst-case contrast between a word and the pixels actually behind its glyphs.

    Uses the 5th percentile so one stray pixel does not fail a word but a bright
    patch behind a few letters does.
    """
    x0, y0, x1, y1 = op['bounds']
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(WIDTH, x1), min(HEIGHT, y1)
    if x1 <= x0 or y1 <= y0:
        return None
    mask = Image.new('L', (x1 - x0, y1 - y0), 0)
    font = load_font(op['font'], op['size'], op['bold'])
    ImageDraw.Draw(mask).text((op['x'] - x0, op['baseline'] - y0), op['text'], font=font, fill=255, anchor='ls')
    region = plate.crop((x0, y0, x1, y1)).convert('RGB')
    mask_pixels = mask.tobytes()
    plate_pixels = region.tobytes()
    text_lum = rgb_luminance(hex_rgb(op['color']))
    values = []
    for index, coverage in enumerate(mask_pixels):
        if coverage > 128:
            at = index * 3
            lum = (.2126 * LINEAR[plate_pixels[at]] + .7152 * LINEAR[plate_pixels[at + 1]]
                   + .0722 * LINEAR[plate_pixels[at + 2]])
            values.append(contrast_lum(text_lum, lum))
    if not values:
        return None
    values.sort()
    return values[len(values) // 20]


def audit_contrast(canvas, slide):
    out, worst = [], None
    for op in canvas.ops:
        value = measure_contrast(op, canvas.plate)
        if value is None:
            continue
        op['contrast'] = round(value, 2)
        need = 3 if op['size'] >= 42 or (op['size'] >= 32 and op['bold']) else 4.5
        if worst is None or value < worst:
            worst = value
        if value < need:
            out.append(_finding('measured_contrast', 'fail',
                                f'{op["text"]!r} measures {value:.2f}:1 against its real background, needs {need}:1.', slide))
    if worst is not None and not out:
        out.append(_finding('measured_contrast', 'pass', f'Lowest measured contrast is {worst:.2f}:1.', slide))
    return out


def audit_layout(canvas, slide, first):
    out = []
    left, top, right, bottom = SAFE_AREA
    for op in canvas.ops:
        x0, y0, x1, y1 = op['bounds']
        if x0 < left or y0 < top or x1 > right or y1 > bottom:
            out.append(_finding('safe_area', 'fail', f'{op["text"]!r} leaves the safe area at {op["bounds"]}.', slide))
        if op['role'] != 'footer' and y1 > FOOTER_TOP:
            out.append(_finding('footer_collision', 'fail', f'{op["text"]!r} runs into the footer.', slide))
        floor = MIN_SIZES.get(op['role'], DEFAULT_MIN_SIZE)
        if op['size'] < floor:
            out.append(_finding('phone_legibility', 'fail', f'{op["text"]!r} is {op["size"]}px, the floor is {floor}px.', slide))
        if first and (x0 < GRID_CROP or x1 > WIDTH - GRID_CROP):
            out.append(_finding('grid_crop', 'fail', f'{op["text"]!r} is cut off by the 3:4 profile grid crop.', slide))
    blocks = {}
    for op in canvas.ops:
        box = blocks.setdefault(op['element'], list(op['bounds']))
        box[0], box[1] = min(box[0], op['bounds'][0]), min(box[1], op['bounds'][1])
        box[2], box[3] = max(box[2], op['bounds'][2]), max(box[3], op['bounds'][3])
    items = list(blocks.items())
    for i, (element, a) in enumerate(items):
        for other, b in items[i + 1:]:
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                out.append(_finding('text_collision', 'fail', f'Text blocks overlap at {a} and {b}.', slide))
    if first:
        sizes = [op['size'] for op in canvas.ops if op['role'] == 'headline']
        if sizes and max(sizes) < COVER_HEADLINE_MIN:
            out.append(_finding('cover_scale', 'warn', f'Cover headline is {max(sizes)}px. It may be weak as a grid thumbnail.', slide))
    area = sum((b[2] - b[0]) * (b[3] - b[1]) for _, b in items if b[3] <= FOOTER_TOP)
    density = area / (WIDTH * FOOTER_TOP)
    if density > .42:
        out.append(_finding('density', 'warn', f'Text covers {density:.0%} of the slide. Consider cutting copy.', slide))
    if not any(item['severity'] == 'fail' for item in out):
        out.append(_finding('layout_bounds', 'pass', f'Safe area, footer, collisions and type floors are clean. Density {density:.0%}.', slide))
    return out


def _thread_center(image, x, color):
    target = hex_rgb(color)
    ys = []
    for y in range(THREAD_Y - 20, THREAD_Y + 21):
        pixel = image.getpixel((x, y))
        if sum(abs(p - q) for p, q in zip(pixel, target)) < 60:
            ys.append(y)
    return sum(ys) / len(ys) if ys else None


def audit_thread(canvases, enabled):
    if not enabled:
        return [_finding('thread_seams', 'skipped', 'The brand kit turns the Crown Thread off.')]
    out = []
    for n in range(len(canvases) - 1):
        a = _thread_center(canvases[n].im, WIDTH - 1, canvases[n].thread_color)
        b = _thread_center(canvases[n + 1].im, 0, canvases[n + 1].thread_color)
        seam = f'{n + 1}/{n + 2}'
        if a is None or b is None:
            out.append(_finding('thread_seams', 'fail', f'Seam {seam}: the thread cannot be found on the slide edge.', n + 1))
        elif abs(a - b) > 3:
            out.append(_finding('thread_seams', 'fail', f'Seam {seam}: the thread jumps {abs(a - b):.1f}px.', n + 1))
    if not out:
        out.append(_finding('thread_seams', 'pass', f'All {len(canvases) - 1} seams line up within 3px.'))
    return out


def audit_rhythm(canvases, exempt):
    if exempt:
        return [_finding('visual_rhythm', 'skipped', 'The plan declares a product variant exception.')]
    def thumb(canvas):
        return canvas.im.convert('L').resize((32, 40), Image.Resampling.BILINEAR).tobytes()
    out = []
    thumbs = [thumb(c) for c in canvases]
    for n in range(len(thumbs) - 1):
        difference = sum(abs(p - q) for p, q in zip(thumbs[n], thumbs[n + 1])) / len(thumbs[n])
        if difference < 8:
            out.append(_finding('visual_rhythm', 'warn', f'Slides {n + 1} and {n + 2} look alike at thumbnail size ({difference:.1f}/255).', n + 1))
    if not out:
        out.append(_finding('visual_rhythm', 'pass', 'Adjacent slides differ at thumbnail size.'))
    return out


def audit_deck(canvases, brand, exempt=False):
    findings = []
    for number, canvas in enumerate(canvases, 1):
        if canvas.im.size != (WIDTH, HEIGHT):
            findings.append(_finding('canvas_size', 'fail', f'Slide is {canvas.im.size}.', number))
        findings += audit_contrast(canvas, number)
        findings += audit_layout(canvas, number, number == 1)
    findings += audit_thread(canvases, brand.get('thread', True))
    findings += audit_rhythm(canvases, exempt)
    return findings


def summarize(findings):
    counts = {'fail': 0, 'warn': 0, 'pass': 0, 'skipped': 0}
    for item in findings:
        counts[item['severity']] += 1
    return counts
