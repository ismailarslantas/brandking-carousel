"""Slide compositions. Every editorial decision lives in the plan, not here."""
from __future__ import annotations

import math

from .canvas import Canvas
from .core import CONTENT_BOTTOM, FOOTER_TOP, PlanError, THREAD_Y, WIDTH, asset_path, contrast, ink, mix
from .styles import house_of

LEFT, RIGHT = 96, 984
HEADER_RULE = 185


class Slide:
    """Everything a layout needs for one slide."""

    def __init__(self, spec, brand, index, total, fonts, sequence=True):
        self.spec, self.brand, self.index, self.total = spec, brand, index, total
        self.sequence = sequence
        self.house = house_of(brand)
        self.bg = {'solid': brand['primary'], 'light': brand['light'],
                   'dark': brand['dark'], 'warm': brand['warm']}[spec['rotation']]
        self.fg = ink(self.bg, brand)
        self.radius = self.house['radius']
        self.canvas = Canvas(self.bg, *fonts)

    def card_colors(self):
        """Palette colors that stand apart from this slide's background."""
        options = [self.brand[k] for k in ('accent', 'warm', 'light', 'dark', 'primary')]
        return [c for c in options if contrast(c, self.bg) >= 1.25] or [self.fg]

    def headline(self, top, bottom=660, scale=1.0, box=(LEFT, RIGHT), color=None, max_lines=3):
        """Set the headline. Steps down a fixed ladder, then asks for shorter copy."""
        text = self.spec['headline']
        if self.house['uppercase']:
            text = text.upper()
        base = round(self.house['title_size'] * scale)
        last = None
        for size in (base, round(base * .86), round(base * .74)):
            try:
                return self.canvas.text(
                    text, (box[0], top, box[1], bottom), size, color or self.fg,
                    bold=self.house['title_bold'], title=True, max_lines=max_lines,
                    leading=self.house['leading'], role='headline',
                    emphasis=self.spec.get('emphasis'), accent=self.brand['accent'])
            except PlanError as error:
                last = error
                self.canvas.ops = [op for op in self.canvas.ops if op['role'] != 'headline']
        raise last

    def body(self, top, bottom=1040, size=46, max_lines=5):
        return self.canvas.text(self.spec.get('body', ''), (LEFT, top, RIGHT, bottom), size, self.fg, max_lines=max_lines)


def _header(s):
    c = s.canvas
    c.text(s.spec.get('eyebrow', ''), (LEFT, 100, 820, 160), 30, s.fg, max_lines=1, role='eyebrow')
    if s.sequence:
        c.text(f'{s.index:02d}/{s.total:02d}', (850, 100, RIGHT, 160), 28, s.fg, max_lines=1, role='counter', align='right')
    c.rect((LEFT, HEADER_RULE, RIGHT, HEADER_RULE + 3), s.fg)


def _cover(s):
    c, spec = s.canvas, s.spec
    if spec.get('image'):
        s.headline(235, 670, 1.08)
        c.image(asset_path(spec['image']), (120, 690, 960, 1110))
        return
    s.headline(235, 690, 1.16)
    # A swipe made visible: three cards, one system, different palette roles.
    palette = (s.card_colors() * 3)[:3]
    for j, color in enumerate(palette):
        x, y = 120 + j * 245, 730 + j * 40
        c.rect((x, y, x + 310, y + 270), color, s.radius)
        tone = ink(color, s.brand)
        c.rect((x + 35, y + 45, x + 240, y + 58), tone, 5)
        c.rect((x + 35, y + 80, x + 175, y + 93), tone, 5)
        c.ellipse((x + 190, y + 150, x + 265, y + 225), tone)


def _statement(s):
    c, spec = s.canvas, s.spec
    end = s.headline(250)
    if spec.get('image'):
        c.image(asset_path(spec['image']), (120, max(end + 30, 660), 960, 1110))
        return
    s.body(max(650, end + 50))
    c.rect((LEFT, 1070, 320, 1082), s.brand['accent'] if contrast(s.brand['accent'], s.bg) >= 1.5 else s.fg, 4)


def _split(s):
    c, spec = s.canvas, s.spec
    end = s.headline(240, 560)
    top = max(690, s.body(end + 30, 680, 38, 2) + 30)
    colors = (s.card_colors() * 2)[:2]
    for j, item in enumerate(spec.get('items', [])):
        x = LEFT + j * 456
        c.rect((x, top, x + 432, 1100), colors[j], s.radius)
        c.text(item, (x + 32, top + 44, x + 400, 1070), 48, ink(colors[j], s.brand), bold=True, max_lines=6)


