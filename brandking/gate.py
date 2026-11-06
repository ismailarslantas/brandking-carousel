"""Image gate. ChatGPT image generation in Codex is for Plus or higher.

The gate records what the user states about their plan. It cannot verify a
subscription, and it never reads Codex credentials: OpenAI decides what an account
can actually do. Rendering and auditing need no plan at all.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
import shutil
import subprocess

from .core import PlanError, project_dir, read_json, write_json

QUALIFYING = ('plus', 'pro', 'business', 'edu', 'enterprise')
NOT_QUALIFYING = ('free', 'go')
EXPLANATION = (
    'Image generation in this workflow uses ChatGPT image generation inside Codex, signed in '
    'with a ChatGPT Plus plan or higher (Plus, Pro, Business, Edu or Enterprise). '
    'Rendering, auditing and writing prompts still work without it.'
)


def gate_file():
    return project_dir() / '.brandking' / 'chatgpt-plan.json'


def confirm(plan):
    """Record the plan the user stated. Refuses plans below Plus."""
    plan = (plan or '').strip().lower()
    if plan in NOT_QUALIFYING:
        raise PlanError(f'The {plan} plan does not qualify. {EXPLANATION}')
    if plan not in QUALIFYING:
        raise PlanError(f'Unknown plan {plan!r}. Choose one of: {", ".join(QUALIFYING + NOT_QUALIFYING)}.')
    record = {'plan': plan, 'confirmed_by': 'user statement', 'date': date.today().isoformat(),
              'note': 'Not verified with OpenAI. Actual access is decided by the account.'}
    path = gate_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, record)
    return record


def check():
    """Return the recorded confirmation, or raise when there is none."""
    path = gate_file()
    if not path.is_file():
        raise PlanError(f'No plan confirmed yet. Ask the user, then run: gate confirm --plan <plan>. {EXPLANATION}')
    record = read_json(path)
    if record.get('plan') not in QUALIFYING:
        raise PlanError(f'The recorded plan does not qualify. {EXPLANATION}')
    return record


def codex_status():
    """Report how Codex is signed in, without touching any credential file."""
    binary = shutil.which('codex')
    if not binary:
        return {'installed': False, 'signed_in': None, 'method': None,
                'detail': 'Codex CLI is not on PATH. The desktop app may still be installed.'}
    try:
        done = subprocess.run([binary, 'login', 'status'], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as error:
        return {'installed': True, 'signed_in': None, 'method': None, 'detail': f'Could not ask Codex: {error}'}
    text = ' '.join(line for line in (done.stdout + ' ' + done.stderr).splitlines() if 'PATH aliases' not in line).strip()
    lowered = text.lower()
    method = 'chatgpt' if 'chatgpt' in lowered else 'api_key' if 'api key' in lowered else None
    signed_in = False if 'not logged in' in lowered else (True if method else None)
    return {'installed': True, 'signed_in': signed_in, 'method': method, 'detail': text}


def doctor():
    """Check the setup. A check that cannot run is skipped with its reason."""
    findings = []
    status = codex_status()
    if not status['installed']:
        findings.append({'check': 'codex_cli', 'severity': 'skipped', 'detail': status['detail']})
    elif status['signed_in'] is False:
        findings.append({'check': 'codex_sign_in', 'severity': 'fail', 'detail': 'Codex is not signed in. Run: codex login'})
    elif status['method'] == 'api_key':
        findings.append({'check': 'codex_sign_in', 'severity': 'fail',
                         'detail': 'Codex is using an API key, which bills API rates. Sign in with ChatGPT instead.'})
    elif status['method'] == 'chatgpt':
        findings.append({'check': 'codex_sign_in', 'severity': 'pass', 'detail': 'Codex is signed in with ChatGPT.'})
    else:
        findings.append({'check': 'codex_sign_in', 'severity': 'skipped', 'detail': f'Could not read the sign-in method: {status["detail"]}'})
    findings.append({'check': 'chatgpt_plan_verified', 'severity': 'skipped',
                     'detail': 'A plan cannot be verified from here. Only the user and OpenAI know it.'})
    try:
        record = check()
        findings.append({'check': 'chatgpt_plan_stated', 'severity': 'pass',
                         'detail': f'The user stated the {record["plan"]} plan on {record["date"]}.'})
    except PlanError as error:
        findings.append({'check': 'chatgpt_plan_stated', 'severity': 'warn', 'detail': str(error)})
    findings.append({'check': 'gate_location', 'severity': 'pass', 'detail': str(Path(gate_file()))})
    return findings
