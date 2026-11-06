"""The Royal Ledger: a local record of what each post set out to test and what happened.

You type the numbers from Instagram's own Insights. Nothing here logs in, scrapes
or calls an API. The report refuses to call a winner on a handful of posts.
"""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path

from .core import PlanError, ROOT

METRICS = ('reach', 'saves', 'sends', 'likes', 'comments', 'follows')
MIN_POSTS = 5


def default_path():
    return ROOT / 'private' / 'ledger.jsonl'


def load(path=None):
    path = Path(path or default_path())
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def add(entry, path=None):
    if not entry.get('id'):
        raise PlanError('A ledger entry needs an id.')
    for metric in METRICS:
        value = entry.get(metric)
        if value is None:
            continue
        if not isinstance(value, int) or value < 0:
            raise PlanError(f'{metric} must be a whole number.')
    if not entry.get('reach'):
        raise PlanError('Reach is required, every rate is measured against it.')
    path = Path(path or default_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {'logged': date.today().isoformat(), **entry}
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry


def report(path=None, by=('hook_type', 'format', 'house')):
    """Compare saves and sends per 1,000 reached. Small groups are flagged, not ranked."""
    entries = load(path)
    groups = {}
    for field in by:
        table = {}
        for entry in entries:
            key = entry.get(field)
            if key:
                table.setdefault(key, []).append(entry)
        rows = []
        for key, posts in table.items():
            reach = sum(p['reach'] for p in posts)
            rows.append({
                'value': key, 'posts': len(posts), 'reach': reach,
                'saves_per_1k': round(1000 * sum(p.get('saves', 0) for p in posts) / reach, 1),
                'sends_per_1k': round(1000 * sum(p.get('sends', 0) for p in posts) / reach, 1),
                'follows_per_1k': round(1000 * sum(p.get('follows', 0) for p in posts) / reach, 1),
                'confidence': 'pattern worth testing' if len(posts) >= MIN_POSTS else f'too few posts, need {MIN_POSTS}',
            })
        groups[field] = sorted(rows, key=lambda r: -(r['saves_per_1k'] + r['sends_per_1k']))
    return {'posts': len(entries), 'groups': groups,
            'note': 'Association, not cause. Topic, timing and audience also move these numbers.'}
