"""Structural validation. A plan that passes here can be rendered, not necessarily posted."""
from __future__ import annotations

import re

from fontTools.ttLib import TTFont

from .core import PlanError, ROOT, asset_path, read_json
from .styles import HOUSES, house_of

LAYOUTS = {
    'cover': 'Headline with a swipe metaphor or an uncropped product image.',
    'statement': 'Headline and body in open space, or an uncropped image.',
    'split': 'Two side-by-side panels through items, with an optional short body.',
    'steps': 'Up to three numbered rows through items.',
    'checklist': 'Up to three ticked rows through items.',
    'timeline': 'Up to four connected points through items.',
    'versus': 'A comparison table: left_label, right_label, items written as "A | B".',
    'myth': 'A struck-through myth and a highlighted fact.',
    'stat': 'One large value with a label. Needs a source.',
    'quote': 'A real quote as the headline. Needs attribution and a source.',
    'bento': 'Up to four cells of varied size through items.',
    'photo': 'A full background image with a text panel. Set panel to false to set type directly on it.',
    'closing': 'Headline, body and one call to action.',
}
ROTATIONS = {'solid', 'light', 'dark', 'warm'}
COLOR_KEYS = ('primary', 'accent', 'dark', 'light', 'warm')
MIN_SLIDES, MAX_SLIDES = 3, 20
ITEM_LIMITS = {'split': 2, 'steps': 3, 'checklist': 3, 'timeline': 4, 'versus': 3, 'bento': 4}
HEADLINE_LIMITS = {'quote': 18}
WORD_LIMITS = {'versus': 30, 'quote': 30}
TEXT_FIELDS = ('eyebrow', 'headline', 'body', 'cta', 'myth', 'fact', 'value', 'attribution',
               'left_label', 'right_label')


def resolve_brand(plan):
    """A plan may inline its brand or point at a reusable brand kit directory."""
    brand = plan.get('brand')
    if isinstance(brand, str):
        kit = (ROOT / brand).resolve()
        if not kit.is_relative_to(ROOT):
            raise PlanError('Brand kits must be inside the project directory.')
        if not (kit / 'brand.json').is_file():
            raise PlanError(f'Brand kit not found: {brand}/brand.json')
        return read_json(kit / 'brand.json')
    if isinstance(brand, dict):
        return brand
    raise PlanError('brand must be an object or the path of a brand kit.')


def slide_words(slide):
    parts = [str(slide.get(field, '')) for field in TEXT_FIELDS]
    parts += [str(item).replace('|', ' ') for item in slide.get('items', [])]
    return ' '.join(parts).split()


def slide_text(slide):
    return ' '.join(slide_words(slide))


def fonts_for(brand):
    house = house_of(brand)
    body = asset_path(brand.get('font', house['body_font']))
    title = asset_path(brand.get('title_font', house['title_font']))
    return body, title


def _check_glyphs(path, text):
    with TTFont(path) as font:
        cmap = font.getBestCmap()
    missing = sorted({c for c in text if not c.isspace() and ord(c) not in cmap})
    if missing:
        raise PlanError(f'{path.name} has no glyph for {missing}. Remove them or use another font.')


