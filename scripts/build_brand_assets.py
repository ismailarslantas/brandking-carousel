"""Derive the logo family from the art-directed source: assets/brand/logo-source.png.

Run this only when the source logo changes.
"""
from pathlib import Path

from PIL import Image, ImageChops

BRAND = Path(__file__).resolve().parents[1] / 'assets' / 'brand'


def transparent(image, background=None):
    """Turn the flat logo background into alpha, keeping edges soft."""
    image = image.convert('RGB')
    background = background or image.getpixel((5, 5))
    difference = ImageChops.difference(image, Image.new('RGB', image.size, background)).convert('L')
    alpha = difference.point(lambda v: min(255, v * 4))
    result = image.convert('RGBA')
    result.putalpha(alpha)
    return result


def tight(image):
    return image.crop(image.getchannel('A').point(lambda v: 255 if v > 40 else 0).getbbox())


def main():
    source = Image.open(BRAND / 'logo-source.png').convert('RGB')
    width, height = source.size
    alpha = transparent(source)
    # The wordmark sits below the emblem, so find the empty band that separates them.
    mask = alpha.getchannel('A').point(lambda v: 255 if v > 40 else 0)
    rows = [mask.crop((0, y, width, y + 1)).getbbox() is not None for y in range(height)]
    ink_rows = [y for y, used in enumerate(rows) if used]
    gaps = [(b - a, a, b) for a, b in zip(ink_rows, ink_rows[1:]) if b - a > 1]
    # The widest gap in the lower half separates the emblem from the wordmark.
    _, split_top, split_bottom = max(g for g in gaps if g[1] > height * .5)
    mark = tight(alpha.crop((0, 0, width, split_top + 1)))
    word = tight(alpha.crop((0, split_bottom, width, height)))
    mark.save(BRAND / 'mark.png')
    word.save(BRAND / 'wordmark.png')
    # Horizontal lockup for slide footers and repository headers.
    h = 200
    mark_small = mark.resize((round(mark.width * h / mark.height), h), Image.Resampling.LANCZOS)
    word_h = 74
    word_small = word.resize((round(word.width * word_h / word.height), word_h), Image.Resampling.LANCZOS)
    lockup = Image.new('RGBA', (mark_small.width + 44 + word_small.width, h), (0, 0, 0, 0))
    lockup.paste(mark_small, (0, 0), mark_small)
    lockup.paste(word_small, (mark_small.width + 44, (h - word_h) // 2), word_small)
    lockup.save(BRAND / 'logo-horizontal.png')
    source.resize((1024, 1024), Image.Resampling.LANCZOS).save(BRAND / 'logo-square.png')
    # Avatar: the emblem alone on the brand field, ready for profile pictures.
    side = 1024
    avatar = Image.new('RGBA', (side, side), source.getpixel((5, 5)) + (255,))
    scale = side * .74 / max(mark.size)
    big = mark.resize((round(mark.width * scale), round(mark.height * scale)), Image.Resampling.LANCZOS)
    avatar.paste(big, ((side - big.width) // 2, (side - big.height) // 2), big)
    avatar.convert('RGB').save(BRAND / 'avatar.png')
    avatar.convert('RGB').resize((256, 256), Image.Resampling.LANCZOS).save(BRAND / 'favicon.png')
    print('Built', sorted(p.name for p in BRAND.glob('*.png')))


if __name__ == '__main__':
    main()
