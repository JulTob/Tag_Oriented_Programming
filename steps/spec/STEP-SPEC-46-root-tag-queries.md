# STEP-SPEC-46: Root Tag Queries Without a Field

- **STEP:** SPEC-46
- **Desk:** spec
- **Title:** Root Tag Queries Without a Field
- **Author:** Codex, recording the Director's 2026-10-15 ruling
- **Status:** Brief
- **Created:** 2026-10-15

## Summary

Root `Tag` has no Field to enumerate, yet it can answer whether a given
object is a sound Agent. Root `~Tag` asks whether an Agent is free but
Post-defective, and root `Tag[:]` asks whether TOP successfully actualized
the object. These are membership queries, not global Agent populations.

## Motivation

Every ordinary Tag has a Field, so `agent in Fighter`, `agent in ~Fighter`
and `agent in Fighter[:]` answer three useful questions. Root `Tag` has no
Field. Still, a Rogue may have Gains without entering the failed Tag; an
Agent may leave its last Field; and an arrested Agent has a distinct
Safehouse status. The program needs the same questions about one known
object without keeping every Agent in a global root Field.

## Specification

1. TOP records when an object is **first successfully actualized** as an
   Agent. This fact survives later Rip and cannot be inferred merely from
   an attached provisional State: a refused first Gate or failed host
   actualization leaves the untouched host unactualized. A later refused
   Gate does not erase an earlier successful actualization. A Tag class
   actualized as a Pin Target is also an Agent for these queries. Whether
   calling root `Tag(host)` can actualize a host without Field admission
   remains open under STEP-SPEC-32; this Brief does not define that call.
2. `agent in Tag[:]` asks whether that object has been successfully
   actualized. It includes a Rogue whose Gains or Imprint failed after
   actualization, an Agent after its last ordinary Rip, and an arrested
   Agent. It excludes an untouched host and a host whose first Gate was
   refused before actualization. Root `Tag[:]` is a query over an object,
   **not** a Field containing or retaining every Agent.
3. `agent in Tag` asks whether it is actualized, free of pending Rip work,
   and sound under its current visible Posts. `agent in ~Tag` asks whether
   it is actualized and free, but those Posts are defective. An arrested
   Agent is in neither root sound nor root defective query, while still
   answering true to `agent in Tag[:]`. Root `Tag[...]` separately shows
   Agents with saved Rip work in the Safehouse; it does not become a Field.
   A sound Rogue can therefore answer true to `agent in Tag` without
   belonging to the Tag whose training failed.
4. `isinstance(agent, Tag)` means that the object has **ever** become an
   Agent through successful actualization. It remains true after Rip and
   during arrest. A provisional State left by a refused initial Gate does
   not make it true. This historical question is independent of current
   Posts and Safehouse custody. Ordinary `isinstance(agent, Fighter)`
   keeps its existing Tag-specific history rule.
5. A root query can be the **right-hand membership filter** of a concrete
   population's intersection or difference. For example,
   `Fighter[:] & ~Tag` walks Fighters and keeps those currently free and
   Post-defective; `Fighter[:] - ~Tag` excludes them. The root operand
   answers membership for each Agent without a global scan. Ordinary
   Field walk timing and Tagging order remain in force.
6. Root `Tag`, `~Tag` and `Tag[:]` cannot be walked or measured: iteration
   and `len(...)` raise a clear resolution error. A TOP population union
   containing one of these root queries also raises, as does a walk led
   by one on the left of `&` or `-`. Consequently population truth of
   `~Tag` and `Tag[:]` cannot be computed and raises the same error.
   Python's separate type-union spelling, such as `Tag | None`, keeps
   its normal meaning.
7. `bool(Tag)` retains root Tag's own contract-truth rule
   (STEP-SPEC-40). It does not search for an Agent or evaluate all
   Agents' Posts. This STEP does not make root Tag eligible as a Pin
   Target or add a new source of root Posts. Root `Tag[...]` retains its
   distinct Safehouse meaning. This STEP does not define `del Tag[:]`
   or bulk Safehouse retry.

```python
class Host:
    pass

class Fighter(Tag):
    @Post
    def Ready(agent):
        return agent.ready

ari = Host()
ari.ready = False
try:
    Fighter(ari)
except Postcondition.Ready:
    pass                        # Fighter admitted Ari, then its Post failed

assert ari in Tag[:]            # TOP successfully actualized Ari
assert ari in ~Tag              # Ari is free but Post-defective
assert ari not in Tag
assert ari in (Fighter[:] & ~Tag)

ari.ready = True
assert ari in Tag               # the same Agent is sound now
assert ari not in ~Tag
```

## Rationale

Membership on a known object needs only its actualization marker, current
Posts and pending Rip status. It needs no root Field, global registry or
extra strong reference to an Agent. The Safehouse stays a separate status:
an interrupted teardown is neither a sound Agent nor an ordinary
Post-defective Agent awaiting repair. A concrete Field supplies the
candidates when an algebra query needs to walk.

## Backwards compatibility

This is a root-only exception to ordinary Tag Field populations and their
lengths in STEP-SPEC-40. It broadens the root `isinstance(..., Tag)`
history rule beyond the “ever a member” wording in Specification §0.3:
successful actualization with no Field admission now counts. Ordinary
Tags' Fields, Posts, Rip and algebra remain unchanged. The runtime does
not implement these root queries yet; this Brief is a design record.

## Dependencies

The sound-membership repair in #216 supplies the ordinary membership
predicate this root query should follow. The Safehouse implementation of
STEP-SPEC-32 supplies the arrest distinction and `Tag[...]`. The
first-successful-actualization marker must be set only after actualization
succeeds. #233 tracks the focused implementation and regressions.

## Alternatives considered

- Give root `Tag` a Field of all Agents: a global registry would retain or
  scan Agents and would blur ordinary Field admission with actualization.
- Treat arrested Agents as `~Tag`: a pending Rip needs Safehouse cleanup,
  a different resolution protocol from a failed Post.
- Use provisional State as the actualization test: a refused first Gate
  can leave State before the host has become an Agent.

### Decision

On 2026-10-15 the Director chose membership-only root `Tag`, `~Tag` and
`Tag[:]` queries; a separate root Safehouse; and right-hand filtering of
concrete populations. This Brief records that direction. STEP clearance
and implementation remain separate review steps.
