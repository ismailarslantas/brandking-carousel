"""Free, offline, brand-aware carousel renderer. No model API or account required."""
from __future__ import annotations
import argparse
import base64
import hashlib
import html
import io
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile
from PIL import Image, ImageDraw, ImageFont, ImageOps
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
LAYOUTS = {'cover', 'statement', 'steps', 'split', 'checklist', 'closing'}
ROTATIONS = {'solid', 'light', 'dark', 'warm'}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def asset_path(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Assets must be inside the project directory.')
    if not path.is_file():
        raise ValueError(f'Asset not found: {value}')
    return path


def luminance(color):
    rgb = [int(color[i:i+2], 16)/255 for i in (1, 3, 5)]
    v = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb]
    return .2126*v[0] + .7152*v[1] + .0722*v[2]


def contrast(a, b):
    x, y = sorted([luminance(a), luminance(b)])
    return (y+.05)/(x+.05)


def ink(background, brand):
    return max([brand['dark'], brand['light']], key=lambda c: contrast(c, background))


def font(path, size, bold=False):
    f = ImageFont.truetype(str(path), size)
    try:
        f.set_variation_by_name('Bold' if bold else 'Regular')
    except (ValueError, OSError, AttributeError):
        pass
    return f


def wrap(text, f, width):
    result = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split():
            if f.getlength(word) > width:
                raise ValueError('A word is too wide. Rewrite it or choose a wider layout.')
            candidate = f'{line} {word}'.strip()
            if line and f.getlength(candidate) > width:
                result.append(line)
                line = word
            else:
                line = candidate
        if line:
            result.append(line)
    return result


def validate(plan):
    if not isinstance(plan, dict):
        raise ValueError('The plan must be a JSON object.')
    brand = plan['brand']
    for key in ('primary', 'accent', 'dark', 'light', 'warm'):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', brand[key]):
            raise ValueError(f'brand.{key} must be a six-digit HEX color.')
    if not brand.get('name') or not plan.get('caption'):
        raise ValueError('Brand name and caption are required.')
    font_path = asset_path(brand.get('font', 'assets/fonts/Figtree.ttf'))
    title_path = asset_path(brand.get('title_font', str(font_path.relative_to(ROOT))))
    if brand.get('logo'):
        asset_path(brand['logo'])
    slides = plan['slides']
    if not 5 <= len(slides) <= 8:
        raise ValueError('A carousel needs 5–8 slides.')
    for n, s in enumerate(slides):
        if s['layout'] not in LAYOUTS or s['rotation'] not in ROTATIONS:
            raise ValueError(f'Slide {n+1}: unsupported layout or rotation.')
        if not 1 <= len(s['headline'].split()) <= 7:
            raise ValueError(f'Slide {n+1}: headline needs 1–7 words.')
        content = ' '.join([s.get('eyebrow', ''), s['headline'], s.get('body', ''),
                            s.get('cta', ''), *s.get('items', [])])
        if len(content.split()) > (8 if n == 0 else 25):
            raise ValueError(f'Slide {n+1}: editorial word limit exceeded.')
        if not s.get('alt') or not s.get('visual_prompt'):
            raise ValueError(f'Slide {n+1}: alt and visual_prompt are required.')
        if s.get('image'):
            asset_path(s['image'])
            if s['layout'] not in {'cover', 'statement'}:
                raise ValueError('Images are supported in cover and statement layouts only.')
            if s.get('body') or s.get('cta'):
                raise ValueError('Image layouts need an empty body and CTA to protect the image zone.')
        if s['layout'] == 'cover' and s.get('body'):
            raise ValueError('Cover layouts do not support body text.')
        if s.get('items') and s['layout'] not in {'steps', 'checklist', 'split'}:
            raise ValueError(f'Slide {n+1}: this layout cannot display items.')
        if len(s.get('items', [])) > (2 if s['layout'] == 'split' else 3):
            raise ValueError(f'Slide {n+1}: too many items for this layout.')
        for path, text in ((title_path, s['headline']), (font_path, content)):
            with TTFont(path) as tf:
                cmap = tf.getBestCmap()
                missing = sorted({c for c in text if not c.isspace() and ord(c) not in cmap})
                if missing:
                    raise ValueError(f'Font is missing characters: {missing}')
        if n and not plan.get('product_variant_exception', False):
            if s['layout'] == slides[n-1]['layout'] or s['rotation'] == slides[n-1]['rotation']:
                raise ValueError('Adjacent slides must vary layout and palette role.')
    if not plan.get('product_variant_exception', False):
        if len({s['rotation'] for s in slides}) < 4 or len({s['layout'] for s in slides}) < 3:
            raise ValueError('Use four palette roles and at least three layouts.')
    return font_path, title_path


