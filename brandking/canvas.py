"""Drawing surface. Geometry is drawn first, text is drawn last.

Keeping the two apart gives the audit something other tools lack: the plate, an
image of exactly what sits behind every glyph. Contrast is then measured instead
of assumed. Everything is drawn at twice the size and scaled down, so rounded
corners and curves come out smooth.
"""
from __future__ import annotations

import base64
from functools import lru_cache
import html
import io
import re

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .core import HEIGHT, PlanError, SAFE_AREA, WIDTH, contrast

SS = 2


@lru_cache(maxsize=64)
def load_font(path, size, bold=False):
    """Load a font and, when it is variable, set its weight axis."""
    font = ImageFont.truetype(str(path), size)
    try:
        axes = font.get_variation_axes()
    except (OSError, AttributeError):
        return font
    values = []
    for axis in axes:
        name = axis['name']
        name = name.decode() if isinstance(name, bytes) else str(name)
        if name.lower().startswith('weight'):
            values.append(min(axis['maximum'], 700 if bold else 400))
        elif name.lower().startswith('optical'):
            # A sturdier cut than the display extreme, whose hairlines vanish on a phone.
            values.append(min(axis['maximum'], 36))
        else:
            values.append(axis['default'])
    font.set_variation_by_axes(values)
    return font


def _token(word):
    return re.sub(r'\W+', '', word).casefold()


