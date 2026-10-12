# STEP-SPEC-42: Ordinary Condition Names in the Python Profile

- **STEP:** SPEC-42
- **Desk:** spec
- **Title:** Ordinary Condition Names in the Python Profile
- **Author:** Codex, recording the Director's condition-name ruling
- **Status:** Brief
- **Created:** 2026-10-12
- **Issue:** [#74](https://github.com/JulTob/Tag_Oriented_Programming/issues/74)

## Summary

Preconditions and Postconditions use ordinary Contribution names. The
Python profile refuses a declared name beginning and ending with `__`,
because conditions expose plain boolean verdicts while Python protocol
seats carry special-method behavior.

## Proposed specification

1. A Precondition or Postcondition cannot use a Python dunder name,
   including an otherwise unused dunder.
2. Refusal is a Declaration Failure at Tag declaration, before class
   construction or Target effects. The failure identifies the Tag and
   the declared Contribution name.
3. The rule applies to Preconditions, Postconditions, and both stacked
   decorator orders, on Tags and Pins. The binding name decides; the
   function's original name does not.
4. Supported late assignment refuses before replacing the existing
   binding. Scanning also refuses a forbidden condition marked in place
   before its first scan; this does not define a general late-declaration
   or cache invalidation policy (#96).
5. Ordinary conditions and permitted special-method Actions retain their
   meanings. The reserved Agent truth seat is a separate ruling recorded
   by STEP-SPEC-40 and issue #71.

## Rationale and compatibility

STEP-SPEC-14 makes a condition a plain boolean read by name, never a
callable proxy. Python could distinguish explicit attribute reads from
implicit special-method lookup, but TOP selects a single predictable
meaning for the Contribution's name.

A program migrates a condition named `__bool__` to an ordinary name such
as `Safe`. A program may continue to use allowed protocol Actions such as
`__add__`, `__enter__` and `__exit__` under their existing rules.

## Acceptance

- Cover truth, kernel, write, finalizer and unused dunder names with all
  condition decorator orders and both Tag/Pin declarations.
- Verify refusal precedes class/Target effects and preserves a late
  binding, including namespace aliases.
- Retain ordinary conditions and permitted protocol Actions.
- Run supported suites and the existing condition/Constant regressions.

### Decision

The Director selected **“ban dunders in conditions”** on 2026-10-12.
This focused record leaves its formal STEP status at Brief for review;
it does not amend the Specification or STEP-SPEC-14's existing status.