class Canvas:
    def __init__(self, bg, body_font, title_font):
        self.im = Image.new('RGB', (1080, 1350), bg)
        self.draw = ImageDraw.Draw(self.im)
        self.body_font, self.title_font = body_font, title_font
        self.svg = [f'<rect width="1080" height="1350" fill="{bg}"/>']
        self.checks = []

    def rect(self, box, color, radius=0):
        self.draw.rounded_rectangle(box, radius=radius, fill=color)
        x, y, r, b = box
        self.svg.append(f'<rect x="{x}" y="{y}" width="{r-x}" height="{b-y}" rx="{radius}" fill="{color}"/>')

    def ellipse(self, box, color):
        self.draw.ellipse(box, fill=color)
        x, y, r, b = box
        self.svg.append(f'<ellipse cx="{(x+r)/2}" cy="{(y+b)/2}" rx="{(r-x)/2}" ry="{(b-y)/2}" fill="{color}"/>')

    def text(self, text, box, size, color, bg, bold=False, title=False, max_lines=8):
        x, y, right, bottom = box
        path = self.title_font if title else self.body_font
        f = font(path, size, bold)
        lines = wrap(text, f, right-x)
        line_height = int(size*1.16)
        if len(lines) > max_lines or y+len(lines)*line_height > bottom:
            raise ValueError(f'Text does not fit: {text!r}. Rewrite or change layout.')
        if contrast(color, bg) < (3 if size >= 42 else 4.5):
            raise ValueError(f'Insufficient text contrast: {text!r}')
        for i, line in enumerate(lines):
            yy = y+i*line_height
            bbox = self.draw.textbbox((x, yy), line, font=f, anchor='lt')
            if bbox[0] < 80 or bbox[1] < 80 or bbox[2] > 1000 or bbox[3] > 1270:
                raise ValueError(f'Text exceeds safe area: {line!r}')
            self.draw.text((x, yy), line, font=f, fill=color, anchor='lt')
            # SVG keeps text editable; raster PNG is the authoritative export.
            self.svg.append(f'<text x="{x}" y="{yy+size*.8}" font-family="{ "Title" if title else "Body" }" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(line)}</text>')
            self.checks.append({'text': line, 'bounds': list(bbox), 'contrast': round(contrast(color, bg), 2)})
        return y+len(lines)*line_height

    def image(self, path, box):
        x, y, right, bottom = box
        with Image.open(path) as source:
            pic = ImageOps.exif_transpose(source).convert('RGBA')
            pic.thumbnail((right-x, bottom-y), Image.Resampling.LANCZOS)
            px, py = x+(right-x-pic.width)//2, y+(bottom-y-pic.height)//2
            self.im.paste(pic, (px, py), pic)
            data = io.BytesIO()
            pic.save(data, format='PNG')
            encoded = base64.b64encode(data.getvalue()).decode()
            self.svg.append(f'<image x="{px}" y="{py}" width="{pic.width}" height="{pic.height}" href="data:image/png;base64,{encoded}"/>')

    def save(self, png, svg):
        self.im.save(png)
        rules = []
        for name, path in [('Body', self.body_font), ('Title', self.title_font)]:
            data = base64.b64encode(path.read_bytes()).decode()
            rules.append(f'@font-face{{font-family:{name};src:url(data:font/ttf;base64,{data});font-weight:100 900;}}')
        svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350"><style>'+''.join(rules)+'</style>'+''.join(self.svg)+'</svg>', encoding='utf-8')


