# STEP-SPEC-32: The Arrest

- **STEP:** SPEC-32
- **Desk:** spec
- **Title:** The Arrest
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-09

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

When a teardown fails, the Agent still leaves the Tag. It is held in the
Tag's safehouse, **arrested**. An arrested Agent does nothing. When it
tries to act, the safehouse first runs the teardowns that have not
passed. If they all pass, the Agent is free, and the act goes on. If one
fails, the act is refused before it starts. The program can also retry
by hand, `del Wizard[ari]`, or end the Agent, `del Wizard[...]`. One rule
covers a Rip, a Field Rip and a deletion.

```python
class Sentry(Tag):

    @Rip
    def Hand_In_Badge(agent):
        agent.locker.Store(agent.badge)   # raises while the locker is jammed


Sentry(guard)
del Sentry[guard]       # Hand_In_Badge fails: the guard leaves Sentry, arrested
                        # (the Rip reports the failure, rule 3)

guard.Patrol()          # an act: the safehouse runs Hand_In_Badge first;
                        # still jammed, so the Arrested Access Failure,
                        # and Patrol never runs

locker.Unjam()
guard.Patrol()          # Hand_In_Badge passes: the guard is free, then Patrol runs
```

**Words used here.**
- **Teardown**: a `@Rip` protocol of a Tag (§3.1). A Tag may have any
  number of them.
- **Safehouse**: where a Tag keeps the Agents whose teardowns failed,
  `Wizard[...]` (STEP-SPEC-18, amendment E, on `step-19-sound-in`).
  `Tag[...]` is every Agent any Tag keeps.
- **Arrested**: kept in a safehouse. The Agent is not a member of the
  Tag any more, and it can do nothing until its teardowns pass.
- **Free** (or liberated): out of every safehouse.
- **Triage**: `del Wizard[...]`, which ends the kept Agents without their
  teardowns (STEP-SPEC-18, amendment F).

## Motivation

The Director ruled on 2026-10-09, answering STEP-SPEC-24's open question
1:

> "A failed rip sends you to the safehouse, and you leave the tag. A
> dangerous agent gets arrested if the rip protocols were not followed
> (it still has a gun and badge! that's a security issue!) it is not
> allowed anything except rerunning rips or deletion. The safehouse of a
> tag should keep the rip protocols of the tag and be able to run them
> on the agents. A successfully rip agent can become a rogue agent. An
> arrested agent cannot do anything (access its own records, or taking
> its own actions included) until successful rip is performed. If any
> activity is tried by the arrested agent (access records or taking
> actions) a rip protocol of the safehouse is launched. If it passes the
> rip, it is then liberated and performs the action as normal. If it
> does not pass the house's rip, an error is raised before it tries to
> perform the action. […] If it is in the safehouse, it is not in the
> tag, so a failed rip does not block leaving membership. It does leave
> the tag, and loses access to reports and operations. It just gets them
> arrested until it follows protocol. same quarantine philosophy of
> contracts and posts but stricter. a single rule for Rip and a Field
> Rip."

And, the same day, on the details:

> "When ALL rips succeed (there is no limit on how may protocols it
> should have). also it applies for all safehouses except Tag[...]
> itself."

> "There is no reading without rip. Only errors. If the code calls for
> acts, then that is a very good moment to ratify if the rip can pass.
> The Rip was taken already, just failed. Reiterating the rip is not
> magic, is a prerequisite. […] Obviously anything called from the rip
> protocol would not trigger that. exempt the teardown."

> "If it's quarantined and arrested it should not be touched. It is
> infectious, it is arrested, and jailed. it does not get visits. […]
> Rip is already a violent act, and everything that breaks that premise
> means it should not have been a rip, but a record mutation. […] A
> rogue agent may be just retired, which is huge as a change, but an
> agent you lost control on is a fuck up. Any contact with it should end
> in arrest."

> "A teardown that fails because something outside is down — yeah...
> that's an architectural problem, not a top paradigm one. If teardown
> is possible, your protocol should be effective."

> "I meant every act **by an arrested Agent**, not every act ever. Any
> Action or record access. Moving the agent around or checking what tags
> it belongs to are not necessarily triggers for that. Just if the agent
> wants to do something."

> "`del Wizard[ari]` runs the Rip again; `del Wizard[...]` forcefully
> deletes the Agent."

Two rules on `step-19-sound-in` give way:
- **STEP-SPEC-18, amendment D**: a failed Rip is refused and rolled back,
  so the Agent is a member again. Under this STEP the Agent leaves.
- **STEP-SPEC-18, amendment E**: a kept Agent "stays a member of its
  Tags". Under this STEP it is not a member.

Amendment F, triage, stays.

