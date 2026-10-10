## What does this change?

<!-- One issue, one purpose. Explain the problem and resulting behavior.
     A change to observable TOP semantics needs a Cleared STEP before its
     implementation merges — see CONTRIBUTING.md. Proposals start at Brief. -->

## Issue and dependencies

<!-- Fixes #... only if this PR completes the issue; otherwise Refs #... .
     Link the STEP for a design change. Name the base and prerequisite PRs;
     say what remains open. -->

## Validation

<!-- Commands run on this branch and their results, including skips.
     For a runtime fix, show that the regression failed before the fix. -->

## Checklist

- [ ] This PR has one purpose and links its issue and dependencies
- [ ] Required checks pass on this branch; runtime changes run `PYTHONPATH=. python3 -m unittest discover -s tests`
- [ ] Any implementation changing TOP semantics links a Cleared STEP; an uncleared proposal remains Draft
- [ ] Spec / docs updated where needed
- [ ] I agree to the contribution licenses (Apache-2.0 for code, CC-BY-4.0 for spec/STEPs)