def render_slide(s, brand, index, total, body_font, title_font):
    bg = {'solid': brand['primary'], 'light': brand['light'], 'dark': brand['dark'], 'warm': brand['warm']}[s['rotation']]
    fg = ink(bg, brand)
    c = Canvas(bg, body_font, title_font)
    c.text(s.get('eyebrow', ''), (96, 100, 800, 160), 30, fg, bg)
    c.text(f'{index:02d}/{total:02d}', (880, 100, 984, 160), 28, fg, bg)
    c.rect((96, 185, 984, 188), fg)
    title_y = 250 if s['layout'] != 'closing' else 325
    end = c.text(s['headline'], (96, title_y, 984, title_y+350), 96, fg, bg, True, True, 3)
    body_y = max(650, end+55)
    if s['layout'] == 'cover':
        # A visual metaphor for a swipe: one card system, varied palette roles.
        for j, col in enumerate((brand['warm'], brand['accent'], brand['light'])):
            x, y = 120+j*245, 720+j*45
            c.rect((x, y, x+310, y+270), col, 24)
            cc = ink(col, brand)
            c.rect((x+35, y+45, x+240, y+58), cc, 5)
            c.rect((x+35, y+80, x+175, y+93), cc, 5)
            c.ellipse((x+190, y+150, x+265, y+225), cc)
    elif s['layout'] in {'steps', 'checklist'}:
        if s.get('body'):
            c.text(s['body'], (96, 600, 984, 690), 38, fg, bg, max_lines=2)
        for j, item in enumerate(s.get('items', [])):
            yy = 730+j*125
            c.rect((96, yy, 984, yy+102), fg, 18)
            c.text(f'{j+1:02d}  {item}', (124, yy+25, 956, yy+92), 36, bg, fg, max_lines=1)
    elif s['layout'] == 'split':
        for j, item in enumerate(s.get('items', [])):
            xx = 96+j*456
            col = brand['accent'] if j == 0 else brand['warm']
            c.rect((xx, 700, xx+432, 1090), col, 24)
            c.text(item, (xx+32, 750, xx+400, 1030), 48, ink(col, brand), col, True, max_lines=4)
        if s.get('body'):
            c.text(s['body'], (96, 600, 984, 690), 38, fg, bg, max_lines=2)
    else:
        c.text(s.get('body', ''), (96, body_y, 984, 1010), 48, fg, bg, max_lines=5)
        if s['layout'] == 'statement':
            c.rect((96, 1080, 320, 1092), brand['accent'], 4)
    if s.get('image'):
        # Preserve the full product/label. Use image only in layouts with a clear image zone.
        if s['layout'] not in {'cover', 'statement'}:
            raise ValueError('Images are supported in cover and statement layouts only.')
        c.rect((96, 700, 984, 1100), bg)
        c.image(asset_path(s['image']), (120, 710, 960, 1090))
    if s.get('cta'):
        col = brand['accent']
        c.rect((96, 1040, 984, 1135), col, 45)
        c.text(s['cta'], (130, 1064, 950, 1125), 36, ink(col, brand), col, True, max_lines=1)
    # Fixed footer across the entire series.
    c.rect((0, 1180, 1080, 1350), brand['dark'])
    if brand.get('logo'):
        c.image(asset_path(brand['logo']), (96, 1210, 330, 1260))
    else:
        c.text(brand['name'], (96, 1220, 620, 1270), 28, brand['light'], brand['dark'], True, max_lines=1)
    c.text(brand.get('handle', ''), (650, 1220, 984, 1270), 24, brand['light'], brand['dark'], max_lines=1)
    return c


