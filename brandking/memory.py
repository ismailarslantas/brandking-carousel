"""Brand memory: give a brand once, and it is never asked for again.

Each brand lives in <home>/brands/<slug>/ with its tokens, voice, visual structure and
copies of its logo, fonts and references. <home> is ~/.brandking, or BRANDKING_HOME when
set, so every project on the computer shares it. Where that folder cannot be written,
such as inside a sandbox, memory falls back to .brandking in the current project.
Nothing leaves the computer.
"""
from __future__ import annotations

from datetime import date
import json
import os
from pathlib import Path
import re
import shutil
import unicodedata

from .core import PlanError, project_dir, read_json, write_json

FILE_FIELDS = {'logo': 'logo', 'font': 'font', 'title_font': 'title-font'}
TEXT_FIELDS = ('name', 'handle', 'house', 'primary', 'accent', 'dark', 'light', 'warm', 'footer',
               'font_name', 'title_font_name', 'visual_structure', 'visual_style', 'website', 'sector', 'evidence')


def global_home():
    return Path(os.environ.get('BRANDKING_HOME') or Path.home() / '.brandking').resolve()


def project_home():
    return (project_dir() / '.brandking').resolve()


def homes():
    """Nearest first, so a project can keep its own version of a brand."""
    return [project_home(), global_home()]


def slugify(name):
    text = unicodedata.normalize('NFKD', str(name)).encode('ascii', 'ignore').decode().lower()
    slug = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    if not slug:
        raise PlanError('The brand name needs at least one letter or digit.')
    return slug


def _writable_home():
    home = global_home()
    try:
        (home / 'brands').mkdir(parents=True, exist_ok=True)
        probe = home / '.write-test'
        probe.write_text('ok', encoding='utf-8')
        probe.unlink()
        return home, 'global'
    except OSError:
        home = project_home()
        (home / 'brands').mkdir(parents=True, exist_ok=True)
        return home, 'project'


def _find(slug):
    for home in homes():
        path = home / 'brands' / slug / 'brand.json'
        if path.is_file():
            return home, path
    return None, None


def remember(fields, references=(), make_active=True):
    """Create or update a brand. Fields that are not given keep their saved value."""
    fields = {k: v for k, v in fields.items() if v not in (None, '')}
    slug = fields.get('slug') or slugify(fields.get('name', ''))
    found_home, found = _find(slug)
    brand = read_json(found) if found else {}
    home, scope = (found_home, 'project' if found_home == project_home() else 'global') if found else _writable_home()
    if not found and not fields.get('name'):
        raise PlanError(f'No saved brand called {slug}. Give its name to create it.')
    folder = home / 'brands' / slug
    folder.mkdir(parents=True, exist_ok=True)
    for key in TEXT_FIELDS:
        if key in fields:
            brand[key] = fields[key]
    if isinstance(fields.get('voice'), dict):
        brand['voice'] = {**brand.get('voice', {}), **fields['voice']}
    for key in FILE_FIELDS:
        if key in fields:
            source = Path(fields[key])
            if not source.is_file():
                raise PlanError(f'{key} file not found: {source}')
            target = folder / f'{FILE_FIELDS[key]}{source.suffix.lower()}'
            if source.resolve() != target.resolve():
                shutil.copy2(source, target)
            brand[key] = f'brands/{slug}/{target.name}'
    if references:
        (folder / 'references').mkdir(exist_ok=True)
        saved = list(brand.get('references', []))
        for item in references:
            source = Path(item)
            if not source.is_file():
                raise PlanError(f'Reference not found: {source}')
            target = folder / 'references' / source.name
            if source.resolve() != target.resolve():
                shutil.copy2(source, target)
            path = f'brands/{slug}/references/{source.name}'
            if path not in saved:
                saved.append(path)
        brand['references'] = saved
    _fill_palette(brand)
    brand['slug'] = slug
    brand['updated'] = date.today().isoformat()
    write_json(folder / 'brand.json', brand)
    if make_active:
        write_json(home / 'active.json', {'slug': slug})
    return {'slug': slug, 'scope': scope, 'path': str(folder), 'brand': brand}


def _fill_palette(brand):
    from .brandkit import derive_palette
    if brand.get('primary') and brand.get('accent'):
        for key, value in derive_palette(brand['primary'], brand['accent']).items():
            brand.setdefault(key, value)


def recall(slug=None):
    """Return a saved brand, or None. Without a slug, return the last one used."""
    if slug is None:
        for home in homes():
            active = home / 'active.json'
            if active.is_file():
                slug = read_json(active).get('slug')
                if slug and _find(slug)[1]:
                    break
                slug = None
    if slug is None:
        return None
    home, path = _find(slug)
    if not path:
        return None
    return {'slug': slug, 'scope': 'project' if home == project_home() else 'global',
            'path': str(path.parent), 'brand': read_json(path)}


def list_brands():
    seen, rows = set(), []
    active = recall()
    for home in homes():
        for path in sorted((home / 'brands').glob('*/brand.json')) if (home / 'brands').is_dir() else []:
            slug = path.parent.name
            if slug not in seen:
                seen.add(slug)
                rows.append({'slug': slug, 'name': read_json(path).get('name'),
                             'scope': 'project' if home == project_home() else 'global',
                             'active': bool(active and active['slug'] == slug)})
    return rows


def forget(slug):
    """Delete a saved brand and its stored copies. Only ever called on the user's request."""
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug):
        raise PlanError('Unknown brand slug.')
    removed = False
    for home in homes():
        folder = home / 'brands' / slug
        if folder.is_dir():
            shutil.rmtree(folder)
            removed = True
        active = home / 'active.json'
        if active.is_file() and read_json(active).get('slug') == slug:
            active.unlink()
    if not removed:
        raise PlanError(f'No saved brand called {slug}.')
    return slug


def remember_from_plan(brand):
    """Called after a successful render, so using a brand once is enough to save it.

    Example brands set "demo": true and are never saved.
    """
    if brand.get('demo') or not brand.get('name'):
        return None
    fields = {k: brand[k] for k in TEXT_FIELDS if brand.get(k)}
    fields['slug'] = brand.get('slug')
    if isinstance(brand.get('voice'), dict):
        fields['voice'] = brand['voice']
    from .core import asset_path
    for key in FILE_FIELDS:
        if brand.get(key):
            fields[key] = str(asset_path(brand[key]))
    return remember(fields)


def dumps(data):
    return json.dumps(data, ensure_ascii=False, indent=2)
