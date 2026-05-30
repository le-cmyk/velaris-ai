---
applyTo: "**/*.py"
description: "Use when running Python commands, installing packages, or executing scripts — always use the project .venv virtual environment."
---

# Python Virtual Environment

Always use the project's `.venv` virtual environment for all Python work.

## Setup (first time)

```bash
/opt/homebrew/bin/python3 -m venv .venv
source .venv/bin/activate
```

## Rules

- **Never** use the system Python or any other interpreter directly.
- **Always** activate the venv before running Python or installing packages:
  ```bash
  source .venv/bin/activate
  ```
- **Always** install packages inside the venv:
  ```bash
  python -m pip install <package>
  ```
- When running scripts, use the venv Python explicitly if needed:
  ```bash
  .venv/bin/python script.py
  ```
- Do **not** use `pip3` or `/opt/homebrew/bin/python3` directly after setup — use `python` and `pip` from within the activated venv.
