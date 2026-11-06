"""Kept so older commands and portable recipes still work: python carousel.py --plan x --output y"""
import argparse
from pathlib import Path
import sys

from brandking.cli import main


if __name__ == '__main__':
    shim = argparse.ArgumentParser(description=__doc__)
    # A portable recipe keeps its plan beside this file; the repository uses the demo.
    shim.add_argument('--plan', default='plan.json' if Path('plan.json').is_file() else 'examples/demo.json')
    shim.add_argument('--output', default='outputs/carousel')
    args = shim.parse_args()
    sys.exit(main(['render', args.plan, '--output', args.output]))
