# STEP-SPEC-19: A Tag Answers `in` for Its Sound Members

- **STEP:** SPEC-19
- **Desk:** spec
- **Title:** A Tag Answers `in` for Its Sound Members
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting
- **Created:** 2026-09-29

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

`agent in Tag` is True exactly when the Agent is a **sound member** of
the Tag: a member whose contract holds. That is the population the plain
loop walks, `len(Tag)` counts and `if Tag:` asks about, so the four
spellings agree. `agent in Tag[:]` is membership, sound or defective:
what `in` answered before. `agent in ~Tag` is True for a defective
member. Combined populations answer `in` from their sides, as sets do.
Nothing else moves: `isinstance`, Rip, views, Flags, published members
and `bool(agent)` keep their rules, and a Pin follows this one with the
Tag as the Agent. Only Agents that carry a
Postcondition are affected, whichever Tag made it; a Tag whose members
carry none changes nothing, so Ring 0's `in` stays membership, and Ring
2 narrows it to the sound. This STEP amends STEP-SPEC-4 item 6 and Ring
2's "membership unchanged".

## Motivation

Until now a defective member answered `agent in Wizard` True while `for
w in Wizard` skipped it, `len(Wizard)` did not count it and `if Wizard:`
did not see it. The Specification said so on purpose: "Membership and
the loop deliberately disagree for it: the loop is the line, and a
defective product is off the line." STEP-SPEC-4 item 6 said the same,
"`agent in Tag` stays true for a defective member."

Neither sentence was the Director's. Both were written by Claude in
commit d258d3b (2026-09-04) and approved in bulk with PR #3; STEP-4's
Decision quotes the Director on defective products and on the
spellings, not on `in`. Asked on 2026-09-29, the Director ruled:

> "'membership and iteration should disagree for defective members'
> that's not the director's ruling. An agent sneaked it in, probably.
> Correct that. Make in consistent with for/len/if. Fighter[:] provides
> the behaviour we need."

Four spellings of one population should give one answer. A program that
asks `if agent in Wizard:` and then walks `for w in Wizard:` should find
the same Agents on both sides of the question. The roster, sound or not,
has its own spelling one character away, `Wizard[:]`, and so does the
repair queue, `~Wizard`.

## Specification

1. **`agent in Tag` is sound membership.** It is True exactly when the
   Agent is a member of the Tag (membership closed upward through
   Shapes, as today) whose contract holds: every visible Postcondition on
   the Agent is true (`Contract.Holds(agent)`; also what `bool(agent)`
   answers, unless a Tag gives the Agent its own `__bool__`). It is the
   same population that `for a in Tag`, `len(Tag)` and `if Tag:` see.
   Soundness is the Agent's, whichever Tag made the promise: a member of
   two Tags with one broken promise is `in` neither.
2. **`agent in Tag[:]` is membership**: every member, sound or defective,
   what `in` was before this STEP. `agent in ~Tag` is True for a
   defective member and False for a sound one or a non-member.
3. **Combined populations** (§2.5) answer `in` from their sides as sets
   do: `Wizard | Fighter` holds the sound members of either, `Wizard[:]
   | Fighter[:]` everyone of either, `Wizard[:] - Sworn` the members of
   `Wizard` who are not sound in `Sworn`, and so on. On every
   population, `in` and the loop agree, except at interpreter teardown,
   when the weakly held Field is already empty while the Agent's own
   state still answers `in`.