def _steps(s):
    c, spec = s.canvas, s.spec
    end = s.headline(240, 560)
    top = max(730, s.body(end + 30, 720, 38, 2) + 30)
    for j, item in enumerate(spec.get('items', [])):
        y = top + j * 125
        c.rect((LEFT, y, RIGHT, y + 104), s.fg, min(s.radius, 18))
        c.text(f'{j + 1:02d}  {item}', (124, y + 28, 956, y + 96), 36, s.bg, max_lines=1, bold=True)


def _checklist(s):
    c, spec = s.canvas, s.spec
    end = s.headline(240, 560)
    top = max(700, s.body(end + 30, 690, 38, 2) + 30)
    tick = s.brand['accent'] if contrast(s.brand['accent'], s.bg) >= 3 else s.fg
    mark = ink(tick, s.brand)
    for j, item in enumerate(spec.get('items', [])):
        y = top + j * 132
        c.ellipse((LEFT, y, LEFT + 76, y + 76), tick)
        c.line([(LEFT + 21, y + 40), (LEFT + 33, y + 52), (LEFT + 56, y + 27)], mark, 7)
        c.text(item, (LEFT + 104, y + 12, RIGHT, y + 112), 40, s.fg, max_lines=2, bold=True, leading=1.14)
        c.rect((LEFT, y + 108, RIGHT, y + 110), mix(s.fg, s.bg, .7))


