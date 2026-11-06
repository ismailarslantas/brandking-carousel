"""Run folders and gates. A run knows which stage it reached and what is still open."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import re

from .core import PlanError, ROOT, read_json, write_json

BRIEF = """# Brief: {run_id}

Brand kit:
Audience (one sentence, who and what they struggle with):
Single reader problem:
Goal (saves, sends, follows, inquiries, sales):
Language:
Mode (review or auto):
Assets supplied:
Facts and sources available:
"""


def run_dir(run_id):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', run_id):
        raise PlanError('A run id uses letters, digits, dots, hyphens and underscores.')
    return ROOT / 'private' / 'runs' / run_id


def new_run(run_id):
    folder = run_dir(run_id)
    if folder.exists():
        raise PlanError(f'{folder} already exists.')
    folder.mkdir(parents=True)
    (folder / 'brief.md').write_text(BRIEF.format(run_id=run_id), encoding='utf-8')
    return folder


def _qa_state(folder):
    report = folder / 'delivery' / 'qa-report.json'
    if not report.is_file():
        return None
    return read_json(report)


def status(run_id):
    """Report each gate from the evidence on disk, never from what an agent says."""
    folder = run_dir(run_id)
    if not folder.is_dir():
        raise PlanError(f'No run named {run_id}.')
    qa = _qa_state(folder)
    gates = [
        ('brief', (folder / 'brief.md').is_file(), 'Fill in brief.md.'),
        ('brand_analysis', (folder / 'brand-analysis.json').is_file(), 'The Scout writes brand-analysis.json.'),
        ('angles', (folder / 'angles.md').is_file(), 'The Strategist writes angles.md.'),
        ('plan', (folder / 'plan.json').is_file(), 'The Scribe and Art Director write plan.json.'),
        ('automatic_qa', bool(qa and qa['automatic'] == 'passed'), 'Run: brandking render <run>/plan.json --output <run>/delivery'),
        ('critic_review', (folder / 'delivery' / 'review.json').is_file(), 'The Critic reviews the slides, then run brandking signoff.'),
        ('ledger', _in_ledger(run_id), 'After 7 days run: brandking ledger add'),
    ]
    rows = [{'gate': name, 'done': done, 'next': None if done else hint} for name, done, hint in gates]
    pending = next((row for row in rows if not row['done']), None)
    return {'run': run_id, 'gates': rows, 'next': pending['next'] if pending else 'Nothing left. The loop is closed.'}


def _in_ledger(run_id):
    from .ledger import load
    return any(entry.get('id') == run_id for entry in load())


def signoff(delivery, reviewer, slides, notes='', approved=True):
    """Record a human or critic visual review. Only this moves visual out of pending."""
    delivery = Path(delivery)
    report_path = delivery / 'qa-report.json'
    if not report_path.is_file():
        raise PlanError(f'No qa-report.json in {delivery}.')
    report = read_json(report_path)
    if report['automatic'] != 'passed':
        raise PlanError('Automatic checks failed. Fix those before a visual review.')
    if not reviewer or not notes:
        raise PlanError('A review needs a reviewer and notes on what was inspected.')
    record = {'reviewer': reviewer, 'date': date.today().isoformat(), 'slides_inspected': slides,
              'notes': notes, 'approved': approved}
    write_json(delivery / 'review.json', record)
    report['visual'] = 'approved' if approved else 'changes requested'
    write_json(report_path, report)
    return record
