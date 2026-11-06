"""Bridge to image tools: exact-size fitting and prompts built from the plan's real copy.

This module never calls an image service. The agent's image tool makes the picture.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from .core import PlanError, asset_path, read_json
from .plan import resolve_brand
from .styles import house_of

SIZES = {'post': (1080, 1350), 'story': (1080, 1920), 'square': (1080, 1080)}
#: Beyond this share of cropped width or height, a full design would lose content.
MAX_CROP = .08
#: Where a logo goes, as (top, bottom) of the footer band for each format.
FOOTER_BANDS = {'post': (1205, 1285), 'story': (1520, 1620), 'square': (950, 1030)}
FOOTER_LEFT, FOOTER_RIGHT = 96, 984


def fit(source, output, fmt='post', logo=None, lock='center', allow_crop=False, focus_y=.5):
    """Bring a generated image to the exact size. Refuses a crop that would cut content."""
    if fmt not in SIZES:
        raise PlanError(f'Format must be one of {", ".join(SIZES)}.')
    if lock not in {'center', 'left'}:
        raise PlanError('The logo lock must be center or left.')
    source, output = Path(source), Path(output)
    if not source.is_file():
        raise PlanError(f'Image not found: {source}')
    if output.exists():
        raise PlanError(f'{output} already exists. Choose a new name.')
    width, height = SIZES[fmt]
    with Image.open(source) as opened:
        picture = ImageOps.exif_transpose(opened).convert('RGB')
    source_ratio, target_ratio = picture.width / picture.height, width / height
    crop_share = abs(1 - min(source_ratio, target_ratio) / max(source_ratio, target_ratio))
    if crop_share > MAX_CROP and not allow_crop:
        raise PlanError(
            f'Fitting {picture.width}x{picture.height} to {width}x{height} would cut {crop_share:.0%} of the image '
            'and could remove text. Generate it again in the right shape, or pass --allow-crop for a text-free plate.')
    fitted = ImageOps.fit(picture, (width, height), Image.Resampling.LANCZOS, centering=(.5, focus_y))
    if logo:
        with Image.open(logo) as opened:
            mark = opened.convert('RGBA')
        top, bottom = FOOTER_BANDS[fmt]
        scale = min(1, (bottom - top) / mark.height, (FOOTER_RIGHT - FOOTER_LEFT) / mark.width)
        mark = mark.resize((round(mark.width * scale), round(mark.height * scale)), Image.Resampling.LANCZOS)
        x = FOOTER_LEFT if lock == 'left' else (width - mark.width) // 2
        fitted.paste(mark, (x, top + (bottom - top - mark.height) // 2), mark)
    output.parent.mkdir(parents=True, exist_ok=True)
    fitted.save(output)
    return {'output': str(output), 'size': [width, height], 'source_size': [picture.width, picture.height],
            'cropped': round(crop_share, 3), 'logo': bool(logo)}


def _style_block(brand):
    colors = ', '.join(f'{key} {brand[key]}' for key in ('primary', 'accent', 'dark', 'light', 'warm'))
    style = brand.get('visual_structure') or brand.get('visual_style') or house_of(brand)['description']
    return f'{style} Palette: {colors}.'


def _typography(brand):
    title, body = brand.get('title_font_name'), brand.get('font_name')
    if title or body:
        parts = [f'Headlines in {title}.' if title else '', f'Other text in {body}.' if body else '']
        return ' '.join(p for p in parts if p)
    return house_of(brand)['description']


def _copy_lines(slide):
    fields = (('Eyebrow', 'eyebrow'), ('Headline', 'headline'), ('Value', 'value'), ('Supporting', 'body'),
              ('Myth', 'myth'), ('Fact', 'fact'), ('Attribution', 'attribution'),
              ('Left label', 'left_label'), ('Right label', 'right_label'), ('CTA button', 'cta'))
    lines = [f'  {label}: "{slide[key]}"' for label, key in fields if slide.get(key)]
    lines += [f'  Item {n}: "{str(item).replace("|", " / ")}"' for n, item in enumerate(slide.get('items', []), 1)]
    return lines


def prompts(plan, mode='plate'):
    """One prompt per slide, in order. Copy is quoted from the plan and never invented."""
    if mode not in {'plate', 'full'}:
        raise PlanError('Mode must be plate or full.')
    brand = resolve_brand(plan)
    style = _style_block(brand)
    fmt = plan.get('format', 'carousel')
    out = []
    for number, slide in enumerate(plan['slides'], 1):
        anchor = 'Attach the image made for item 1 as the style reference. ' if number > 1 and fmt != 'grid' else ''
        if mode == 'plate':
            text = (f'Use case: stylized-concept\nAsset type: text-free background for Instagram post {number}\n'
                    f'Primary request: {slide["visual_prompt"]}\nStyle: {style}\n'
                    f'Composition: 4:5 portrait. Keep the area behind the planned text calm.\n'
                    f'{anchor}Constraints: no text, no lettering, no logos, no watermark, no platform marks, no fake interface.')
        else:
            copy = '\n'.join(_copy_lines(slide))
            footer = 'Leave the bottom 170 px as a calm solid band for the logo, which is added afterwards.'
            text = (f'Use case: ads-marketing\nAsset type: finished Instagram post {number}, 4:5 portrait, 1080 x 1350\n'
                    f'Primary request: {slide["visual_prompt"]}\nStyle: {style}\n'
                    f'{anchor}Text (verbatim, exact spelling and every special character kept):\n{copy}\n'
                    f'Typography: {_typography(brand)} One emphasis only. Keep text at least 80 px from every edge. {footer}\n'
                    'Constraints: print only the text listed above. No extra words, no logos, no watermark, no platform marks, no shadow or outline on type.')
        out.append({'slide': number, 'mode': mode, 'layout': slide['layout'], 'prompt': text,
                    'needs_image': mode == 'full' or bool(slide.get('background') or slide.get('image'))})
    return out


def prompts_markdown(plan, mode='plate'):
    lines = [f'# Image prompts ({mode})', '',
             'Made from the plan. Generate item 1 first so later images can follow its look.', '']
    for item in prompts(plan, mode):
        state = 'needs a picture' if item['needs_image'] else 'composed by the engine, no picture needed'
        lines += [f'## {item["slide"]}: {item["layout"]} ({state})', '', '```text', item['prompt'], '```', '']
    return '\n'.join(lines)


def plan_prompts(path, mode='plate'):
    plan = read_json(path)
    for slide in plan.get('slides', []):
        if slide.get('background'):
            asset_path(slide['background'])
    return prompts(plan, mode)
