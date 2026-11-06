"""Write .codex/agents/*.toml from .claude/agents/*.md, so both tools share one source.

Run after changing a specialist. A test fails if the two drift apart.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse(path):
    text = path.read_text(encoding='utf-8').replace('\r\n', '\n')
    _, header, body = text.split('---\n', 2)
    fields = dict(line.split(': ', 1) for line in header.strip().split('\n'))
    return fields['name'], fields['description'], body.strip()


def render(name, description, body):
    assert "'''" not in body and '"' not in description
    return f'name = "{name}"\ndescription = "{description}"\ndeveloper_instructions = \'\'\'\n{body}\n\'\'\'\n'


def expected():
    return {f'{path.stem}.toml': render(*parse(path)) for path in sorted((ROOT / '.claude/agents').glob('*.md'))}


def main():
    target = ROOT / '.codex/agents'
    target.mkdir(parents=True, exist_ok=True)
    for name, content in expected().items():
        (target / name).write_text(content, encoding='utf-8', newline='\n')
    print('Wrote', sorted(expected()))


if __name__ == '__main__':
    main()