## Specification

1. **A failed teardown ends membership anyway.** *Decided.* When a
   teardown fails during a Rip (`del Wizard[ari]`), a Field Rip
   (`del Wizard[:]`, STEP-SPEC-24) or the Agent's deletion, the Agent
   still leaves the Tag. It is out of `Wizard[:]`, `Wizard` and
   `~Wizard`, and it loses the Tag's published Reports and Operations, as
   after any Rip (§0.7).
2. **It is arrested in the Tag's safehouse.** *Decided.* The Agent is
   kept in `Wizard[...]`, with every teardown of Wizard that has not
   passed for it. The safehouse can run them again.
   - An Agent can be arrested by several Tags at once. Each Tag's
     safehouse keeps its own teardowns.
   - `Tag[...]` lists every arrested Agent. It keeps no teardowns of its
     own: "it applies for all safehouses except Tag[...] itself".
   - The safehouse holds the Agent, so dropping the last reference does
     not free it.
3. **The failure is reported.** *Recommended.* `del Wizard[ari]` raises
   the Composition Failure. It names the teardowns that failed and says
   the Agent is arrested, with the first teardown's own error as its
   cause. A Field Rip reports once, after the walk (STEP-SPEC-24, rule
   1.4). A deletion reports as the language reports a finalizer's error.
   In every case, the arrest has already happened when the failure is
   raised.
