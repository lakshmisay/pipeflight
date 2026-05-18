# Release Checklist

1. Update the version in `pyproject.toml`.
2. Install release tools:

```bash
uv pip install build twine
```

3. Run tests:

```bash
python -m pytest
```

4. Build distributions:

```bash
python -m build
```

5. Validate package metadata:

```bash
python -m twine check dist/*
```

6. Upload to TestPyPI first:

```bash
python -m twine upload --repository testpypi dist/*
```

7. Install from TestPyPI in a clean environment and run the example.
8. Upload to PyPI:

```bash
python -m twine upload dist/*
```

## First Public Repo Tasks

- Reserve `pipeflight` on PyPI.
- Add a GIF or screenshot of `pipeflight record orders.parquet`.
- Add examples for schema drift, freshness failure, null explosion, and replay.
