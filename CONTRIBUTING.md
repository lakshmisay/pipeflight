# Contributing to Pipeflight

Thanks for helping build Pipeflight.

The project goal is narrow: make data pipeline incidents reproducible. Before adding a feature, ask whether it improves the incident bundle, replay flow, or developer trust.

## Local Setup

```bash
uv venv
uv pip install -e ".[dev]"
python -m pytest
```

## Development Rules

- Keep v0.1 small.
- Prefer simple files over services.
- Do not add dashboards, auth, orchestration, or cloud-specific behavior yet.
- Add tests for behavior that changes the incident bundle.
- Keep CLI output short and scriptable.

## Good First Issues

- Improve `report.html`.
- Add more example contracts.
- Add Markdown report output.
- Add better schema drift explanations.
- Add PII masking for captured failing rows.