class Canvas:
    def __init__(self, bg, body_font, title_font):
        self.bg = bg
        self.body_font, self.title_font = body_font, title_font
        self.base = Image.new('RGB', (WIDTH * SS, HEIGHT * SS), bg)
        self.draw = ImageDraw.Draw(self.base)
        self.svg = [f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{bg}"/>']
        self.ops = []
        self.im = None
        self.plate = None

    # Geometry ---------------------------------------------------------------
    def rect(self, box, color, radius=0):
        x, y, right, bottom = box
        self.draw.rounded_rectangle([v * SS for v in box], radius=radius * SS, fill=color)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{right - x}" height="{bottom - y}" rx="{radius}" fill="{color}"/>')

    def ellipse(self, box, color):
        x, y, right, bottom = box
        self.draw.ellipse([v * SS for v in box], fill=color)
        self.svg.append(f'<ellipse cx="{(x + right) / 2}" cy="{(y + bottom) / 2}" rx="{(right - x) / 2}" ry="{(bottom - y) / 2}" fill="{color}"/>')

    def polygon(self, points, color):
        self.draw.polygon([(x * SS, y * SS) for x, y in points], fill=color)
        path = ' '.join(f'{x},{y}' for x, y in points)
        self.svg.append(f'<polygon points="{path}" fill="{color}"/>')

    def line(self, points, color, width):
        self.draw.line([(x * SS, y * SS) for x, y in points], fill=color, width=width * SS, joint='curve')
        path = ' '.join(f'{x},{y}' for x, y in points)
        self.svg.append(f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>')

    def _embed(self, picture, x, y):
        data = io.BytesIO()
        picture.convert('RGB').save(data, format='JPEG', quality=86)
        encoded = base64.b64encode(data.getvalue()).decode()
        self.svg.append(f'<image x="{x}" y="{y}" width="{picture.width}" height="{picture.height}" href="data:image/jpeg;base64,{encoded}"/>')

    def image(self, path, box):
        """Fit a picture inside the box without cropping. For products and logos."""
        x, y, right, bottom = box
        with Image.open(path) as source:
            picture = ImageOps.exif_transpose(source).convert('RGBA')
        scale = min((right - x) / picture.width, (bottom - y) / picture.height)
        size = max(1, round(picture.width * scale)), max(1, round(picture.height * scale))
        big = picture.resize((size[0] * SS, size[1] * SS), Image.Resampling.LANCZOS)
        px, py = x + (right - x - size[0]) // 2, y + (bottom - y - size[1]) // 2
        self.base.paste(big, (px * SS, py * SS), big)
        self._embed(big.resize(size, Image.Resampling.LANCZOS), px, py)

    def cover(self, path, box, focus_y=.5):
        """Fill the box, cropping the overflow. For scenes and text-free plates."""
        x, y, right, bottom = box
        with Image.open(path) as source:
            picture = ImageOps.exif_transpose(source).convert('RGB')
        fitted = ImageOps.fit(picture, ((right - x) * SS, (bottom - y) * SS), Image.Resampling.LANCZOS, centering=(.5, focus_y))
        self.base.paste(fitted, (x * SS, y * SS))
        self._embed(fitted.resize((right - x, bottom - y), Image.Resampling.LANCZOS), x, y)

    # Text -------------------------------------------------------------------
    def _lines(self, text, font, width):
        lines = []
        for paragraph in text.split('\n'):
            line = ''
            for word in paragraph.split():
                if font.getlength(word) / SS > width:
                    raise PlanError(f'The word {word!r} is too wide. Rewrite it or use a wider layout.')
                candidate = f'{line} {word}'.strip()
                if line and font.getlength(candidate) / SS > width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            if line:
                lines.append(line)
        return lines

    def text(self, text, box, size, color, bold=False, title=False, max_lines=8,
             leading=1.22, role='body', emphasis=None, accent=None, strike=False, align='left'):
        """Lay out text and queue it for drawing. Returns the y below the block.

        Raises PlanError when the copy does not fit, because the fix is better
        copy or another layout, never a silently smaller font.
        """
        if not text:
            return box[1]
        x, y, right, bottom = box
        path = self.title_font if title else self.body_font
        font = load_font(path, size * SS, bold)
        lines = self._lines(text, font, right - x)
        step = round(size * leading)
        if len(lines) > max_lines or y + len(lines) * step > bottom + round(size * .2):
            raise PlanError(f'Text does not fit: {text!r}. Rewrite it or change the layout.')
        wanted = {_token(w) for w in (emphasis or '').split()}
        element = len({op['element'] for op in self.ops})
        for index, line in enumerate(lines):
            baseline = y + round(size * .9) + index * step
            words = [(line, False)]
            if wanted:
                words = [(w, _token(w) in wanted) for w in line.split()]
            line_width = font.getlength(line) / SS
            cursor = {'left': x, 'right': right - line_width, 'center': x + (right - x - line_width) / 2}[align]
            space = font.getlength(' ') / SS
            for word, marked in words:
                advance = font.getlength(word) / SS
                fill = color
                if marked:
                    if contrast(accent, self.bg) >= 3:
                        fill = accent
                    else:
                        # A marker stroke keeps the emphasis readable when the
                        # accent would vanish against this background.
                        self.rect((round(cursor - 8), baseline - round(size * .82),
                                   round(cursor + advance + 8), baseline + round(size * .2)), accent, 6)
                self.ops.append({'text': word, 'x': cursor, 'baseline': baseline, 'size': size,
                                 'color': fill, 'font': path, 'bold': bold, 'role': role,
                                 'element': element, 'strike': strike})
                cursor += advance + space
        return y + len(lines) * step

    # Output -----------------------------------------------------------------
    def finish(self):
        """Draw queued text and produce both the plate and the final image."""
        self.plate = self.base.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(self.base)
        for op in self.ops:
            font = load_font(op['font'], op['size'] * SS, op['bold'])
            position = (op['x'] * SS, op['baseline'] * SS)
            draw.text(position, op['text'], font=font, fill=op['color'], anchor='ls')
            box = draw.textbbox(position, op['text'], font=font, anchor='ls')
            op['bounds'] = [round(v / SS) for v in box]
            if op['strike']:
                # Drawn over the text, so it never counts as the text's background.
                mid = (op['baseline'] - op['size'] * .3) * SS
                draw.line([(box[0], mid), (box[2], mid)], fill=op['color'], width=4 * SS)
            family = 'Title' if op['font'] == self.title_font else 'Body'
            self.svg.append(f'<text x="{op["x"]:.1f}" y="{op["baseline"]}" font-family="{family}" font-size="{op["size"]}" font-weight="{700 if op["bold"] else 400}" fill="{op["color"]}">{html.escape(op["text"])}</text>')
        self.im = self.base.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        return self

    def save(self, png, svg):
        self.im.save(png, optimize=True)
        rules = []
        for name, path in (('Body', self.body_font), ('Title', self.title_font)):
            data = base64.b64encode(path.read_bytes()).decode()
            rules.append(f'@font-face{{font-family:{name};src:url(data:font/ttf;base64,{data});font-weight:100 900;}}')
        svg.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}"><style>'
            + ''.join(rules) + '</style>' + ''.join(self.svg) + '</svg>', encoding='utf-8')


__all__ = ['Canvas', 'SAFE_AREA', 'SS', 'load_font']
