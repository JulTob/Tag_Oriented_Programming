# Releasing TopKit

TopKit is published to PyPI as **`topkit`**:
https://pypi.org/project/topkit/. The name was claimed with `0.2.0a3` on
2026-09-21. Only the Director holds the PyPI account and its tokens, so
the steps below are written to be run by the Director and by nobody
else.

## Once: the account and the token

1. Register at https://pypi.org/account/register/ and confirm the email.
2. Turn on two-factor authentication under Account settings. PyPI
   refuses uploads without it.
3. Make a token under Account settings, API tokens. Now that the project
   exists, scope it to **`topkit`** only. PyPI shows the token once.

Keep the token where no chat, file or repository will ever see it. A
token that has been pasted anywhere is spent: revoke it and make a new
one. Nothing in this repository stores a token, and nothing should.

## Every release

Work in a fresh clone of `main` and a virtual environment. Homebrew and
distribution Pythons refuse system-wide installs, and the clone keeps
stray files out of the distribution.

```
git clone https://github.com/JulTob/Tag_Oriented_Programming.git topkit-release
cd topkit-release
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip build twine
```

Check before building:

```
PYTHONPATH=. python3 -m unittest discover -s tests -t .
```

- The suite says `OK`. It runs the examples, every runnable block of the
  Specification and the guides, and a short walk of the oracle.
- The oracle at size passes: `PYTHONPATH=. python3 tests/oracle_topkit.py
  --seeds 50 --steps 1200 --population 18`.
- `CHANGELOG.md` has an entry for this version, and it is no longer
  marked unreleased.
- `pyproject.toml`'s `version` matches that entry and is higher than the
  last one on PyPI.

Build, check, upload:

```
python3 -m build                    # writes dist/
python3 -m twine check dist/*       # both files must say PASSED
TWINE_USERNAME=__token__ TWINE_PASSWORD='<the token>' python3 -m twine upload dist/*
```

Twine prints the release page when it succeeds. Then `deactivate`, and
the clone can be deleted.

## What cannot be undone

A version number, once uploaded, can be yanked but never reused. Bump
`version` in `pyproject.toml` before any further upload; a second upload
of the same number is refused.

## Version numbers

`0.2.0aN` while the Specification is still moving. The version rises
when a STEP is Deployed, not when the code changes: the kit tracks the
paradigm, not the other way round. An alpha is not installed by a plain
`pip install topkit`; users who want it say `pip install --pre topkit`.
