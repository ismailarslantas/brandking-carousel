#!/usr/bin/env python3
"""Run Brandking from anywhere, setting up its two dependencies on first use.

Uses only the standard library so it can run before anything is installed. It keeps a
virtual environment in .brandking/venv inside the current project, and leaves the
current folder as the project, so plans and assets resolve against the user's work.
"""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent.parent


def has_dependencies():
    return all(importlib.util.find_spec(name) for name in ('PIL', 'fontTools'))


def environment_python():
    folder = Path.cwd() / '.brandking' / 'venv'
    python = folder / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        print('First run: setting up Brandking in .brandking/venv. This needs network access once.', file=sys.stderr)
        venv.EnvBuilder(with_pip=True).create(folder)
        subprocess.run([str(python), '-m', 'pip', 'install', '-q', '--disable-pip-version-check',
                        '-r', str(ROOT / 'requirements.txt')], check=True, stdout=sys.stderr)
    return python


def main():
    if has_dependencies():
        sys.path.insert(0, str(ROOT))
        from brandking.cli import main as run
        return run(sys.argv[1:])
    python = environment_python()
    env = {**os.environ, 'PYTHONPATH': str(ROOT)}
    return subprocess.run([str(python), '-m', 'brandking', *sys.argv[1:]], env=env).returncode


if __name__ == '__main__':
    raise SystemExit(main())
