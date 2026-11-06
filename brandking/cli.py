"""Command line. Exit code 0 means clean, 1 means a check failed or the input is wrong.

Every command takes --json so an agent can read results without scraping prose.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import __version__, brandkit, deliver, ledger, runs
from .core import PlanError, read_json
from .lint import has_failures, lint_plan
from .plan import LAYOUTS, validate
from .styles import HOUSES


def _print_findings(findings, key):
    marks = {'fail': 'FAIL', 'warn': 'WARN', 'pass': ' ok ', 'skipped': 'SKIP'}
    for item in findings:
        where = f' slide {item["slide"]}' if 'slide' in item else ''
        print(f'  {marks[item["severity"]]} {item[key]}{where}: {item["detail"]}')


def _cmd_lint(args):
    plan = read_json(args.plan)
    validate(plan)
    findings = lint_plan(plan)
    failed = has_failures(findings)
    if args.json:
        return {'ok': not failed, 'findings': findings}, failed
    _print_findings(findings, 'rule')
    print('Copy lint: ' + ('FAILED' if failed else f'clean, {len(findings)} warning(s)'))
    return None, failed


def _cmd_check(args):
    result = deliver.check(read_json(args.plan))
    if args.json:
        return result, not result['ok']
    _print_findings([f for f in result['lint'] if f['severity'] != 'pass'], 'rule')
    _print_findings([f for f in result['audit'] if f['severity'] != 'pass'], 'check')
    print(f'Lint {result["lint_summary"]}\nAudit {result["audit_summary"]}')
    print('Ready to render.' if result['ok'] else 'Not ready.')
    return None, not result['ok']


def _cmd_render(args):
    result = deliver.render(args.plan, args.output)
    failed = result['status'] != 'passed'
    if args.json:
        return result, failed
    for item in result['problems']:
        _print_findings([item], 'rule' if 'rule' in item else 'check')
    if failed:
        print(f'Automatic checks FAILED. Inspect {result["output"]}. No carousel.zip was made.')
    else:
        print(f'Carousel exported to {result["output"]}. Automatic checks passed; visual review is still required.')
    return None, failed


def _cmd_covers(args):
    ranking = deliver.covers(args.plan, args.output)
    if args.json:
        return {'ranking': ranking}, False
    for row in ranking:
        print(f'  {row["option"]}  {row["score"]}/5  {row["headline"]}')
    print(f'Compare them at phone size: {Path(args.output) / "cover-sheet.jpg"}. The ranking is an editing aid, not a forecast.')
    return None, False


def _cmd_layouts(args):
    data = {'layouts': LAYOUTS, 'houses': {k: v['description'] for k, v in HOUSES.items()}}
    if args.json:
        return data, False
    for name, text in LAYOUTS.items():
        print(f'  {name:<10} {text}')
    print('Houses:')
    for name, house in HOUSES.items():
        print(f'  {name:<10} {house["description"]}')
    return None, False


def _cmd_brand_init(args):
    folder = brandkit.init_kit(args.slug, args.name, args.primary, args.accent, args.handle, args.house)
    if args.json:
        return {'kit': str(folder)}, False
    print(f'Brand kit created at {folder}. Run: brandking brand check {folder}')
    return None, False


def _cmd_brand_check(args):
    result = brandkit.check_kit(args.path)
    failed = has_failures(result['findings'])
    if args.json:
        return result, failed
    _print_findings(result['findings'], 'check')
    return None, failed


def _cmd_run_new(args):
    folder = runs.new_run(args.id)
    if args.json:
        return {'run': str(folder)}, False
    print(f'Run folder created at {folder}. Fill in brief.md first.')
    return None, False


def _cmd_run_status(args):
    result = runs.status(args.id)
    if args.json:
        return result, False
    for gate in result['gates']:
        print(f'  [{"x" if gate["done"] else " "}] {gate["gate"]}')
    print(f'Next: {result["next"]}')
    return None, False


def _cmd_signoff(args):
    record = runs.signoff(args.delivery, args.reviewer, args.slides, args.notes, not args.changes_requested)
    if args.json:
        return record, False
    print(f'Visual review recorded: {"approved" if record["approved"] else "changes requested"}.')
    return None, False


def _cmd_ledger_add(args):
    entry = {k: getattr(args, k) for k in ('id', 'hook_type', 'format', 'house', 'hypothesis', *ledger.METRICS)
             if getattr(args, k) is not None}
    saved = ledger.add(entry, args.file)
    if args.json:
        return saved, False
    print(f'Logged {saved["id"]}.')
    return None, False


def _cmd_ledger_report(args):
    result = ledger.report(args.file)
    if args.json:
        return result, False
    print(f'{result["posts"]} post(s) logged. {result["note"]}')
    for field, rows in result['groups'].items():
        if rows:
            print(f'\nBy {field}:')
        for row in rows:
            print(f'  {row["value"]:<18} posts {row["posts"]:<3} saves/1k {row["saves_per_1k"]:<7} sends/1k {row["sends_per_1k"]:<7} {row["confidence"]}')
    return None, False


def parser():
    root = argparse.ArgumentParser(prog='brandking', description='Brandking Carousel: plan, render, audit and learn from Instagram carousels.')
    root.add_argument('--version', action='version', version=__version__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--json', action='store_true', help='print machine-readable JSON')
    sub = root.add_subparsers(dest='command', required=True)

    def command(name, func, help_text, parent=sub):
        made = parent.add_parser(name, parents=[common], help=help_text)
        made.set_defaults(func=func)
        return made

    p = command('lint', _cmd_lint, 'check the copy of a plan')
    p.add_argument('plan')
    p = command('check', _cmd_check, 'lint and audit a plan without writing files')
    p.add_argument('plan')
    p = command('render', _cmd_render, 'render, audit and package a delivery')
    p.add_argument('plan')
    p.add_argument('--output', required=True)
    p = command('covers', _cmd_covers, 'render cover_options side by side')
    p.add_argument('plan')
    p.add_argument('--output', required=True)
    command('layouts', _cmd_layouts, 'list layouts and houses')

    brand = sub.add_parser('brand', help='create and check brand kits').add_subparsers(dest='action', required=True)
    p = command('init', _cmd_brand_init, 'create a kit in private/brands', brand)
    p.add_argument('slug')
    p.add_argument('--name', required=True)
    p.add_argument('--primary', required=True)
    p.add_argument('--accent', required=True)
    p.add_argument('--handle', default='')
    p.add_argument('--house', default='sovereign')
    p = command('check', _cmd_brand_check, 'measure how a palette behaves', brand)
    p.add_argument('path')

    run = sub.add_parser('run', help='track a carousel through its gates').add_subparsers(dest='action', required=True)
    p = command('new', _cmd_run_new, 'create a run folder', run)
    p.add_argument('id')
    p = command('status', _cmd_run_status, 'show which gates are open', run)
    p.add_argument('id')

    p = command('signoff', _cmd_signoff, 'record the visual review of a delivery')
    p.add_argument('delivery')
    p.add_argument('--reviewer', required=True)
    p.add_argument('--slides', required=True, help='which slides were inspected, for example 1-6')
    p.add_argument('--notes', required=True)
    p.add_argument('--changes-requested', action='store_true')

    book = sub.add_parser('ledger', help='log and compare real results').add_subparsers(dest='action', required=True)
    p = command('add', _cmd_ledger_add, 'log the results of a post', book)
    p.add_argument('id')
    p.add_argument('--file')
    for field in ('hook-type', 'format', 'house', 'hypothesis'):
        p.add_argument(f'--{field}')
    for metric in ledger.METRICS:
        p.add_argument(f'--{metric}', type=int)
    p = command('report', _cmd_ledger_report, 'compare results by hook type, format and house', book)
    p.add_argument('--file')
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        data, failed = args.func(args)
    except (PlanError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        if getattr(args, 'json', False):
            print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False))
        else:
            print(f'ERROR: {error}', file=sys.stderr)
        return 1
    if data is not None:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 1 if failed else 0
