# Releasing TopKit

TopKit is published to PyPI as **`topkit`**:
https://pypi.org/project/topkit/. The name was claimed with `0.2.0a3` on
2026-09-21. Only the Director publishes it.

Releases go out through **Trusted Publishing**: PyPI trusts one workflow
in this repository, `.github/workflows/release.yml`, and GitHub proves to
PyPI, for each run, that an upload comes from it. So there is no token to
keep, lose or leak. The workflow runs when the Director publishes a
GitHub Release, and it uploads only after the Director approves it.

## Once: connect PyPI to this repository

1. **The PyPI account.** It exists, with two-factor authentication on;
   PyPI refuses uploads without it.
2. **The trusted publisher, on PyPI.** Your projects → `topkit` →
   Manage → Publishing → Add a new publisher → GitHub, with exactly:
   - Owner: `JulTob`
   - Repository name: `Tag_Oriented_Programming`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
3. **The environment, on GitHub.** The repository's Settings →
   Environments → New environment, named `pypi`:
   - Required reviewers: `JulTob`. Leave "Prevent self-review" off: the
     Director approves his own releases.
   - Deployment branches and tags: Selected branches and tags → add a tag
     rule `v*`.
4. **Old tokens.** Once a release has gone through this way, delete the
   API tokens under PyPI's Account settings → API tokens. Nothing needs
   them any more.

## Every release

1. **Prepare it in a pull request**, reviewed and merged like any other:
   - `pyproject.toml`'s `version` is higher than the last one on PyPI.
   - `CHANGELOG.md` has a heading for that version, dated:
     `## 0.2.0a5 — 2026-10-20`, no longer "unreleased".
   - The README's links are absolute GitHub links: PyPI shows the
     README, and a relative link is broken there.
2. **Publish a GitHub Release.** Releases → Draft a new release:
   - Choose a tag: type `v` and the version, for example `v0.2.0a5`, and
     create it on publish, from `main`.
   - Title `TopKit 0.2.0a5`; for the notes, paste the changelog entry.
   - Tick "Set as a pre-release" for an alpha.
   - Publish release.
3. **The workflow checks everything.** Under Actions, "Release to PyPI"
   runs:
   - the suite on Python 3.12, 3.13 and 3.14, and the oracle at its
     audited size;
   - a check that the tag is `v` plus `pyproject.toml`'s version and that
     the changelog has a dated heading for it;
   - the build, and `twine check --strict` on both files.
   If any step fails, nothing is uploaded.
4. **Approve the upload.** The run stops at "Publish to PyPI" and waits:
   Review deployments → tick `pypi` → Approve and deploy. Only then does
   it upload.
5. **Check** that https://pypi.org/project/topkit/ shows the new version.

If a check fails before the upload, the version number is still free:
fix it in a pull request, delete the GitHub Release and its tag, and
publish the release again.

## By hand, if GitHub cannot do it

Make an API token on PyPI for this one upload (Account settings → API
tokens, scoped to `topkit` only). Keep it where no chat, file or
repository will ever see it; a token that has been pasted anywhere is
spent, so revoke it and make a new one.

Work in a fresh clone of `main` and a virtual environment. Homebrew and
distribution Pythons refuse system-wide installs, and a fresh clone
keeps stray files, and an older `dist/`, out of the upload.

```
git clone https://github.com/JulTob/Tag_Oriented_Programming.git topkit-release-<version>
cd topkit-release-<version>
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip build twine
PYTHONPATH=. python3 -m unittest discover -s tests -t .
PYTHONPATH=. python3 tests/oracle_topkit.py --seeds 50 --steps 1200 --population 18
python3 -m build                    # writes dist/
python3 -m twine check dist/*       # both files must say PASSED
python3 -m twine upload -u __token__ dist/*
```

`__token__` is typed as it stands: it is PyPI's user name for token
logins. Twine then asks for a password: paste the token there, where it
is not shown and not kept. Never put the token on the command line,
where the shell history would keep it. Twine prints the release page
when it succeeds. Then `deactivate`, delete the clone, and delete the
token on PyPI.

## What cannot be undone

A version number, once uploaded, can be yanked but never reused. Bump
`version` in `pyproject.toml` before any further upload; a second upload
of the same number is refused.

## Version numbers

`0.2.0aN` while the Specification is still moving. The version rises
when a STEP is Deployed, not when the code changes: the kit tracks the
paradigm, not the other way round.

While no final release exists, a plain `pip install topkit` installs the
newest alpha: pip follows PEP 440 and takes a pre-release when no final
release matches. Once a final release is on PyPI, a plain pip installs
that, and users who want an alpha say `pip install --pre topkit`.
`pip index versions topkit` hides alphas unless given `--pre`.