4. **Unchanged.** `isinstance(agent, Tag)`, the has-been check.
   `del Tag[agent]` Rips any member, defective too. The Agent-bound view
   `Tag[agent]` (and `agent.Tag`) keeps its requirement, active
   membership sound or defective, and raises a Resolution Failure ("Tag
   is not active on this Agent") for a non-member. Flags and keywords in
   the Agent's seat: `Undead in ghoul` and `"Undead" in ghoul` ask for
   the keyword and stay True for a defective ghoul. Published members
   answer sound members only, as STEP-SPEC-10 says. `Contract.Status`
   and `bool(agent)`. Pins follow the same rule with the Tag as the
   Agent: `Wizard in Rare` is True for a sound pinned Tag, `Wizard in
   Rare[:]` for any pinned Tag, `Wizard in ~Rare` for a defective one.
5. **Where no Postcondition is visible on the Agent every member is
   sound.** Soundness is the Agent's (item 1), so a Tag whose members
   carry no promise, from it or from any other Tag, changes nothing:
   `in` is membership there. Ring 0's `in` is membership; Ring 2 narrows
   it to the sound. Inside a check the kit runs on an Agent, `agent in
   Tag` reads membership and `agent in ~Tag` is False for that Agent,
   exactly as `bool(agent)` answers True there, and the loop counts the
   Agent under check among the sound; every other member answers by its
   own contract. A promise never reads the contract it is part of. The
   checks the kit runs that way are a Postcondition, the tagging's
   quality check, a condition read by name, a published member's gate,
   and `Contract.Holds`, `Preconditions`, `Postconditions` and `Status`.
   A Precondition at the tagging's gate runs outside that guard and
   reads the sound and defective populations as code outside does, so
   one Pre can refuse at the gate and read True under `Contract.Status`.
   A guard that means membership is spelled `agent in Tag[:]`, which
   reads the same on every path; `agent in ~Tag` is no guard inside a
   promise.
6. **Conformance text.** The Ring 0 line becomes "membership and Base
   membership (`agent in Tag[:]`, and `agent in Tag` where no contract
   narrows it), closed upward, with a has-been check that survives
   Rip"; the Ring 2 line becomes "the plain loop and `in` as the sound
   population, `~Tag` the defective one, `Tag[:]` everyone".
   `CONFORMANCE.md` and the Specification's own ring list at its end
   say the same.
7. **Amendments.** STEP-SPEC-4 item 6 carries an amendment note under
   STEP-4 (the model of STEP-SPEC-7's Amendment table) quoting the
   ruling above and pointing here. The Specification's sentence
   "Membership and the loop deliberately disagree for it" goes; its
   example `assert broken in Wizard` becomes `assert broken in
   Wizard[:]`, with its comment; every document that said a defective
   member answers `in` is corrected.

Cost: `agent in Tag` reads the Agent's state and, once a Postcondition
is visible, runs the contract, the same work as `bool(agent)`. On
CPython 3.14 that is about 125 ns without a Postcondition and 360 ns
with one; `agent in Tag[:]` about 140 ns; `isinstance` about 100 ns.

## Rationale

One truth, four spellings. Soundness is already one thing in the kit:
`bool(agent)`, the sound population and a published member's gate all
ask "does every visible promise hold". `in` was the one spelling that
asked something else, and it is the spelling a program reaches for
first. The Director's rule, "consistent with
for/len/if", makes the plain Tag mean one population everywhere.

The roster keeps a spelling. `Tag[:]` already meant everyone in the
loop; now it means everyone under `in` too. "Does it carry the Tag,
sound or not?" is `agent in Wizard[:]`; "is it a Wizard fit to play?"
is `agent in Wizard`. Both read as they work.

The other direction, making the loop walk everyone, was ruled out when
STEP-SPEC-4 was cleared: the loop is the working population, with
`~Tag` one character away.

## Backwards compatibility

In 0.2.0a3 a defective member answered `agent in Tag` True; now False.
Programs that ask "does it carry the Tag?" write `agent in Tag[:]`.
Only Tags whose Agents carry a Postcondition are affected: where no
promise is visible every member is sound and nothing changes, which is
why every Ring 0 example in the Specification runs as it did.

A gate that reads another Tag, `@Pre def Is_A_Caster(agent): return
agent in Wizard`, now asks for a sound Wizard. A defective Wizard is
refused at that gate and nothing is applied; before, the Tag applied
and the tagging reported the standing defect. Membership alone is
`agent in Wizard[:]`. `Contract.Status` and `Contract.Preconditions`
read that same Pre under the re-entrancy guard, where `in` is
membership, so they can answer True for an Agent the gate refused. That
the gate runs outside the guard is older than this STEP; whether it
should join the others is the Director's call.

A guard inside a Postcondition, `if agent not in Sworn: return True`,
works as it did, because there `in` reads membership (item 5). A guard
in a Precondition at the gate reads the sound population, so it now
skips a defective member where before it read on; spell it `Sworn[:]`.
The documents spell every guard `Sworn[:]`, which says what it reads.
A guard on the defective view, `if agent in ~Other: return True`, let a
Postcondition pass at tagging before, because the tagging's quality
check ran outside the guard and the view read a nested run of the
contract; now that check runs under the guard, the Agent under check
is never in `~Other` from inside, and the promise is read. Spell it `Other[:]`, or read the
promise by name.

The oracle model asserts membership, sound membership and defective
membership apart. The tests that asserted a defective member `in` its
Tag now assert `in Tag[:]` and `not in Tag`.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Keep the disagreement: `in` membership, the loop sound | Rejected by the Director: "that's not the director's ruling. [...] Make in consistent with for/len/if." |
| The loop walks everyone, `in` and the loop agree on membership | Rejected when STEP-SPEC-4 was cleared: the loop is the working population |
| A Tag in an operator seat means everyone in its Field, so `Wizard \| Fighter` reads as `Wizard[:] \| Fighter[:]` | Set aside by the Director: "Wizard \| Fighter should mean a valid fighter OR a valid Wizard, so it is present. A simple isinstance(wizard) or isinstance(fighter) can satisfy the other cases, which are rare and not good practice. Wizard[:] \| Fighter[:] would mean broken wizards or good wizards or broken fighters or good fighters, all active agency, all members in the sets (broken or not)." The sound population in every seat, `in` included (item 3) |
| `in` raises for a defective member | Rejected: a question, not a failure; `~Tag` and `Tag[:]` say the other populations |
| A fourth spelling for sound membership (`agent in +Wizard`) | Rejected: `Tag[:]` already exists; the Director: "Fighter[:] provides the behaviour we need" |
| `in` inside a Postcondition, or any check run under the guard, reads soundness too | Rejected: a promise would read the contract it is part of; `bool(agent)` already answers True there |

## Acceptance requirements

Covered by `tests/test_topkit.py::SoundMembershipTests`: a broken member
in `Tag`, `Tag[:]` and `~Tag`; the same through a Shape; in every
combined population, where `in` and the loop agree; after repair; after
Rip, with the has-been check and the view's requirement; a Tag whose
members carry no Postcondition unchanged, and one that follows its
Agents' promises from another Tag; a Pin with the Tag as the Agent;
Flags in the Agent's seat; `in` and `~Tag` inside a promise; a gate
reading another Tag, and the same Pre under `Contract.Status`; a Scope
over a defective Tag the Agent carried. The tests of STEP-SPEC-4,
-9 and -10 that asserted a defective member `in` its Tag now assert the
new answers. The oracle (`tests/oracle_topkit.py`, `Assert_Target`)
checks membership, sound membership and defective membership on every
transition. The guides' blocks and the Specification's examples run.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-29, per
> the Director's ruling on the sentence "Membership and the loop
> deliberately disagree for it" and on STEP-SPEC-4 item 6: "'membership
> and iteration should disagree for defective members' that's not the
> director's ruling. An agent sneaked it in, probably. Correct that.
> Make in consistent with for/len/if. Fighter[:] provides the behaviour
> we need." Recorded as a new STEP, shipped in 0.2.0a4 with the Field
> algebra, amending STEP-SPEC-4 item 6 and Ring 2's "membership
> unchanged"; Ring 0 keeps `in` as membership, because Ring 0 has no
> contracts and there every member is sound.
