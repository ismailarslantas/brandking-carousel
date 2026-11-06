"""Reusable brand kits: one folder per brand, shared by every carousel."""
from __future__ import annotations

from pathlib import Path
import re

from .core import PlanError, ROOT, asset_path, contrast, mix, read_json, write_json
from .plan import COLOR_KEYS
from .styles import HOUSES


def derive_palette(primary, accent):
    """Build the three neutrals from two brand colors, tinted so they feel related."""
    return {
        'primary': primary.upper(), 'accent': accent.upper(),
        'dark': mix(primary, '#000000', .72),
        'light': mix(primary, '#FFFFFF', .95),
        'warm': mix(mix(primary, '#F5E6C8', .8), '#FFFFFF', .25),
    }


def init_kit(slug, name, primary, accent, handle='', house='sovereign', root=None):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug):
        raise PlanError('The brand slug uses lowercase letters, digits and hyphens.')
    for label, value in (('primary', primary), ('accent', accent)):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
            raise PlanError(f'{label} must be a six-digit HEX color.')
    if house not in HOUSES:
        raise PlanError(f'house must be one of {", ".join(sorted(HOUSES))}.')
    folder = Path(root or ROOT / 'private' / 'brands') / slug
    if (folder / 'brand.json').exists():
        raise PlanError(f'{folder} already holds a brand kit. Edit it instead.')
    folder.mkdir(parents=True, exist_ok=True)
    kit = {'name': name, 'handle': handle, 'house': house, **derive_palette(primary, accent),
           'footer': 'split', 'thread': True,
           'voice': {'tone': '', 'banned_words': [], 'allowed_words': [], 'max_hashtags': 5},
           'evidence': 'Replace with where these tokens came from: brand guide, logo file or screenshots.'}
    write_json(folder / 'brand.json', kit)
    return folder


def check_kit(path):
    """Report how the palette behaves before any slide uses it."""
    kit = read_json(Path(path) / 'brand.json')
    findings = []
    for key in COLOR_KEYS:
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', str(kit.get(key, ''))):
            raise PlanError(f'brand.{key} must be a six-digit HEX color.')
    for role in ('primary', 'light', 'dark', 'warm'):
        best = max(contrast(kit['dark'], kit[role]), contrast(kit['light'], kit[role]))
        severity = 'pass' if best >= 4.5 else 'fail'
        findings.append({'check': f'ink_on_{role}', 'severity': severity, 'detail': f'Best ink on {role} measures {best:.2f}:1, needs 4.5:1.'})
        accent = contrast(kit['accent'], kit[role])
        findings.append({'check': f'accent_on_{role}', 'severity': 'pass' if accent >= 3 else 'warn',
                         'detail': f'Accent on {role} measures {accent:.2f}:1. Below 3:1 the engine uses a marker stroke or ink instead.'})
    for key in ('font', 'title_font', 'logo'):
        if kit.get(key):
            asset_path(kit[key])
            findings.append({'check': key, 'severity': 'pass', 'detail': f'{kit[key]} exists.'})
        elif key == 'logo':
            findings.append({'check': 'logo', 'severity': 'warn', 'detail': 'No logo set. The footer will show the brand name as text.'})
    return {'name': kit.get('name'), 'findings': findings}