def _timeline(s):
    c, spec = s.canvas, s.spec
    end = s.headline(240, 560)
    items = spec.get('items', [])
    top = max(600, end + 50)
    gap = min(135, (CONTENT_BOTTOM - top) // max(1, len(items)))
    node = s.brand['accent'] if contrast(s.brand['accent'], s.bg) >= 1.6 else s.fg
    c.rect((LEFT + 17, top + 18, LEFT + 23, top + 18 + gap * (len(items) - 1)), node)
    for j, item in enumerate(items):
        y = top + j * gap
        c.ellipse((LEFT, y, LEFT + 40, y + 40), node)
        c.text(item, (LEFT + 76, y - 4, RIGHT, y + gap - 8), 40, s.fg, max_lines=2, leading=1.14)


def _versus(s):
    c, spec = s.canvas, s.spec
    end = s.headline(240, 480, .86, max_lines=2)
    top = max(500, end + 35)
    tones = (mix(s.fg, s.bg, .84), s.brand['accent'] if contrast(s.brand['accent'], s.bg) >= 1.25 else s.fg)
    rows = spec.get('items', [])
    for j, tone in enumerate(tones):
        x = LEFT + j * 456
        fg = ink(tone, s.brand)
        c.rect((x, top, x + 432, 1100), tone, s.radius)
        c.text(spec['left_label' if j == 0 else 'right_label'], (x + 30, top + 30, x + 402, top + 90), 34, fg, bold=True, max_lines=1)
        for r, row in enumerate(rows):
            cell = row.split('|')[j].strip()
            y = top + 112 + r * ((1100 - top - 130) // max(1, len(rows)))
            c.text(cell, (x + 30, y, x + 402, 1085), 42, fg, max_lines=4, leading=1.14)


def _myth(s):
    c, spec = s.canvas, s.spec
    end = s.headline(240, 480, .8, max_lines=2)
    top = max(520, end + 40)
    bottom = s.canvas.text('MYTH', (LEFT, top, 400, top + 50), 30, s.fg, bold=True, max_lines=1)
    after = c.text(spec['myth'], (LEFT, bottom + 8, RIGHT, 830), 46, s.fg, max_lines=3, strike=True)
    panel = s.brand['accent'] if contrast(s.brand['accent'], s.bg) >= 1.25 else s.fg
    fg = ink(panel, s.brand)
    y = max(after + 30, 790)
    c.rect((LEFT, y, RIGHT, 1100), panel, s.radius)
    c.text('FACT', (LEFT + 36, y + 30, 400, y + 80), 30, fg, bold=True, max_lines=1)
    for size in (64, 52, 42):
        try:
            c.text(spec['fact'], (LEFT + 36, y + 84, RIGHT - 36, 1085), size, fg, bold=True, max_lines=4, leading=1.1)
            break
        except PlanError:
            if size == 42:
                raise


def _stat(s):
    c, spec = s.canvas, s.spec
    value, last = spec['value'], None
    for size in (300, 240, 180, 130):
        try:
            end = c.text(value, (LEFT, 225, RIGHT, 640), size, s.fg, bold=s.house['title_bold'], title=True,
                         max_lines=1, leading=1.1, role='value')
            break
        except PlanError as error:
            last = error
    else:
        raise last
    end = s.headline(end + 30, 800, .62)
    s.body(end + 30, 1010, 42, 3)
    c.text(f'Source: {spec["source"]}', (LEFT, 1030, RIGHT, 1118), 28, s.fg, max_lines=2, role='source')


def _quote(s):
    c, spec = s.canvas, s.spec
    bar = s.brand['accent'] if contrast(s.brand['accent'], s.bg) >= 1.5 else s.fg
    end = s.headline(300, 900, .84, box=(LEFT + 52, RIGHT), max_lines=6)
    c.rect((LEFT, 306, LEFT + 14, end), bar, 7)
    bottom = c.text(spec['attribution'], (LEFT + 52, end + 40, RIGHT, end + 110), 38, s.fg, bold=True, max_lines=1)
    c.text(f'Source: {spec["source"]}', (LEFT + 52, max(bottom + 16, 1020), RIGHT, 1118), 28, s.fg, max_lines=2, role='source')


def _bento(s):
    c, spec = s.canvas, s.spec
    end = s.headline(240, 520, .86, max_lines=2)
    top, items = max(540, end + 35), spec.get('items', [])
    colors = (s.card_colors() * 4)[:4]
    mid_x, mid_y = 590, top + (1100 - top) * 3 // 5
    boxes = {
        1: [(LEFT, top, RIGHT, 1100)],
        2: [(LEFT, top, mid_x - 12, 1100), (mid_x + 12, top, RIGHT, 1100)],
        3: [(LEFT, top, mid_x - 12, 1100), (mid_x + 12, top, RIGHT, mid_y - 12), (mid_x + 12, mid_y + 12, RIGHT, 1100)],
        4: [(LEFT, top, mid_x - 12, mid_y - 12), (mid_x + 12, top, RIGHT, mid_y - 12),
            (LEFT, mid_y + 12, 470, 1100), (494, mid_y + 12, RIGHT, 1100)],
    }.get(len(items), [])
    for j, (box, item, color) in enumerate(zip(boxes, items, colors)):
        c.rect(box, color, s.radius)
        size = 60 if j == 0 and len(items) in (1, 2, 3) else 40
        c.text(item, (box[0] + 28, box[1] + 26, box[2] - 24, box[3] - 14), size, ink(color, s.brand), bold=True, max_lines=6, leading=1.12)


def _photo(s):
    c, spec = s.canvas, s.spec
    c.cover(asset_path(spec['background']), (0, 0, WIDTH, 1130), spec.get('focus_y', .5))
    if spec.get('panel', True):
        # The panel hugs its copy, so short headlines do not sit in an empty box.
        scale = .92 if s.index == 1 else .76
        s.canvas = Canvas(s.bg, c.body_font, c.title_font)
        probe = s.headline(0, 400, scale, max_lines=3)
        probe = s.canvas.text(spec.get('body', ''), (LEFT, probe + 14, RIGHT, probe + 200), 36, s.fg, max_lines=3)
        s.canvas = c
        top = 1100 - probe - 70
        c.rect((64, top, 1016, 1100), s.bg, s.radius)
        c.rect((64, 70, 1016, 150), s.bg, s.radius)
        c.text(spec.get('eyebrow', ''), (96, 92, 820, 142), 28, s.fg, max_lines=1, role='eyebrow')
        if s.sequence:
            c.text(f'{s.index:02d}/{s.total:02d}', (850, 92, RIGHT, 142), 28, s.fg, max_lines=1, role='counter', align='right')
        end = s.headline(top + 30, top + 430, scale, max_lines=3)
        c.text(spec.get('body', ''), (LEFT, end + 14, RIGHT, 1090), 36, s.fg, max_lines=3)
        return
    # No panel: type sits directly on the picture and the audit measures it.
    c.text(spec.get('eyebrow', ''), (LEFT, 100, 820, 160), 30, s.fg, max_lines=1, role='eyebrow')
    if s.sequence:
        c.text(f'{s.index:02d}/{s.total:02d}', (850, 100, RIGHT, 160), 28, s.fg, max_lines=1, role='counter', align='right')
    end = s.headline(200, 800)
    c.text(spec.get('body', ''), (LEFT, end + 20, RIGHT, 1090), 42, s.fg, max_lines=4)


def _closing(s):
    c, spec = s.canvas, s.spec
    end = s.headline(310, 720)
    s.body(max(640, end + 45), 980, 46, 4)
    if spec.get('cta'):
        color = s.brand['accent'] if contrast(s.brand['accent'], s.bg) >= 1.25 else s.fg
        c.rect((LEFT, 1010, RIGHT, 1104), color, min(47, s.radius * 2))
        c.text(spec['cta'], (130, 1034, 950, 1098), 36, ink(color, s.brand), bold=True, max_lines=1, role='cta')


LAYOUT_FUNCTIONS = {
    'cover': _cover, 'statement': _statement, 'split': _split, 'steps': _steps, 'checklist': _checklist,
    'timeline': _timeline, 'versus': _versus, 'myth': _myth, 'stat': _stat, 'quote': _quote,
    'bento': _bento, 'photo': _photo, 'closing': _closing,
}


def _crown(c, x, y, color, size=30):
    """A small three-point crown, the mark at the end of the thread."""
    h = size * .78
    c.polygon([(x - size, y + h * .5), (x - size * 1.05, y - h * .6), (x - size * .48, y - h * .05),
               (x, y - h), (x + size * .48, y - h * .05), (x + size * 1.05, y - h * .6),
               (x + size, y + h * .5)], color)


def thread_y(x):
    """The wave completes whole periods per slide, so every seam meets at the same height."""
    return round(THREAD_Y + 7 * math.sin(2 * math.pi * x / 540), 1)


def _thread(s):
    """The Crown Thread: one continuous line that crosses every swipe.

    It starts with a bead on slide one, keeps moving through the deck and ends
    in a crown on the last slide. It is the same line in the same lane, so the
    seam between two slides lines up while the reader is mid-swipe.
    """
    c = s.canvas
    color = s.brand['accent'] if contrast(s.brand['accent'], s.bg) >= 1.8 else s.fg
    first, last = s.index == 1, s.index == s.total
    start, end = (LEFT if first else 0), (RIGHT - 50 if last else WIDTH)
    points = [(x, thread_y(x)) for x in range(start, end + 1, 6)]
    if points[-1][0] != end:
        points.append((end, thread_y(end)))
    c.line(points, color, 5)
    if last:
        _crown(c, RIGHT - 18, thread_y(end) - 2, color, 32)
    else:
        bead = LEFT + (RIGHT - LEFT) * (s.index - 1) / max(1, s.total - 1)
        bead_y = thread_y(bead)
        c.ellipse((round(bead - 13), round(bead_y - 13), round(bead + 13), round(bead_y + 13)), color)
    return color


def _footer(s):
    c, brand = s.canvas, s.brand
    c.rect((0, FOOTER_TOP, WIDTH, 1350), brand['dark'])
    if brand.get('footer', 'split') == 'center':
        if brand.get('logo'):
            c.image(asset_path(brand['logo']), (340, 1205, 740, 1275))
        else:
            c.text(brand['name'], (96, 1222, 984, 1272), 30, brand['light'], bold=True, max_lines=1, role='footer', align='center')
        return
    if brand.get('logo'):
        c.image(asset_path(brand['logo']), (LEFT, 1208, 400, 1272))
    else:
        c.text(brand['name'], (LEFT, 1222, 560, 1272), 28, brand['light'], bold=True, max_lines=1, role='footer')
    handle = brand.get('handle', '')
    if handle:
        c.text(handle, (580, 1224, RIGHT, 1272), 24, brand['light'], max_lines=1, role='footer', align='right')


def render_slide(spec, brand, index, total, fonts, sequence=True):
    """Compose one slide. Returns its finished canvas plus what the audit needs."""
    s = Slide(spec, brand, index, total, fonts, sequence)
    if spec['layout'] != 'photo':
        if spec.get('background'):
            s.canvas.cover(asset_path(spec['background']), (0, 0, WIDTH, 1130), spec.get('focus_y', .5))
        _header(s)
    if s.spec['layout'] == 'photo':
        s.canvas.rect((0, 1130, WIDTH, FOOTER_TOP), s.bg)
    try:
        LAYOUT_FUNCTIONS[spec['layout']](s)
    except PlanError as error:
        raise PlanError(f'Slide {index}: {error}') from error
    # Counters and the thread only make sense when slides are swiped in order.
    thread_color = _thread(s) if sequence and brand.get('thread', True) else None
    _footer(s)
    s.canvas.finish()
    s.canvas.thread_color = thread_color
    return s.canvas
