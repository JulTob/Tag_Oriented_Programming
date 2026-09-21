# STEP-SPEC-11: Conditions End With Membership

- **STEP:** SPEC-11
- **Desk:** spec
- **Title:** Conditions End With Membership
- **Author:** Julio Toboso (@JulTob)
- **Status:** Redacted
- **Created:** 2026-09-07
- **Redacted:** 2026-09-21

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A Tag's gates and promises are the Tag's. When an Agent leaves the Tag's
Field, they end: Rip removes the Tag's Preconditions and Postconditions
from the Agent, and a condition the Tag had laid over another Tag's (a
Shape over its Base, or one independent Tag over another) gives that
prior condition back. A Rogue Agent keeps what it became, its Actions
and Records, and is no longer held to a role it left.

## Motivation

Until now conditions were sticky like contributions: Rip a Wizard and
the Agent was still held to Wizard's promises, so a Rogue Wizard with an
empty spellbook stayed "defective" under a role it no longer carried.
That contradicts STEP-SPEC-10, where what the Agency imposes ends when
the Agent leaves it. The Director raised the case ("an imprint may add a
lot of conditions, but all of them may be only conditional to the tag")
and asked for the alternatives to be evaluated: a `@Rip` that deletes
conditions by name, a language shortcut to rip them all, a modifier, a
codeword, or "rip all and select which to save". The automatic law
needs none of them.

## Specification

1. Rip removes every Precondition and Postcondition the ripped Tag bound
   on the Agent.
2. Where the ripped Tag's condition was laid over a prior condition of
   the same name (a Shape over its Base with or without `@Underlay`, an
   independent Tag over another), the prior condition whose Tag is still
   active becomes visible again. If no such prior exists, the name is
   free.
3. Ripping a Tag whose condition is not the visible one (another Tag has
   laid over it) changes nothing: the visible condition is the other
   Tag's composition, and it ends with that Tag. **Where that composition
   is an `@Underlay` that calls the ripped Tag's check, see the open
   question below: §3 as written is not yet the whole law.**
4. Ripping a Base is still refused while a Shape requires it (§0.7), so
   a Shape's `@Underlay` condition never loses the Base check it calls.
5. Pins follow the same rule with the Tag as Agent.
6. Contributions remain sticky (§0.7). Only conditions end.

## Rationale

A condition is a necessity the Tag declares, not something the Agent
became. Necessary to enter, necessary to stay; once the Agent is no
longer in, there is nothing to stay in. A necessity that must outlive a
role belongs to a Tag the Agent still carries: "selecting which
conditions to save" is the Geometry, not a list. With the automatic law,
the per-name deletes, the shortcut and the modifier are all unneeded, and
the `@Rip` protocol stays what it is, a teardown.

## Backwards compatibility

A program that relied on a Ripped Tag's promise still binding the Agent
now sees the Agent as sound under that name. No spelling changes.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Sticky conditions, deleted by name in the teardown (`@Rip @Delete`) | Rejected: a line per promise, and one forgotten line leaves a ghost promise on a Rogue Agent |
| A modifier for a promise that survives Rip (`@Post @Lasting`) | Set aside: no real use that a second Tag does not express better |
| A language shortcut to rip all conditions (`del ~Tag[agent]`) | Rejected: the common case should need no spelling; an obscure one is worse than a line |
| `@Public + @Rip`, `@Pre + @Post + @Rip` | No coherent meaning; a Rip is a teardown protocol and already a callable Action |
| A reserved codeword | Against the namespace principle (§0.8) |
| Resolve an `@Underlay`'s `base()` by walking the chain at every call | Set aside in favour of rebinding at Rip: the same answer, off the hot path (see the open question) |

## Open question · an Overlay that took the condition as its Underlay

*Raised by the Director: "what about the case of an overlay taking over a
condition? And using it as underlay? What then? Do we delete the new
condition with the same name? Or do we make a jump in the calling node to
skip that beat? Is that feasible?"*

### The case

`Elf` lays an `@Underlay` promise over `Alive`'s promise of the same
name. `Elf` is not a Shape of `Alive`; they are independent Tags that met
on one Agent.

```python
class Alive(Tag):

    @Post
    def Fine(agent):
        return agent.alive


class Elf(Tag):

    @Post
    @Underlay
    def Fine(agent, base):
        return base() and agent.pointy_ears


Alive(ari); Elf(ari)
del Alive[ari]                # Ari is a Rogue Agent of Alive
ari.alive = False             # a promise she no longer carries
bool(ari)                     # False today; should be True
```

The visible `Fine` is Elf's, so §3 leaves it alone, and Elf's `base()`
still calls Alive's check from inside its closure. Ari is defective under
a role she left. The law of §1 holds for the name Rip can see and fails
for the one it cannot.

The declared-Geometry case is already safe: a Shape's `@Underlay` reaches
its Base, and §4 refuses to Rip a Base a Shape requires. The hole is
exactly where the Underlay was **opportunistic**: `Elf` took whatever
happened to be under the name, and no Form says `Elf` needs `Alive`.

### Delete the new condition?

Refused. `Elf` is still a member and `Fine` is Elf's own promise. Ripping
`Alive` would silently disarm a promise `Alive` never made and `Elf`
never gave up, which is the opposite of §1: **only the ripped Tag's
conditions end**. It is also unrecoverable, since re-applying `Alive`
could not bring Elf's promise back.

### Jump the dead beat — recommended

The Director's second reading, and the right one. Every bound check
already records what it was laid over (`__topkit_prior__`), so the
conditions under one name are a chain. Rip rebuilds that chain instead of
only its visible end: the dead beats come out, and each survivor is bound
again over the nearest **live** prior. `Elf.Fine`'s `base()` then calls
whatever is genuinely underneath now, which is what `Elf` would have been
bound to had `Alive` never been there. A condition is laid over what is
there; when what it was laid over leaves, it is laid over what remains.

The floor of the same law: **an `@Underlay` condition whose chain empties
ends with it.** TopKit already refuses to install an `@Underlay` with no
prior of that name (a Resolution Failure). Keeping one alive afterwards
with an invented `base()` would contradict the rule that made it
installable. Answering `True` would make an `and` promise vacuous;
answering `False` would flag an Agent for a promise nobody holds. There
is no honest third answer, so the condition ends. Read forwards it is
"an `@Underlay` needs an underneath"; read backwards it is the same
sentence.

This is one law in three lines:

1. A ripped Tag's conditions come out of the chain, visible or not.
2. Each surviving `@Underlay` is bound again over the nearest live prior.
3. A surviving `@Underlay` with no live prior comes out too, and so on
   upward.

A plain override is untouched, as §3 already says: it never called the
prior, and the prior is only history in its chain.

### Is it feasible? Yes, and it costs nothing at call time

The alternative reading of "a jump in the calling node" is to resolve
`base()` by walking the chain **on every call**. That works, but it puts
the walk on the hot path, where conditions run at every tagging and every
use of a published member. Rebinding at Rip pays once, in the rare act,
and leaves the call exactly as fast as it is today.

The one thing missing is that a bound check does not keep the function it
was made from, so it cannot be bound again. Stamping the declaring
function beside the origin and the prior is one attribute, set where
`__topkit_origin__` already is. Rip then rebuilds each affected chain
bottom-up.

The change this makes visible, stated plainly: `Elf.Fine`'s `base()` may
come to mean a different Tag's check than it did when `Elf` applied. That
is the intended reading of "laid over what is there", and the Director
should see it written down before it is law.

*Held for the Director's decision. Nothing in the kernel is changed for
this question yet.*

## Acceptance requirements

Covered by `tests/test_topkit.py::ConditionsEndWithMembershipTests`. The
open question above is not covered; it has no test until it is decided.

---

### Decision *(filled by the Director)*

> Status set to **Redacted** on 2026-09-21, because the Director
> reviewed the mechanism against the goals of the project and rejected
> deletion at Rip: "I am doubtful about the spec 11. Rip protocols can be
> dangerous. They could be implemented with an 'if target in MyTag' flow
> control." On the replacement: "Add some examples of the 'The author
> writes it' guardrail for the conditions. more flexible this way." And,
> confirming the practice: "Didn't we establish that the real good
> practice was either explicit deletion on rip protocol or a field check
> in the condition?"
>
> What this STEP wanted, a Rogue Agent not held to a role it left, is
> kept; the automatic law is not. STEP-SPEC-12 records the replacement:
> conditions are sticky, and the author ends them, by a guard in the
> condition or by `Contract.Delete` from the Tag's own `@Rip` protocol.
> The open question below is moot under it: nothing is deleted at Rip,
> so no chain is left half-alive; an Underlay that should skip a Tag the
> Agent has left says so in its own line.
