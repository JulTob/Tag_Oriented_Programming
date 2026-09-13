# Releasing TopKit

TopKit is published to PyPI as **`topkit`**. The name is free and
unclaimed; the first upload is what reserves it. Only the Director holds
the PyPI account and the token, so the steps below are written to be run
by the Director and by nobody else.

## Reserving the name

One upload of the current alpha claims `topkit` for the project. An
alpha is a real release, so PyPI will not hand the name to anyone else
afterwards.

```
python3 -m pip install --upgrade build twine
python3 -m build                    # writes dist/
python3 -m twine check dist/*       # metadata must PASS
python3 -m twine upload dist/*      # asks for the API token
```

The token is a PyPI **project-scoped API token** once the project exists;
the very first upload needs an account-scoped one. Nothing in this
repository stores it, and nothing should.

Publishing is irreversible in the way that matters: a version number can
be yanked but never reused. Upload the alpha only when the branch is the
one you mean to publish.

## Before any upload

- `python3 -m unittest tests.test_topkit` passes.
- Every runnable block of the Specification, the Guide and the Contracts
  Guide runs clean.
- `CHANGELOG.md` has an entry for this version.
- `pyproject.toml`'s `version` matches that entry.

## Version numbers

`0.2.0aN` while the Specification is still moving. The version rises
when a STEP is Deployed, not when the code changes: the kit tracks the
paradigm, not the other way round.
