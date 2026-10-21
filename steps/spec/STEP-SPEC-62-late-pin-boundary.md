# STEP-SPEC-62: The Late Pin Boundary

- **STEP:** SPEC-62
- **Desk:** spec
- **Title:** When may an ordinary Tag be marked a Pin?
- **Author:** Claude, laying the 2026-10-20 record before the Director
- **Status:** Brief
- **Created:** 2026-10-20

> One STEP, one topic. If this grows a second purpose, split it into another STEP.

## Summary

Two readings of the late-`@Pin` rule exist on the record from the same
day, and they disagree on one case. This STEP lays both before the
Director with the verified consequences of each, so the Specification
carries exactly one law.

**Agreed by both readings** (and enforced on PR #170's branch today):
`Pin(T)` refuses when `T` has a Shape, a current Field member, or a
declared `@Tool` naming it as a kind; a refused mark leaves the Tag
ordinary; restating the mark on a Pin is a no-op; Fields never mix Agents
and Tags (§1.9).

**The disputed case** — a Tag that trained Agents which have all since
left its Field:

- **Reading A, "a Pin is born, not made"** (the Director, in session,
  2026-10-20): *"a tag should not become a pin. That breaks the strong
  type-tag sense, and breaks the contract made when building a tag."*
  Under A, any ordinary-Tag use commits the Tag for good; the empty-Field
  historical case **refuses**.
- **Reading B, "free again when nothing depends on it"** (the Director,
  on the PR #170 branch, same day, commit `3037302`): *"An empty Tag may
  be marked even if it previously trained Agents that have since left its
  Field."* Under B, the historical case **accepts**; only current
  commitments block.

## Verified consequences of each reading

Probed on the #170 branch and `main` (2026-10-20):

| Case | Reading A | Reading B (branch today) |
| --- | --- | --- |
| Train, Rip all, `Pin(T)` | refuse | accept |
| `isinstance(agent, T)` after such a mark | n/a | stays `True` for the old trainee of a now-Pin |
| A `@Tool` assigned late (not in a class body) naming `T` | refuse (one mark at `Tool(...)` creation) | **hole today**: the assignment door is unguarded (only class-body Tools are noted) |
| The naming Tool's Tag dies and is collected, then `Pin(T)` | refuse (commitment never lapses — consistent) | **inconsistent today**: still refuses, though nothing current depends on `T`; under B's own logic it should accept (open draft #271 fixes exactly this) |
| `Pin(T)` from inside `T`'s own Imprint (Field still empty mid-Tagging) | refuse (the turn itself commits) | **hole today**: accepted, a plain object then sits in a Pin's Field (issue #286; draft #287 proposes a reservation) |
| Cost | no weak tracking; marks live on the Tag | weak identity tracking retained |

Neither reading is free: A is simpler and closes every door with two
plain marks, but it makes a Tag's first use irreversible even for
scratch Tags in tests and notebooks. B matches "explicit beats implicit"
(a visible, current commitment blocks; history alone does not), but it
owes three repairs to be consistent with itself: the assignment door,
the dead-owner unblock (#271), and the in-flight window (#286/#287).

## Specification

To be written as the chosen reading, in §1.9, once the Director rules.
Both candidate texts exist in history: Reading A in #170's reverted
commit `3185898`; Reading B in the branch's current `_refuse_late_pin`
and the §1.9 sentence of commit `3037302`.

## Rationale

The rule guards the law that Fields never mix Agents and Tags, and the
contract a Tag's author makes at declaration. The disputed case decides
what that contract covers: the Tag's whole life (A) or its current
commitments (B).

## Backwards compatibility

Reading B is today's branch behaviour; adopting A refuses programs that
re-purpose an emptied Tag as a Pin. No code on `main` implements either
yet (`main` still accepts every late mark).

## Alternatives considered

- A per-Tag opt-in (`@Pin` only valid in a declaration window measured in
  statements or time) — rejected as magic; neither explicit nor dumb.
- Allowing conversion with a diagnostic warning — rejected: a Field that
  can mix levels is not a law with a warning, it is no law.

---

### Decision *(filled by the Director)*

Status set to **____** on **____** because **____**.
The disputed case resolves as reading **____**.