def check_slide(slide, n, total, brand, fonts):
    label = f'Slide {n + 1}'
    if not isinstance(slide, dict):
        raise PlanError(f'{label}: must be an object.')
    for field in ('layout', 'rotation', 'headline', 'alt', 'visual_prompt'):
        if not slide.get(field):
            raise PlanError(f'{label}: {field} is required.')
    layout = slide['layout']
    if layout not in LAYOUTS:
        raise PlanError(f'{label}: unknown layout {layout!r}. Available: {", ".join(sorted(LAYOUTS))}.')
    if slide['rotation'] not in ROTATIONS:
        raise PlanError(f'{label}: rotation must be one of {", ".join(sorted(ROTATIONS))}.')
    limit = HEADLINE_LIMITS.get(layout, 7)
    if not 1 <= len(slide['headline'].split()) <= limit:
        raise PlanError(f'{label}: headline needs 1-{limit} words.')
    words = slide_words(slide)
    budget = 8 if n == 0 else WORD_LIMITS.get(layout, 25)
    if len(words) > budget:
        raise PlanError(f'{label}: {len(words)} words is over the limit of {budget}. Cut copy, do not shrink it.')
    if slide.get('emphasis') and not set(slide['emphasis'].casefold().split()) <= {
            re.sub(r'\W+', '', w).casefold() for w in slide['headline'].split()}:
        raise PlanError(f'{label}: emphasis must use words from the headline.')
    if slide.get('items'):
        if layout not in ITEM_LIMITS:
            raise PlanError(f'{label}: the {layout} layout cannot display items.')
        if len(slide['items']) > ITEM_LIMITS[layout]:
            raise PlanError(f'{label}: {layout} holds at most {ITEM_LIMITS[layout]} items.')
    if layout == 'cover' and slide.get('body'):
        raise PlanError(f'{label}: cover layouts do not take body text.')
    if slide.get('image'):
        asset_path(slide['image'])
        if layout not in {'cover', 'statement'}:
            raise PlanError(f'{label}: image works in cover and statement layouts. Use photo with background otherwise.')
        if slide.get('body') or slide.get('cta'):
            raise PlanError(f'{label}: image layouts need an empty body and CTA to protect the image zone.')
    if slide.get('background'):
        asset_path(slide['background'])
    focus = slide.get('focus_y', .5)
    if not isinstance(focus, (int, float)) or not 0 <= focus <= 1:
        raise PlanError(f'{label}: focus_y must be between 0 and 1.')
    if layout == 'photo' and not slide.get('background'):
        raise PlanError(f'{label}: the photo layout needs a background image.')
    if layout == 'versus':
        if not slide.get('left_label') or not slide.get('right_label'):
            raise PlanError(f'{label}: versus needs left_label and right_label.')
        if not all(str(item).count('|') == 1 for item in slide.get('items', [])):
            raise PlanError(f'{label}: versus items are written as "left | right".')
    if layout == 'myth' and not (slide.get('myth') and slide.get('fact')):
        raise PlanError(f'{label}: myth needs both myth and fact.')
    if layout == 'stat' and not (slide.get('value') and slide.get('source')):
        raise PlanError(f'{label}: stat needs value and source. Numbers without a source do not ship.')
    if layout == 'quote' and not (slide.get('attribution') and slide.get('source')):
        raise PlanError(f'{label}: quote needs attribution and source. Quotes must be real.')
    body, title = fonts
    uppercase = house_of(brand).get('uppercase')
    headline = slide['headline'].upper() if uppercase else slide['headline']
    _check_glyphs(title, headline + str(slide.get('value', '')))
    _check_glyphs(body, slide_text(slide))


def validate(plan):
    """Return (brand, body_font, title_font) or raise PlanError."""
    if not isinstance(plan, dict):
        raise PlanError('The plan must be a JSON object.')
    brand = resolve_brand(plan)
    for key in COLOR_KEYS:
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', str(brand.get(key, ''))):
            raise PlanError(f'brand.{key} must be a six-digit HEX color.')
    if not brand.get('name'):
        raise PlanError('brand.name is required.')
    if brand.get('house', 'sovereign') not in HOUSES:
        raise PlanError(f'brand.house must be one of {", ".join(sorted(HOUSES))}.')
    if not plan.get('caption'):
        raise PlanError('caption is required.')
    if brand.get('logo'):
        asset_path(brand['logo'])
    fonts = fonts_for(brand)
    slides = plan.get('slides')
    if not isinstance(slides, list) or not MIN_SLIDES <= len(slides) <= MAX_SLIDES:
        raise PlanError(f'A carousel needs {MIN_SLIDES}-{MAX_SLIDES} slides.')
    for n, slide in enumerate(slides):
        check_slide(slide, n, len(slides), brand, fonts)
    if not plan.get('product_variant_exception', False):
        for n in range(1, len(slides)):
            if slides[n]['layout'] == slides[n - 1]['layout'] or slides[n]['rotation'] == slides[n - 1]['rotation']:
                raise PlanError(f'Slides {n} and {n + 1}: adjacent slides must vary layout and palette role.')
        if len({s['rotation'] for s in slides}) < min(4, len(slides)):
            raise PlanError('Use four palette roles across the deck.')
        if len({s['layout'] for s in slides}) < min(3, len(slides)):
            raise PlanError('Use at least three layouts across the deck.')
    return (brand, *fonts)