4. **An arrested Agent does nothing.** *Decided; the list is
   Recommended.* Anything the Agent answers itself is an **act**:
   - reading or writing any name on it: a Record, a host attribute, a
     Link;
   - calling an Action or a host method;
   - its own answers to the language: `str()`, `repr()`, `print()`,
     `format()` (apart from the kit's display specs), `bool()`, `len()`,
     iteration, the host's own `in`, and any operator its host defines.

   These are **not** acts, and never touch the safehouse:
   - holding or moving it: identity (`is`, `id()`), `==` and `hash()`, so
     that it can sit in lists, sets and dictionaries;
   - the kit's questions about its Tags: `ari in Wizard[:]`, `ari in
     Wizard[...]`, `Tags(ari)`, `Outline(ari)`, `Keyword(ari, ...)`, a
     Flag's word with `in`, and the display specs `f"{ari:tags}"`,
     `f"{ari:outline}"` and `f"{ari:contract}"`.
5. **An act retries the teardowns first.** *Decided.* Before the act,
   every safehouse that keeps the Agent runs its teardowns that have not
   passed, in order.
   - If they all pass, the Agent is free, and the act goes on as normal.
   - If one fails, the act is refused before it starts, with the
     **Arrested Access Failure**. Its cause is the teardown's own error.
     The Agent stays arrested.
   - *Recommended:* a teardown that passed is done. It never runs again,
     in a later retry or by hand.
6. **The teardowns themselves are exempt.** *Decided.* While a teardown
   of the Agent runs, it reads and writes the Agent freely, and what it
   calls does too. No retry starts inside a retry.
7. **The ways out.** *Decided.*
   - `del Wizard[ari]` runs Wizard's remaining teardowns for ari again,
     by hand. If one fails, it raises as rule 3 says. Today `del
     Wizard[ari]` on an Agent that is not a member is a Resolution
     Failure; for an Agent in Wizard's safehouse it is this retry.
   - `del Wizard[...]` ends every Agent Wizard's safehouse keeps, without
     their teardowns: triage, as STEP-SPEC-18 amendment F says. `del
     Tag[...]` ends every arrested Agent. One Triage Warning per Agent.
8. **Free.** *Decided.* An Agent is free when every teardown of every
   safehouse that kept it has passed: "When ALL rips succeed". It leaves
   every safehouse. It is then a Rogue Agent of each Tag it left (§0.7,
   §1.5): it keeps what the Tags gave it, and their published members
   raise the Rogue Access Failure.
9. **Tagging an arrested Agent.** *Recommended.* `Wizard(ari)`, or any
   other Tag on ari, is an act: the teardowns run first. If ari goes
   free, the tagging goes on. If not, it is refused with the Arrested
   Access Failure. The Director: "it is not allowed anything except
   rerunning rips or deletion".
10. **At interpreter exit.** *Recommended.* Once the interpreter is
    finalizing, nothing can be kept, as STEP-SPEC-18 amendment E already
    says. A teardown that fails in the `At_Exit` pass is reported, and
    the Agent is not kept.
11. **The failure.** *Recommended:* `TagArrestedAccessError`, the **Tag
    Arrested Access Failure**, a Resolution Failure like the Rogue Access
    Failure. The Failure model gains a row:

    | Failure | When | Effect |
    | --- | --- | --- |
    | **Tag Arrested Access Failure** | An arrested Agent tried to act, and a teardown failed again. | the act refused; the Agent stays arrested |

## What this replaces

| Where | Today | With this STEP |
| --- | --- | --- |
| STEP-SPEC-18 amendment D (`step-19-sound-in`) | A failed Rip is refused and rolled back; the Agent is a member again | The Agent leaves and is arrested (rules 1, 2) |
| STEP-SPEC-18 amendment E (`step-19-sound-in`) | A kept Agent stays a member of its Tags | A kept Agent is not a member (rule 2) |
| STEP-SPEC-18 amendment F (`step-19-sound-in`) | Triage, `del Wizard[...]` | Stays (rule 7) |
| `main` | A failed teardown on a Rip: the Agent is out, half torn down, and nothing holds it | Arrested (rules 1, 2) |
| STEP-SPEC-24 open question 1 | Open: arrest, the act decides, or today's kit | Answered: arrest, one rule (rule 1) |
| STEP-SPEC-29 open question 3 | `del Wizard[...][:]` refused until STEP-24 OQ1 settles | Kept Agents are not members; `del Wizard[...]` is triage |

## Rationale

**Security first.** An Agent whose teardown failed may still hold what
the Tag gave it: "it still has a gun and badge". Rolling it back makes
it a full member again. Leaving it free, as `main` does, lets it act. An
arrest does neither: the membership ends, and the Agent can do nothing
until its cleanup is done.

**The same idea as a broken promise, made stricter.** A defective
member is kept out of the loop until it is repaired (§2.5). An arrested
Agent is kept out of everything until its teardowns pass.

**A retry at the act is a prerequisite, not a side effect.** The Rip
was asked for already, and failed. When the program next asks the Agent
to act, the safehouse checks that the Rip can now go through. If it
can, the program gets what it expects from a Rip that passed. If not, it
gets an error, never the act.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Roll back the Rip (STEP-SPEC-18 amendment D) | The Agent keeps its badge. Replaced by the Director's ruling. |
| The act decides: a demanded Rip rolls back, an ending arrests (STEP-SPEC-24 option b) | Two rules. The Director: "a single rule for Rip and a Field Rip". |
| Out, half torn down (today's kit) | The Agent can still act. |
| Refuse every act, and retry only by hand | The Director chose the retry at the act: "Reiterating the rip is not magic, is a prerequisite." |

## Implementation plan

1. **The safehouse is on `step-19-sound-in`.** `Wizard[...]`, `Tag[...]`
   and triage are built there (STEP-SPEC-18, amendments E and F), not on
   `main`. This STEP changes them. Building it on `main` first would mean
   building the safehouse twice. Recommended: build it on top of
   `step-19-sound-in`, once that line is settled.
2. **The lock.** The runtime type of an arrested Agent answers every act
   of rule 4 by running the retry first. The kit already gives every
   Agent a runtime type with its own `__getattr__`; the lock needs
   `__getattribute__` and the language's other entry points, with the
   teardowns exempt (rule 6).
3. **Teardowns that passed** are remembered per Agent and per Tag, so a
   retry runs only the rest (rule 5).

## Open questions for the Director

1. **Does the failed Rip still raise?** (rule 3) Recommended: yes. The
   arrest has happened, but the program asked for a Rip that did not
   finish cleanly, and a silent arrest would surprise it later.
2. **What counts as an act?** (rule 4) Recommended: the two lists there.
3. **The failure's name.** (rule 11) Recommended:
   `TagArrestedAccessError`, beside `TagRogueAccessError`.
4. **Tagging an arrested Agent.** (rule 9) Recommended: an act.
5. **A teardown that passed never runs again.** (rule 5) Recommended:
   yes.

## Acceptance requirements

- `tests/test_topkit.py`: an `ArrestTests` class, covering:
  - a failed teardown on a Rip, a Field Rip and a deletion: the Agent is
    out of the Field and in the safehouse;
  - every act of rule 4 runs the retry, and nothing in the second list
    does;
  - a retry that passes frees the Agent and the act runs; one that fails
    raises the Arrested Access Failure before the act;
  - the teardown is exempt;
  - several Tags arresting one Agent: free only when all pass;
  - `del Wizard[ari]` retries; `del Wizard[...]` and `del Tag[...]`
    triage;
  - a teardown that passed does not run again.
- The Specification's §3.1 and §3.2 say rules 1 to 10; the Failure model
  gains the row of rule 11.
- The Guide shows the example of the Summary.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Ruled by the Director on 2026-10-09:* "A failed rip sends you to the
> safehouse, and you leave the tag. […] a single rule for Rip and a
> Field Rip."
