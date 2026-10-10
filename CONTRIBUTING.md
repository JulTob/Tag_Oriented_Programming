# Contributing

Thank you for helping shape TOP. Three channels:

1. **Bugs & small fixes** → an **Issue**, then a focused PR. (Typos, kit bugs, doc clarifications.)
2. **Ideas & questions** → a **Discussion**. Scouting an idea is the **Recon** stage.
3. **A change to the paradigm** → a **STEP**.

## STEPs

A **STEP** — *Standard TOP Enhancement Proposal* — is how the paradigm evolves, one deliberate step at a time. **One STEP is one task, one purpose, one topic** — split anything larger.

The full process, the status pipeline (**Recon → Brief → Vetting → Cleared / Redacted → Deployed**), and the track layout live in [`steps/README.md`](steps/README.md). In short:

1. Copy `steps/STEP-template.md` into the right Desk folder as `STEP-<DESK>-<n>-<slug>.md`.
2. Fill it in and open a PR with **Status: Brief**.
3. The **Director** moves it to **Cleared** or **Redacted**, with the reason recorded in the STEP.

## Merging

All merges to `main` require the Director's review (`CODEOWNERS`). The Specification changes only through a Cleared — and ultimately Deployed — STEP.

## Working issue by issue

Open one issue for each concrete bug or design decision. A bug issue records
the affected commit, a reproducer, expected behavior, and acceptance criteria.
A design issue links its existing STEP and distinguishes recorded decisions
from open questions; do not allocate a second STEP for the same proposal.

Use one short-lived branch and one PR per issue. Start from current `main`
when possible. If work depends on an unmerged PR, name the prerequisite and
base the branch on it, so the diff contains only the new work. After the
prerequisite merges, update the branch, retarget the PR to `main`, and rerun
its checks. Preserve local work before updating a branch.

The PR describes the problem, resulting behavior, issue link, dependencies,
and validation. Use `Fixes #...` only when merging it completes the issue;
use `Refs #...` for proposals or partial work. Keep a proposal at Brief and
its PR in Draft while decisions remain open. Proposing a STEP does not
clear it. A behavior change that needs a STEP waits for Cleared before its
implementation merges; Deployed records the implementation merged and
validated on `main`.

Separate design proposals from implementation changes. If a PR accumulates
several purposes, split them into focused PRs and keep the original as a
linked coordination record until the split work is accounted for. Update
the title, description, and dependency list to describe the current diff.
Close superseded work with links to its replacements.

For a TopKit runtime fix, add a regression that demonstrates the failure
and run the complete existing suite on the proposed base:

```bash
PYTHONPATH=. python3 -m unittest discover -s tests
```

Run the oracle or relevant fuzz checks when the change affects composition,
membership, or lifecycle. Report commands and passed, failed, and skipped
results; do not reuse results from another branch. Documentation-only
changes need the existing document checks when their content affects those
checks. A merge does not authorize a release.

## License of contributions

By contributing you agree that your code is licensed **Apache-2.0** and your specification / STEP text **CC-BY-4.0**, consistent with this repository.
