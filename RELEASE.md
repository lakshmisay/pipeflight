# Release Checklist

1. Update the version in `pyproject.toml`.
2. Confirm the repository is clean:

```bash
git status --short
```

3. Run tests:

```bash
uv run pytest --basetemp .pytest_tmp -p no:cacheprovider
```

4. Build distributions from a clean `dist/` directory:

```bash
uv run python -m build
```

5. Validate package metadata:

```bash
uv run python -m twine check dist/*
```

6. Upload to TestPyPI first:

```bash
uv run python -m twine upload --repository testpypi dist/*
```

7. Install from TestPyPI in a clean environment and run the example.
8. Upload to PyPI:

```bash
uv run python -m twine upload dist/*
```

9. Verify the public install:

```bash
pip install pipeflight
pipeflight --help
```

Note: PyPI badges may show unavailable until the first real PyPI release is published.

## First Public Repo Tasks

- Reserve `pipeflight` on PyPI.
- Confirm the GitHub Actions CI badge is passing.
- Confirm README images render on GitHub and PyPI.
