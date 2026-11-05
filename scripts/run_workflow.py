"""Validate dispatch input as a data path, never as executable shell text."""
import os
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from carousel import render

if __name__ == '__main__':
    plan = (ROOT / os.environ.get('CAROUSEL_PLAN', 'examples/demo.json')).resolve()
    if not plan.is_relative_to(ROOT) or plan.suffix.lower() != '.json':
        raise SystemExit('Plan must be a JSON file inside the repository.')
    render(plan, ROOT/'outputs/carousel')
