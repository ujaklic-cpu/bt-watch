# Contributing

Thanks for wanting to help! This project is small; the basics below keep things smooth.

## How to propose changes
- Open an issue first for non-trivial changes so we can agree on scope.
- Fork and branch off `main`; use clear branch names (e.g., `feat/rssi-threshold`).
- Keep commits focused and with meaningful messages.

## Development setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- Run a quick syntax check before opening a PR: `python -m compileall .`
- If you touch dependencies, update `requirements.txt`.

## Pull requests
- Describe what changed and why.
- Note any manual testing performed.
- Keep PRs small; prefer incremental improvements over large rewrites.

## Code of conduct
See `CODE_OF_CONDUCT.md`. By participating, you agree to follow it.