def render(plan_path, output):
    plan_path, output = Path(plan_path), Path(output).resolve()
    plan = read_json(plan_path)
    body_font, title_font = validate(plan)
    # Never mix stale slides from a previous run with a new delivery.
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output must be empty. Choose a new output directory.')
    output.mkdir(parents=True, exist_ok=True)
    (output/'slides').mkdir()
    (output/'editable').mkdir()
    qa, manifest, specs = [], [], []
    thumbnails = []
    for i, s in enumerate(plan['slides'], 1):
        c = render_slide(s, plan['brand'], i, len(plan['slides']), body_font, title_font)
        name = f'{i:02d}'
        png = output/'slides'/f'{name}.png'
        c.save(png, output/'editable'/f'{name}.svg')
        qa.append({'slide': i, 'size': [1080, 1350], 'text_checks': c.checks, 'visual_review': 'pending'})
        manifest.append({'slide': i, 'file': f'slides/{name}.png', 'sha256': hashlib.sha256(png.read_bytes()).hexdigest()})
        thumb = c.im.copy()
        thumb.thumbnail((360, 450), Image.Resampling.LANCZOS)
        thumbnails.append(thumb)
        specs.append(f"## Slide {i} — {s['layout']}\n\nCopy: {s['headline']}\n\n{s.get('body', '')}\n\nLayout: {s['layout']}; palette role: {s['rotation']}.\n\nVisual production prompt: {s['visual_prompt']}\n")
    sheet = Image.new('RGB', (1080, 450*((len(thumbnails)+2)//3)), '#d9ded8')
    for j, thumb in enumerate(thumbnails):
        sheet.paste(thumb, ((j%3)*360, (j//3)*450))
    sheet.save(output/'contact-sheet.jpg', quality=92)
    write_json(output/'plan.json', plan)
    write_json(output/'manifest.json', manifest)
    write_json(output/'qa-report.json', {'automatic': 'passed', 'visual': 'pending', 'slides': qa})
    write_json(output/'brand-profile.json', plan['brand'])
    (output/'caption.txt').write_text(plan['caption'], encoding='utf-8')
    (output/'alt-texts.md').write_text('\n\n'.join(f"{i}. {s['alt']}" for i, s in enumerate(plan['slides'], 1)), encoding='utf-8')
    (output/'slide-specs.md').write_text('\n'.join(specs), encoding='utf-8')
    (output/'sources.md').write_text('\n'.join(plan.get('sources', [])) or 'No factual claims requiring external sources. Demo content is illustrative.', encoding='utf-8')
    # Self-contained editable recipe: renderer, fonts, dependencies and referenced assets.
    recipe = output/'editable'/'recipe'
    recipe.mkdir()
    for name in ('carousel.py', 'requirements.txt'):
        shutil.copy2(ROOT/name, recipe/name)
    write_json(recipe/'plan.json', plan)
    for value in {plan['brand'].get('font', 'assets/fonts/Figtree.ttf'), plan['brand'].get('title_font', 'assets/fonts/Figtree.ttf'), plan['brand'].get('logo'), *[s.get('image') for s in plan['slides']]} - {None}:
        path = asset_path(value)
        target = recipe/path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    shutil.copy2(ROOT/'assets/fonts/OFL.txt', recipe/'assets/fonts/OFL.txt')
    archive = output/'carousel.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(output.rglob('*')):
            if p.is_file() and p != archive:
                z.write(p, p.relative_to(output).as_posix())
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', default='examples/demo.json')
    parser.add_argument('--output', default='outputs/carousel')
    args = parser.parse_args()
    try:
        result = render(args.plan, args.output)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1
    print(f'Carousel exported to {result}. Visual review is still required.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
