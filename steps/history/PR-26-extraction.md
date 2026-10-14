# Extraction register for PR #26 and PR #77

Recorded 2026-10-14. The mixed implementation in [#26](https://github.com/JulTob/Tag_Oriented_Programming/pull/26)
and its reconciliation [#77](https://github.com/JulTob/Tag_Oriented_Programming/pull/77) are design history, not merge
candidates. Their branches are retained. Each remaining Brief now has an
independent documentation-only Draft PR, based on main `fcea45f`.
Closing the source PRs neither clears these proposals nor deploys their code.

## Remaining Briefs

Each extraction retains the original proposal verbatim, preceded by
current-law boundaries and immutable source links. None depends on merging
the frozen branches. Dependencies between the designs remain explicit.

| STEP | Topic | Preservation PR | Tracking |
| --- | --- | --- | --- |
| SPEC-20 | Conditions Across Independent Tags | [#187](https://github.com/JulTob/Tag_Oriented_Programming/pull/187) | [#10](https://github.com/JulTob/Tag_Oriented_Programming/issues/10) |
| SPEC-23 | Field Filters | [#188](https://github.com/JulTob/Tag_Oriented_Programming/pull/188) | [#38](https://github.com/JulTob/Tag_Oriented_Programming/issues/38) |
| SPEC-24 | Field Rip and the End of a Tag | [#189](https://github.com/JulTob/Tag_Oriented_Programming/pull/189) | [#35](https://github.com/JulTob/Tag_Oriented_Programming/issues/35) |
| SPEC-25 | Commands to a Population | [#190](https://github.com/JulTob/Tag_Oriented_Programming/pull/190) | [#183](https://github.com/JulTob/Tag_Oriented_Programming/issues/183) |
| SPEC-26 | A Shape Keeps No Base Hostage | [#191](https://github.com/JulTob/Tag_Oriented_Programming/pull/191) | [#184](https://github.com/JulTob/Tag_Oriented_Programming/issues/184) |
| SPEC-27 | The Deletion Protocol of a Tag | [#192](https://github.com/JulTob/Tag_Oriented_Programming/pull/192) | [#34](https://github.com/JulTob/Tag_Oriented_Programming/issues/34) |
| SPEC-28 | Category Error | [#193](https://github.com/JulTob/Tag_Oriented_Programming/pull/193) | [#185](https://github.com/JulTob/Tag_Oriented_Programming/issues/185) |
| SPEC-29 | The Population Algebra | [#194](https://github.com/JulTob/Tag_Oriented_Programming/pull/194) | [#186](https://github.com/JulTob/Tag_Oriented_Programming/issues/186) |
| SPEC-32 | The Arrest | [#195](https://github.com/JulTob/Tag_Oriented_Programming/pull/195) | [#36](https://github.com/JulTob/Tag_Oriented_Programming/issues/36) |

## Work already carried elsewhere

- **SPEC-22 Links:** [#171](https://github.com/JulTob/Tag_Oriented_Programming/pull/171) owns the active proposal and implementation; its [source](https://github.com/JulTob/Tag_Oriented_Programming/blob/65c6e87e1374cdef9834793b8c1f4b723d7a887f/steps/spec/STEP-SPEC-22-links.md) already includes #77's distinction between skipped and failed Pair cleanup. This register does not clear Links.
- **SPEC-30 Requirement:** [the Cleared STEP](../spec/STEP-SPEC-30-retire-requirement.md) and removal are on main. Do not copy #26's old version over it.
- **SPEC-31 Scope:** [the Cleared STEP](../spec/STEP-SPEC-31-retire-scope.md) and retirement are on main. #77's [historical amendment](https://github.com/JulTob/Tag_Oriented_Programming/blob/7802fd75c07165aa4ea61267df290ba1fa2ff57f/steps/spec/STEP-SPEC-31-retire-scope.md) remains an archived reconciliation; it does not amend the current Cleared document. `try`/`finally` exposes the explicit Rip's failure policy; it does not choose arrest or rollback.
- **Absorbing inversion and live walks:** [SPEC-38](../spec/STEP-SPEC-38-absorbing-defective-population.md) / [#63](https://github.com/JulTob/Tag_Oriented_Programming/pull/63) and [SPEC-35](../spec/STEP-SPEC-35-population-walk-membership.md) / [#65](https://github.com/JulTob/Tag_Oriented_Programming/pull/65) carry these focused changes. The former STEP-29 collision was resolved by giving absorbing inversion SPEC-38.
- **Agent/Tag truth:** [SPEC-40](../spec/STEP-SPEC-40-agent-contract-truth.md) / [#160](https://github.com/JulTob/Tag_Oriented_Programming/pull/160) supersede the historical truth rows. Tag truth is its own visible Posts; cardinalities stay population questions.
- **Warning wording and private Field mutation:** [#52](https://github.com/JulTob/Tag_Oriented_Programming/pull/52) and [#67](https://github.com/JulTob/Tag_Oriented_Programming/pull/67) carry those focused changes. They do not clear Category Failure or the rest of the algebra.

## The catalog and reconciliation coverage

The complete [original catalog](https://github.com/JulTob/Tag_Oriented_Programming/blob/1947490209d8eddf158c2bc6c0e6b538ddb6f9e0/steps/CATALOG-tag-algebra.md)
and [reconciled catalog](https://github.com/JulTob/Tag_Oriented_Programming/blob/7802fd75c07165aa4ea61267df290ba1fa2ff57f/steps/CATALOG-tag-algebra.md)
remain available as immutable archives. Their dated branch-status tables
include obsolete Scope, Requirement and Tag-truth claims; they are not a
current API guide. The source commits retain all original implementation
changes, examples and tests for historical comparison; none is imported here.

Every file changed by #77 is accounted for:

- SPEC-24, 26, 27, 29 and 32: recovered from the reconciled source in the PRs above.
- SPEC-22: carried into #171.
- Historical SPEC-31: archived at the exact source link above; current law stays intact.
- Catalog: archived at the reconciled source link above.

The extraction preserves per-Agent freeze/retry separately from unresolved
bulk continuation, interruption and reapplication during failed cleanup
(SPEC-32 questions 16, 17 and 14). Preservation does not choose those rules.

## Suggested design review order

Start with independent Base/Shape membership (SPEC-26), then failed-Rip
obligations (SPEC-32), whole-Field cleanup (SPEC-24), and the remaining stop
and reset choices (SPEC-27). Review population algebra (SPEC-29), Filters
(SPEC-23), and population writes (SPEC-25) together at their shared boundaries.
Independent condition diagnostics (SPEC-20) and Category Failure (SPEC-28)
can be reviewed separately. This is a design order, not a merge dependency.
