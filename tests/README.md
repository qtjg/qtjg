# Tests for `qtjg` profile tools

Run from the repository root:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## What's covered

- `test_repo_pulse.py` — `tools/repo_pulse.py`: the `collect_pulse` / `render_human`
  contract, the `--json` CLI flag, and the not-a-git-repo error path.

## Conventions

- Tests are zero-dependency (standard library only).
- Each test module imports the tool under test by adding `tools/` to `sys.path`,
  so the suite runs without an install step.
