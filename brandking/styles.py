"""Houses: complete typographic systems a brand picks once and keeps."""
from __future__ import annotations

HOUSES = {
    'sovereign': {
        'description': 'Confident geometric sans. A safe default for education, software and services.',
        'title_font': 'assets/fonts/Figtree.ttf', 'body_font': 'assets/fonts/Figtree.ttf',
        'title_size': 96, 'title_bold': True, 'leading': 1.08, 'radius': 24, 'uppercase': False,
    },
    'editorial': {
        'description': 'Quiet serif headlines over a sans body. For premium, hospitality, art and culture.',
        'title_font': 'assets/fonts/Fraunces.ttf', 'body_font': 'assets/fonts/Figtree.ttf',
        'title_size': 92, 'title_bold': False, 'leading': 1.1, 'radius': 6, 'uppercase': False,
    },
    'poster': {
        'description': 'Tall condensed capitals. For food, events, retail and anything that should shout.',
        'title_font': 'assets/fonts/Anton.ttf', 'body_font': 'assets/fonts/Figtree.ttf',
        'title_size': 128, 'title_bold': False, 'leading': 1.12, 'radius': 0, 'uppercase': True,
    },
}


def house_of(brand):
    return HOUSES[brand.get('house', 'sovereign')]
