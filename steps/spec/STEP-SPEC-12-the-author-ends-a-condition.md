# STEP-SPEC-12: Conditions Are Sticky; the Author Ends Them

- **STEP:** SPEC-12
- **Desk:** spec
- **Title:** Conditions Are Sticky; the Author Ends Them
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting
- **Created:** 2026-09-21

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A Tag's Preconditions and Postconditions are sticky, like its
contributions: Rip does not touch them. A promise that outlives its Tag
fails loud, never silently. When a condition should end, **the author
ends it**, in one of two visible ways:

- a **guard in the condition**, one line of flow control that says which
  membership the condition follows: `if agent not in Wizard: return
  True`. It can follow any membership at all: the Tag's own, another
  Tag's, a keyword on a Tag, or the Tag under an Underlay;
- an **explicit deletion from the Tag's own `@Rip` protocol**,
  `Contract.Delete(agent, "Has_Book")`, one deliberate name at a time. A
  name that is not a condition on the Agent is a Resolution Failure.

This replaces STEP-SPEC-11 (Redacted), which made Rip remove the ripped
Tag's conditions and restore the prior one.

## Motivation

STEP-SPEC-11 answered a real need, a Rogue Wizard with an empty
spellbook should not stay defective under a role it left, with an
automatic law at Rip. The Director rejected the mechanism: "Rip
protocols can be dangerous. They could be implemented with an 'if
target in MyTag' flow control." Three things were wrong with deletion
at Rip:

1. Rip should do one thing, end membership. It is the one act nothing
   can roll back, so every extra rule at Rip widens what can go wrong
   there.
2. A promise that quietly disappears fails silently; a promise that
   stays too long fails loud. The loud failure is the safe one.
3. The law needed chain surgery to get right (an Overlay that took the
   ripped condition as its Underlay kept calling it), which is exactly
   the clever machinery the project's principles warn against.

The Director, on the replacement: "Add some examples of the 'The author
writes it' guardrail for the conditions. more flexible this way." And:
"Didn't we establish that the real good practice was either explicit
deletion on rip protocol or a field check in the condition?"

## Specification

1. **Sticky.** Rip removes membership and runs the Tag's `@Rip`
   protocols. It does not remove, restore or rebind any Precondition or
   Postcondition. §0.7 says so beside "contributions are sticky".
2. **The guard.** A condition may read any membership and decide for
   itself whether it applies: `agent in Tag`, `"Keyword" in Tag`,
   `agent in ~Tag`. Returning `True` when it does not apply is the
   idiom. This is ordinary flow control; nothing in the kernel treats
   it specially.
3. **The guarded Underlay.** An `@Underlay` condition that should skip a
   Tag the Agent has left calls `base()` only while that Tag is active:
   `underneath = base() if agent in Alive else True`. The chain is never
   rebuilt by the kernel.
4. **Explicit deletion.** `Contract.Delete(agent, *names)` ends the named
   conditions on the Agent (Preconditions and Postconditions alike, so a
   `@Requirement` ends whole). A name that is not a condition on the
   Agent raises a Resolution Failure: an author who ends a promise must
   be ending a real one. It is written to be called from the Tag's own
   `@Rip` protocol; it works for a pinned Tag as well.
5. **Spelling.** `Contract.Delete(agent, "Has_Book")` joins §0.8, beside
   the other `Contract` queries. `@Delete` on a Tag member keeps its
   meaning (remove a visible contribution at application); the two share
   the word because both are the author's explicit removal.
6. **Re-application.** A Tag re-applied after its own Rip replaces its
   own condition silently, as before (§0.7); the origin stamp on a bound
   check remains for that rule only.

## Rationale

Consistent with STEP-SPEC-10: when a rule is about membership, it is
checked where it is written, once. The guard puts the check in the
condition; the deletion puts the end in the protocol that ends the role.
Both are one line the next reader can see. Neither costs anything at
Rip, neither guesses, and a forgotten line fails loud (a stale promise
flags the Agent) rather than silently (a vanished promise flags nothing).

## Backwards compatibility

Under STEP-SPEC-11's kit, a Rogue Agent lost the ripped Tag's conditions
automatically. Under this STEP it keeps them until the author ends them.
Programs that relied on the automatic removal add the guard or the
deletion; the Guide (pattern 9) and the Contracts Guide (§8) show both.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Delete at Rip and restore the prior condition (STEP-SPEC-11) | Redacted by the Director: "Rip protocols can be dangerous" |
| Delete at Rip and rebuild the Underlay chain | Rejected with it: chain surgery at the one irreversible act |
| The kernel skips a condition whose origin Tag is inactive | Set aside: the same answer with no visible line; the Director chose flexibility over an automatic law |
| A modifier for a promise that survives Rip (`@Post @Lasting`) | Unneeded: surviving is now the default |
| `@Rip @Delete` stacked on a condition name | Set aside: the call in the teardown says the same thing without a new mark combination |

## Acceptance requirements

Covered by `tests/test_topkit.py::StickyConditionTests`,
`examples/crew_access.py` (pattern 6) and the Contracts Guide §8, which
the test suite runs.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-21, per
> the Director's words above.
