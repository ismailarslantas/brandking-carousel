"""Command line. Exit code 0 means clean, 1 means a check failed or the input is wrong.

Every command takes --json so an agent can read results without scraping prose.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import __version__, brandkit, deliver, gate, images, ledger, memory, runs
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
    result = deliver.render(args.plan, args.output, not args.no_remember)
    failed = result['status'] != 'passed'
    if args.json:
        return result, failed
    for item in result['problems']:
        _print_findings([item], 'rule' if 'rule' in item else 'check')
    if failed:
        print(f'Automatic checks FAILED. Inspect {result["output"]}. No carousel.zip was made.')
    else:
        print(f'Carousel exported to {result["output"]}. Automatic checks passed; visual review is still required.')
        if result['remembered']:
            print(f'Brand saved as "{result["remembered"]}". It will not be asked for again.')
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


def _cmd_brand_remember(args):
    fields = {'slug': args.slug, 'name': args.name, 'handle': args.handle, 'house': args.house,
              'primary': args.primary, 'accent': args.accent, 'dark': args.dark, 'light': args.light,
              'warm': args.warm, 'footer': args.footer, 'logo': args.logo, 'font': args.font,
              'title_font': args.title_font, 'font_name': args.font_name, 'title_font_name': args.title_font_name,
              'visual_structure': args.visual_structure, 'website': args.website, 'sector': args.sector}
    voice = {key: value for key, value in (('tone', args.tone), ('banned_words', args.banned_word)) if value}
    if voice:
        fields['voice'] = voice
    saved = memory.remember(fields, args.reference or ())
    if args.json:
        return saved, False
    print(f'Saved {saved["brand"].get("name")} as "{saved["slug"]}" in {saved["path"]}. It will not be asked for again.')
    if saved['scope'] == 'project':
        print('Saved for this project only, because the shared folder could not be written.')
    return None, False


def _cmd_brand_recall(args):
    saved = memory.recall(args.slug)
    if not saved:
        message = {'found': False, 'next': 'Ask for the brand details once, then run: brand remember'}
        if args.json:
            print(json.dumps(message, ensure_ascii=False, indent=2))
        else:
            print('No saved brand yet. Give the details once with: brand remember')
        return None, True
    if args.json:
        return {'found': True, **saved}, False
    print(memory.dumps(saved))
    return None, False


def _cmd_brand_list(args):
    rows = memory.list_brands()
    if args.json:
        return {'brands': rows}, False
    for row in rows:
        print(f'  {"*" if row["active"] else " "} {row["slug"]:<24} {row["name"]} ({row["scope"]})')
    if not rows:
        print('No saved brands yet.')
    return None, False


def _cmd_brand_forget(args):
    memory.forget(args.slug)
    if args.json:
        return {'forgotten': args.slug}, False
    print(f'Forgot {args.slug}.')
    return None, False


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


def _cmd_fit(args):
    result = images.fit(args.image, args.output, args.format, args.logo, args.lock, args.allow_crop, args.focus_y)
    if args.json:
        return result, False
    print(f'Saved {result["output"]} at {result["size"][0]}x{result["size"][1]}, cropped {result["cropped"]:.0%}.')
    return None, False


def _cmd_prompts(args):
    items = images.plan_prompts(args.plan, args.mode)
    if args.json:
        return {'prompts': items}, False
    print(images.prompts_markdown(read_json(args.plan), args.mode))
    return None, False


def _cmd_gate_confirm(args):
    record = gate.confirm(args.plan)
    if args.json:
        return record, False
    print(f'Recorded: the user stated the {record["plan"]} plan. {record["note"]}')
    return None, False


def _cmd_gate_check(args):
    record = gate.check()
    if args.json:
        return record, False
    print(f'Image generation allowed: the user stated the {record["plan"]} plan on {record["date"]}.')
    return None, False


def _cmd_doctor(args):
    findings = gate.doctor()
    failed = has_failures(findings)
    if args.json:
        return {'ok': not failed, 'findings': findings}, failed
    _print_findings(findings, 'check')
    return None, failed


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
    p.add_argument('--no-remember', action='store_true', help='do not save the brand after rendering')
    p = command('covers', _cmd_covers, 'render cover_options side by side')
    p.add_argument('plan')
    p.add_argument('--output', required=True)
    command('layouts', _cmd_layouts, 'list layouts and houses')
    command('doctor', _cmd_doctor, 'check Codex sign-in and the stated ChatGPT plan')
    p = command('fit', _cmd_fit, 'bring a generated image to an exact Instagram size')
    p.add_argument('image')
    p.add_argument('--output', required=True)
    p.add_argument('--format', default='post', choices=sorted(images.SIZES))
    p.add_argument('--logo', help='logo file to place in the footer band')
    p.add_argument('--lock', default='center', choices=['center', 'left'])
    p.add_argument('--allow-crop', action='store_true', help='allow a large crop, for text-free plates only')
    p.add_argument('--focus-y', type=float, default=.5, help='which part survives the crop, 0 keeps the top')
    p = command('prompts', _cmd_prompts, 'build image prompts from the copy in a plan')
    p.add_argument('plan')
    p.add_argument('--mode', default='plate', choices=['plate', 'full'])

    door = sub.add_parser('gate', help='record the ChatGPT plan needed for image generation').add_subparsers(dest='action', required=True)
    p = command('confirm', _cmd_gate_confirm, 'record the plan the user stated', door)
    p.add_argument('--plan', required=True)
    command('check', _cmd_gate_check, 'exit 1 unless a qualifying plan was stated', door)

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
    p = command('remember', _cmd_brand_remember, 'save a brand once; only given fields change', brand)
    for field in ('slug', 'name', 'handle', 'primary', 'accent', 'dark', 'light', 'warm', 'logo', 'font', 'title-font',
                  'font-name', 'title-font-name', 'visual-structure', 'website', 'sector', 'tone'):
        p.add_argument(f'--{field}')
    p.add_argument('--house', choices=sorted(HOUSES))
    p.add_argument('--footer', choices=['split', 'center'])
    p.add_argument('--banned-word', action='append')
    p.add_argument('--reference', action='append', help='a reference image to keep with the brand')
    p = command('recall', _cmd_brand_recall, 'show a saved brand; exit 1 when there is none', brand)
    p.add_argument('slug', nargs='?')
    command('list', _cmd_brand_list, 'list saved brands', brand)
    p = command('forget', _cmd_brand_forget, 'delete a saved brand', brand)
    p.add_argument('slug')

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
