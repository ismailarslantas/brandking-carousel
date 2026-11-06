"""Shared constants and small helpers. Nothing here knows about layouts or copy."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIDTH, HEIGHT = 1080, 1350
#: Text must stay inside this box (left, top, right, bottom).
SAFE_AREA = (80, 80, 1000, 1270)
#: Every slide reserves this band for the footer lock.
FOOTER_TOP = 1180
#: The Crown Thread runs along this baseline, between content and footer.
THREAD_Y = 1156
#: Layout content must end above this line.
CONTENT_BOTTOM = 1122


class PlanError(ValueError):
    """The plan cannot be rendered as written. The message says what to change."""


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def asset_path(value):
    """Resolve a repository-relative asset. Paths may not leave the project."""
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT):
        raise PlanError('Assets must be inside the project directory.')
    if not path.is_file():
        raise PlanError(f'Asset not found: {value}')
    return path


def _channel(value):
    value /= 255
    return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4


#: Linear-light lookup table, so pixel audits do not recompute the curve per pixel.
LINEAR = [_channel(v) for v in range(256)]


def hex_rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def rgb_luminance(rgb):
    return .2126 * LINEAR[rgb[0]] + .7152 * LINEAR[rgb[1]] + .0722 * LINEAR[rgb[2]]


def luminance(color):
    return rgb_luminance(hex_rgb(color))


def contrast_lum(a, b):
    low, high = sorted((a, b))
    return (high + .05) / (low + .05)


def contrast(a, b):
    return contrast_lum(luminance(a), luminance(b))


def ink(background, brand):
    """Pick whichever brand neutral reads best on this background."""
    return max((brand['dark'], brand['light']), key=lambda c: contrast(c, background))


def mix(a, b, amount):
    """Blend two HEX colors. amount=0 returns a, amount=1 returns b."""
    x, y = hex_rgb(a), hex_rgb(b)
    return '#' + ''.join(f'{round(p + (q - p) * amount):02X}' for p, q in zip(x, y))
