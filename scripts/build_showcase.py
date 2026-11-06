"""Prepare showcase carousels: exact slides plus one strip per set for the README.

Usage: python scripts/build_showcase.py <folder with name-1.png ... name-5.png> name [name ...]
"""
from pathlib import Path
import sys

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'showcase'
FIELD = '#111A17'
TILE = (432, 540)
GAP = 12


def main(source, names):
    for name in names:
        folder = OUT / name
        folder.mkdir(parents=True, exist_ok=True)
        slides = []
        for number in range(1, 6):
            with Image.open(Path(source) / f'{name}-{number}.png') as raw:
                slide = ImageOps.fit(raw.convert('RGB'), (1080, 1350), Image.Resampling.LANCZOS)
            slide.save(folder / f'{number:02d}.jpg', quality=90)
            slides.append(slide)
        strip = Image.new('RGB', (5 * TILE[0] + 4 * GAP, TILE[1]), FIELD)
        for j, slide in enumerate(slides):
            strip.paste(slide.resize(TILE, Image.Resampling.LANCZOS), (j * (TILE[0] + GAP), 0))
        strip.save(OUT / f'{name}.jpg', quality=88)
    print('Built', sorted(p.name for p in OUT.iterdir()))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
