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

When a teardown fails during an ordinary Tag's explicit Rip or Field
Rip, the Agent still leaves the Tag. It is held in the Tag's safehouse,
**arrested**. An
arrested Agent does nothing. When it tries to act, the safehouse first
runs its teardowns again. If they all pass, the Agent is free, and the act
goes on. If one fails, the act is refused before it starts. The program
can also retry by hand, with `del Wizard[ari]`. Or it can end every Agent
that Wizard keeps, with `del Wizard[...]`. One decided rule covers an
ordinary Tag's explicit Rip and Field Rip. Agent deletion remains open
question 7; a Tag's end, Pins and Links remain open question 8.

```python
class Sentry(Tag):

    @Rip
    def Hand_In_Badge(agent):
        agent.locker.Store(agent.badge)   # raises while the locker is jammed


guard.locker = locker   # the program keeps its own name for the locker
Sentry(guard)
try:
    del Sentry[guard]   # Hand_In_Badge fails: the guard leaves Sentry, arrested
except TagCompositionError:
    pass                # the Rip reports the failure (rule 3)

try:
    guard.Patrol()      # an act: the safehouse runs Hand_In_Badge first
except TagArrestedAccessError:
    pass                # still jammed: Patrol never ran (rule 5)

locker.Unjam()          # not guard.locker: reading guard is an act
guard.Patrol()          # Hand_In_Badge passes: the guard is free, then Patrol runs
```

**Words used here.**
- **Teardown**: a `@Rip` protocol of a Tag (§3.1). A Tag may have any
  number of them.
- **Field Rip**: `del Wizard[:]`. Every member leaves the Tag, then each
  one's cleanup begins (STEP-SPEC-24); a failure freezes its remaining
  teardowns under rule 5.
- **Safehouse**: where a Tag keeps the Agents whose teardowns failed,
  `Wizard[...]` (STEP-SPEC-18, amendment E, on `step-19-sound-in`).
  `Tag[...]` lists every Agent that any Tag keeps.
- **Arrested**: kept in a safehouse. The Agent is not a member of that
  Tag any more, and it can do nothing until its teardowns pass.
- **Act**: something the arrested Agent does or answers itself (rule
  4).
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

On the same day he answered a summary of that ruling. To "Once a Rip
succeeds, the Agent goes free":

> "Not really. When ALL rips succeed (there is no limit on how may
> protocols it should have). also it applies for all safehouses except
> Tag[...] itself."

To the worry that a read would become an act:

> "There is no reading without rip. Only errors. If the code calls for
> acts, then that is a very good moment to ratify if the rip can pass.
> The Rip was taken already, just failed. Reiterating the rip is not
> magic, is a prerequisite. An agent in the safehouse is jailed and
> cannot answer the print. After the rip, the agent is liberated and
> then it can answer, which is just what the user should expect if now
> the rip protocol can happen. It is a safety check, but would not break
> the code for a failed state that it is fixed or fixable now.
> Obviously anything called from the rip protocol would not trigger
> that. exempt the teardown."

To the worry that things touch an Agent without meaning to:

> "If it's quarantined and arrested it should not be touched. It is
> infectious, it is arrested, and jailed. it does not get visits. That
> is what quarantines are for. Only the treatment (ripping) can get you
> out of confinement. Rip is already a violent act, and everything that
> breaks that premise means it should not have been a rip, but a record
> mutation. If you went to the troubles of ripping it means something
> huge happened, so it is the full security response. A rogue agent may
> be just retired, which is huge as a change, but an agent you lost
> control on is a fuck up. Any contact with it should end in arrest."

To the worry about a teardown that fails because something outside is
down: "yeah... that's an architectural problem, not a top paradigm one.
If teardown is possible, your protocol should be effective."

On what an act is:

> "I meant every act **by an arrested Agent**, not every act ever. Any
> Action or record access. Moving the agent around or checking what tags
> it belongs to are not necessarily triggers for that. Just if the agent
> wants to do something."

And on the ways out, he kept the first line of the summary and rewrote
the second: "`del Wizard[ari]` runs the Rip again; `del Wizard[...]`
forcefully deletes the Agent."

Two rules on `step-19-sound-in` give way:
- **STEP-SPEC-18, amendment D**: a failed Rip is refused and rolled back,
  so the Agent is a member again. Under this STEP the Agent leaves.
- **STEP-SPEC-18, amendment E**: a kept Agent "stays a member of its
  Tags". Under this STEP it is not a member.

Amendment F, triage, stays.

## Specification

1. **A failed teardown ends membership anyway.** *Decided.* When an
   ordinary Tag's teardown fails during a Rip (`del Wizard[ari]`) or a
   Field Rip (`del Wizard[:]`, STEP-SPEC-24), the Agent still leaves the
   Tag: "If it is
   in the safehouse, it is not in the tag". It is out of `Wizard[:]`,
   `Wizard` and `~Wizard`, and it loses the Tag's published Reports and
   Operations, as after any Rip (§0.7).
   - *Recommended:* the same at the Agent's deletion, where STEP-SPEC-18
     amendment E already keeps it. Every Tag's teardowns run there
     (§3.2). The Agent leaves every Tag it carries, and only the Tags
     whose teardowns failed keep it. Nothing is rolled back. Open
     question 7.
   - *Recommended:* the same at a Tag's end (STEP-SPEC-24, rule 3.1). A
     member whose teardown fails is kept, and only `Tag[...]` lists it,
     since the Tag is gone. The Director, 2026-10-08: "any safehouse can
     be accessed from Tag[...] so it's ok if the tag is deleted and no
     myTag[...] access exists." Open question 8.
   - *Recommended:* if a teardown applied the Tag again (STEP-SPEC-24,
     rule 1.5; §3.1 calls it outside good TOP use), the new membership
     stands, and that Tag does not arrest the Agent. The failure is
     still reported (rule 3). Open question 14.
2. **It is arrested in the Tag's safehouse.** *Decided.* The Agent is
   kept in `Wizard[...]`. The safehouse keeps Wizard's teardowns and can
   run them on the Agent: "The safehouse of a tag should keep the rip
   protocols of the tag and be able to run them on the agents."
   - An Agent can be arrested by several Tags at once. Each Tag's
     safehouse keeps its own teardowns.
   - `Tag[...]` lists every arrested Agent. It keeps no teardowns of its
     own: "it applies for all safehouses except Tag[...] itself".
   - The safehouse holds the Agent. Dropping the last reference does not
     end it.
   - *Recommended:* at a deletion, the kit keeps the Agent from inside
     its finalizer, as STEP-SPEC-18 amendment E does. Python runs a
     finalizer only once per object. So when an Agent arrested at its
     deletion goes free, or triage lets it go, its `__del__` Layers and
     its host's `__del__` never run. If it was collected in a cycle, it
     has already lost its weak references: one the program held stays
     dead. Open question 7.
3. **An explicit Rip reports the failure.** *Decided.* The Director,
   2026-10-09: "A failed del Wizard[ari] should raise an error. Yes."
   `del Wizard[ari]` raises the Composition Failure. It names the
   teardown that failed and says the Agent is arrested, with that
   teardown's own error as its cause. The arrest has already happened
   when the failure is raised.

   *Recommended, not decided:* a Field Rip continues with its next member
   and reports its ordinary failures once after the bulk walk
   (STEP-SPEC-24, rule 1.4; open question 16). Reporting at an Agent's
   deletion remains part of open question 7.
4. **An arrested Agent does nothing.** *Decided:* no Action and no record
   access ("Any Action or record access"), and no `print()` ("An agent
   in the safehouse is jailed and cannot answer the print"). Moving it,
   or asking what Tags it carries, need not be an act ("Moving the agent
   around or checking what tags it belongs to are not necessarily
   triggers for that"). *Decided:* the lists below. The Director, 2026-10-09: "Yes,
   that's the model. An agent acts, or the program acts on the agent are
   different concepts. hashs and equal checks are more organizational
   than actions, unless the agent has redefined them and needs to access
   information on records or needs to execute actions."

   Anything the Agent answers itself is an **act**:
   - reading or writing any name on it: a Record, a host attribute, a
     Link;
   - calling an Action or a host method;
   - reading a Tag view of it, `ari.Watch` or `Watch[ari]`, or calling an
     Action through one, even one taken before the arrest;
   - its promises: `bool(ari)`, `f"{ari:contract}"` and the `Contract`
     readings run its conditions, and those read its Records;
   - its own answers to the language: `str()`, `repr()`, `print()`,
     `format()` (apart from the display specs of the next list), `len()`,
     iteration, the host's own `in`, and any operator its host defines,
     its own `==` and `hash()` included.

   These are **not** acts, and never touch the safehouse:
   - holding or moving it: identity (`is`, `id()`), `type()` and
     `isinstance()`. `==` and `hash()` are free too when the host keeps
     Python's own, which go by identity, so the Agent can sit in lists,
     sets and dictionaries. A host that defines its own `__eq__` or
     `__hash__` answers them with its own code, and that code reads the
     Agent: on such a host, finding the Agent in a set or a dictionary
     is an act;
   - the kit's questions about its Tags: `ari in Wizard[:]`, `ari in
     Wizard[...]`, `Tags(ari)`, `Outline(ari)`, `Keyword(ari, ...)`, a
     Flag's word with `in`, and the display specs `f"{ari:tags}"` and
     `f"{ari:outline}"` on a host with no `__format__` of its own.

   Showing the Agent is an act. A `print()` of the safehouse, a log line
   with `%r`, a debugger, or a failing test's message runs the retry,
   with whatever the teardowns do, or raises.

   *Recommended:* the kit never checks an arrested Agent's promises
   for a Tag it still carries, because a check reads its Records. While
   it is arrested, it is in no sound population and in no broken one:
   `ari in Fighter` and `ari in ~Fighter` are `False`, and their walks
   and counts skip it, with no retry. Its Fields still list it: `ari in
   Fighter[:]` is `True`. Open question 6.

   *Recommended:* a Rip of a Tag the Agent still carries, `del
   Fighter[ari]`, is not an act. It goes through, and Fighter's
   teardowns run as rule 6 lets them: "Only the treatment (ripping) can
   get you out of confinement." Open question 13.
5. **An act retries the teardowns first.** *Decided.* Before the act,
   every safehouse that keeps the Agent runs its teardowns on it again.
   - If they all pass, the Agent is free, and the act goes on as
     normal: "it is then liberated and performs the action as normal".
   - If one fails, an error is raised before the act starts: "an error
     is raised before it tries to perform the action". The Agent stays
     arrested. *Decided:* the error is the Arrested Access Failure (rule
     11). *Recommended:* the teardown's own error is its cause.
   - *Decided:* a teardown that passed never runs again, in a later
     retry or by hand.
   - *Decided:* the teardowns keep their order. A Tag's run top to
     bottom, as written. A Shape's run before its Base's: overlay to
     underlay (§3.2; checked on TopKit 0.2.0a4). At the first failure,
     the teardowns after it do not run: they wait, frozen, so the order
     holds. A retry starts again at the one that failed, and goes on in
     the same order. The Director, 2026-10-09: ""A teardown that passed never runs
     again." ok, but the order of running is the order of tagging up to
     down in the code, right? two rip protocols in an underlay run up to
     down and overlay to underlay, right? So a failed ripping should
     freeze the underlaying rips so they keep the intended order."
   - *Recommended:* the safehouses take turns in the order they arrested
     the Agent. In a Field Rip, one member's failure freezes only that
     member's teardowns; the next member's still run (STEP-SPEC-24, rule
     1.4; open question 16).
   - *A limit of Python:* a host method taken before the arrest (`ping =
     guard.ping`), or called through its class (`Host.ping(guard)`),
     does not ask the Agent first. The lock stops it at its first read
     or write on the Agent. What it did before that stays done. A host
     method that never touches the Agent runs.
6. **The teardowns themselves are exempt.** *Decided:* "Obviously
   anything called from the rip protocol would not trigger that. exempt
   the teardown." While a teardown of the Agent runs, it reads and writes
   the Agent freely, and what it calls does too.
   - *Recommended:* the exemption belongs to the thread that runs the
     teardown. Work the teardown hands to another thread is not exempt.
     Another thread that acts on the Agent meanwhile waits for the retry
     to end, then gets its outcome. No retry of an Agent starts while
     another retry of the same Agent runs. Open question 12.
   - *Recommended:* while any teardown runs on that thread, even another
     Agent's in the same Field Rip, an arrested Agent it touches is not
     retried, as the Director's words say: "anything called from the rip
     protocol". Open question 12.
7. **The ways out.** *Decided:* "it is not allowed anything except
   rerunning rips or deletion".
   - `del Wizard[ari]` runs Wizard's teardowns for ari again, by hand:
     "`del Wizard[ari]` runs the Rip again". Which ones run is rule 5's
     recommendation. Today `del Wizard[ari]` on an Agent that is not a
     member is a Resolution Failure. For an Agent that Wizard itself
     keeps, it is this retry. *Recommended:* an Agent that only a Shape
     of Wizard keeps is retried through that Shape, though `Wizard[...]`
     lists it (open question 13).
   - `del Wizard[...]` "forcefully deletes the Agent": it ends every
     Agent that Wizard's safehouse keeps, without their teardowns. This
     is triage, as STEP-SPEC-18 amendment F says. `del Tag[...]` ends
     every arrested Agent. One Triage Warning per Agent.
8. **Free.** *Decided:* "When ALL rips succeed". An Agent is free when
   the teardowns of every safehouse that keeps it have passed. It leaves
   every safehouse. It is then a Rogue Agent of each Tag it left (§0.7,
   §1.5): it keeps what the Tags gave it, and their published members
   raise the Rogue Access Failure. *Recommended:* a safehouse whose
   teardowns have all passed lets the Agent go, as amendment E says; the
   Agent stays arrested while another safehouse keeps it (open question
   13).
9. **Tagging an arrested Agent.** *Decided.* `Wizard(ari)`, or any other
   Tag on ari, is an act: the teardowns run first. If ari goes free, the
   tagging goes on. If not, it is refused with the Arrested Access
   Failure. The Director, 2026-10-09: "Tagging would grant acts to the Agent. these
   could be used as "skip protocol" hacks. Yes, it is better to ban
   taggings too. An override of the features of the tag could still
   happen before, which is a better design rule."
10. **At interpreter exit.** *Recommended.* Once the interpreter is
    finalizing, nothing can be kept, as STEP-SPEC-18 amendment E already
    says. A teardown that fails in the `At_Exit` pass is reported; the
    Agent leaves the Tag, as in rule 1, but is not kept. An Agent still
    arrested at exit is let go when the interpreter clears the kit. No
    retry runs then, because no teardown runs while finalizing. Its
    `__del__` Layers run, exempt as a teardown is: the Director allows
    "rerunning rips or deletion". Open question 9.
11. **The failure.** *Decided:* `TagArrestedAccessError`, the **Tag
    Arrested Access Failure** ("TagArrestedAccessError, yes").
    *Recommended:* a Resolution Failure, like the Rogue Access Failure.
    The Failure model gains a row:

    | Failure | Meaning | Effect |
    | --- | --- | --- |
    | **Tag Arrested Access Failure** | An arrested Agent tried to act, and a teardown failed again. | the act refused; the Agent stays arrested |

12. **An arrested Tag.** *Recommended.* A Pin's Agent is a Tag, and a
    Pin's teardown can fail (`del Patch[Wizard]`), so a Tag can be
    arrested. Its acts are what the program asks of it: reading or
    writing its Records and Reports, calling its Operations and Actions,
    and tagging with it, `Wizard(ari)`. The kit's own reads of it (its
    name, its Field, its populations) are not acts. A Link's teardown
    follows this STEP (STEP-SPEC-22). Open question 8.

## What this replaces

| Where | Today | With this STEP |
| --- | --- | --- |
| STEP-SPEC-18 amendment D (`step-19-sound-in`) | A failed Rip is refused and rolled back; the Agent is a member again | The Agent leaves and is arrested (rules 1, 2) |
| STEP-SPEC-18 amendment E (`step-19-sound-in`) | A kept Agent stays a member of its Tags | A kept Agent is not a member (rules 1, 2) |
| STEP-SPEC-18 amendment F (`step-19-sound-in`) | Triage, `del Wizard[...]` | Stays (rule 7) |
| §0.7 (`step-19-sound-in`) | "A Rip whose own teardown fails is refused too, and rolled back" | The Rip goes through, and the Agent is arrested (rules 1, 2) |
| §3.2 table and the Failure model (`step-19-sound-in`) | "on a Rip, the Rip refused; at deletion, the Agent kept" | On an explicit Rip, the Agent leaves and is arrested; the same rule at deletion is recommended in open question 7 |
| `main`, a Rip | A failed teardown: the Agent is out, half torn down, and nothing holds it | Arrested (rules 1, 2) |
| `main`, a deletion | A failed teardown is silent, and the Agent is freed | Recommended: arrested and reported; open question 7 |
| A Scope's exit (amendment D; while `Scope` lasts, STEP-SPEC-31) | A failed Rip on exit is refused and rolled back; the Tag stays | The Agent leaves and is arrested |
| STEP-SPEC-24 open question 1, and rules 1.4 and 3.1 | Open: arrest, the act decides, or today's kit | Answered: arrest (rule 1); a Tag's end is open question 8 |
| STEP-SPEC-26 rule 2.1 | On `step-19-sound-in` the §0.7 bullet keeps amendment D's sentence | The sentence goes (rule 1) |
| STEP-SPEC-27 rules 2.2 and 2.3 | A failed member's fate is STEP-24's open question 1; old members "are Rogue Agents" | Arrested (rules 1, 2); a Rogue Agent once free (rule 8) |
| STEP-SPEC-29 open question 3, rule 8.3 | `del Wizard[...][:]` refused until STEP-24 OQ1 settles whether kept Agents are members | Settled: kept Agents are not members (rule 1). What `del Wizard[...][:]` does is open question 11; `del Wizard[...]` stays triage (rule 7) |
| STEP-SPEC-31, Backwards compatibility 3 | Amendment D's rollback "still holds for every Rip" | Replaced: a failed Rip arrests (rule 1) |
| STEP-SPEC-22, its point on a failed Link teardown | Follows STEP-24's open question 1 | Rule 12 and open question 8 |
| §3.1, and STEP-SPEC-24 rule 1.4 | Every teardown of a Rip runs, even after one fails; the failures are collected | At the first failure, the Agent's later teardowns wait, frozen (rule 5) |

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

**The costs, honestly.**
- Showing an arrested Agent runs its retry: a `print()`, a log line, a
  debugger, a failing test's message (rule 4).
- On a host with its own `==` or `hash()`, finding the Agent in a set or
  a dictionary is an act (rule 4).
- Python lets a host method taken before the arrest start before the
  lock sees it (rule 5).

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
   building the safehouse twice. Open question 10.
2. **The lock.** When an Agent is arrested, the kit swaps its runtime
   type for an arrested one. When it goes free, the kit swaps it back.
   Python looks up special methods on the type, past
   `__getattribute__`. So the arrested type defines these, and each one
   runs the retry first:
   - `__getattribute__`, `__setattr__` and `__delattr__`;
   - `__repr__`, `__str__`, `__bool__` and `__format__`, even when the
     host has none (`__format__` lets the kit's display specs through);
   - every other special method the host or a Tag defines, except
     `__del__`, and except `__eq__` and `__hash__` when they are
     Python's own. If it wraps `__eq__`, it wraps `__hash__` too: a
     class that defines `__eq__` alone loses its hash.

   Reading `__class__` stays free, because `isinstance()` reads it, and
   so does the kit in every message. The kit writes `__class__` past the
   lock. The teardowns' exemption (rule 6) has its own count, per
   thread. It cannot reuse the kit's composition guard, because promise
   checks raise that guard too. The lock is the type, so code that reads
   the Agent past its type (`object.__getattribute__(ari, name)`,
   `gc.get_referents(ari)`) is not seen.
3. **Teardowns that passed** are remembered per Agent and per Tag, with
   the one that failed, so a retry starts there and runs only the rest,
   in order (rule 5).
4. **What the kit hands out.** An Action and a Tag view hold the Agent
   and reach it past its type. Each one checks the arrest when it is
   used, so one taken before the arrest is locked too.

## Open questions for the Director

1. **Does the failed Rip still raise?** (rule 3) *Decided on 2026-10-09:*
   yes.
2. **What counts as an act?** (rule 4) *Decided on 2026-10-09:* the two
   lists there; on a host with its own `__eq__` or `__hash__` that reads
   the Agent, `==` and `hash()` are acts.
3. **The failure's name and kind.** (rules 5, 11) *Decided on
   2026-10-09:* `TagArrestedAccessError`. Still recommended: a Resolution
   Failure, with the teardown's own error as its cause.
4. **Tagging an arrested Agent.** (rule 9) *Decided on 2026-10-09:* an
   act, so it is banned until the Agent is free.
5. **Which teardowns does a retry run?** (rule 5) *Decided on
   2026-10-09:* a teardown that passed never runs again; the order holds;
   a failure freezes the ones after it, and a retry starts at the one
   that failed.
6. **An arrested Agent in another Tag's populations.** (rule 4)
   Recommended: in neither `Fighter` nor `~Fighter`, with no retry, and
   still in `Fighter[:]`.
7. **A deletion that fails.** (rules 1, 2) Recommended: the same rule.
   The Agent leaves every Tag it carries, only the Tags whose teardowns
   failed keep it, and its `__del__` never runs again.
8. **A Tag's end, Pins and Links.** (rules 1, 12) Recommended: a Tag's
   end arrests, under `Tag[...]`. A Tag that a Pin arrests: the
   program's uses of it are acts, the kit's reads are not. A Link's
   teardown follows the same rule.
9. **At exit.** (rule 10) Recommended: a failed teardown in the
   `At_Exit` pass is reported; the Agent leaves the Tag and is not kept.
   An Agent still arrested at exit: its `__del__` Layers run, with no
   retry.
10. **Where to build it.** (Implementation plan 1) Recommended: on top
    of `step-19-sound-in`, once that line is settled.
11. **`del Wizard[...][:]`** (STEP-SPEC-29, open question 3).
    Recommended: a retry of every Agent `Wizard[...]` lists, each as
    `del Wizard[ari]`. Failures are reported once, after every retry has
    run. The other choice: it stays refused.
12. **Threads, and another Agent's teardown.** (rule 6) Recommended:
    only the teardown's own thread is exempt; other threads wait for the
    retry. While any teardown runs on that thread, touching an arrested
    Agent starts no retry.
13. **A safehouse that is done, a Shape's prisoner, a Rip of another
    Tag.** (rules 4, 7, 8) Recommended: the done safehouse lets go; a
    Shape's prisoner is retried through the Shape; a Rip of a Tag the
    Agent still carries goes through.
14. **A teardown that tags again.** (rule 1) Recommended: the new
    membership stands, with no arrest. The other choice: the arrest
    wins, and the new tagging is undone.
15. **A teardown layered over its Base's.** A Shape's `@Rip @Underlay
    def Second` runs the Base's `Second` through `underlay()`. At the
    Agent's deletion, the Base's own `Second` then runs again (checked on
    TopKit 0.2.0a4: `Hexer.Second`, `Wizard.Second`, then `Wizard.First`,
    `Wizard.Second`, `Wizard.Third`). Under "a teardown that passed never
    runs again", should the Base's `Second` count as passed once the
    Shape's ran it? Recommended: yes.
16. **Continue the Field Rip after one member fails?** Recommended: yes.
    That member's later teardowns stay frozen, but cleanup continues with
    the next member in the initial snapshot. Ordinary failures are
    reported once after the walk. The other choice is to stop the cleanup
    walk at the first failed member while retaining every unattempted
    obligation for retry.
17. **Interruption during a Field Rip.** If a teardown raises an
    interruption such as `KeyboardInterrupt` or `SystemExit`, does the
    bulk walk stop immediately, or finish cleanup for the other snapshot
    members and then re-raise? In either case, the original interruption
    remains an interruption, pending cleanup is not discarded, and no
    success is fabricated. Still open: whether the interruption itself
    arrests the current member.

## Acceptance requirements

- `tests/test_topkit.py`: an `ArrestTests` class, covering:
  - a failed teardown on an explicit Rip: the Agent is out of the Field
    and in the safehouse; the same outcome for that failed member in a
    Field Rip, with later-member continuation following open question 16;
    Agent deletion follows open question 7;
  - every act of rule 4 runs the retry, and nothing in the second list
    does; a Tag view and an Action taken before the arrest are locked;
  - a retry that passes frees the Agent and the act runs; one that fails
    raises the Arrested Access Failure before the act;
  - the teardown is exempt;
  - several Tags arresting one Agent: free only when all pass;
  - `del Wizard[ari]` retries; `del Wizard[...]` and `del Tag[...]`
    triage;
  - a teardown that passed does not run again;
  - another Tag's populations skip the arrested Agent.
- The Specification says rules 1 to 12 in §0.7, §0.8, §3.1 and §3.2.
  §0.7: an Agent is a Rogue Agent only once it is free; on
  `step-19-sound-in`, the bullet "A Rip whose own teardown fails is
  refused too, and rolled back" goes. §0.8: the safehouse row reads
  "kept after a failed teardown". The Failure model's Composition
  Failure row says the Agent leaves and is arrested, and the model gains
  the row of rule 11. The Conformance obligations for Ring 3 say the
  same.
- The Guide shows the example of the Summary.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Ruled by the Director on 2026-10-09:* "A failed rip sends you to the
> safehouse, and you leave the tag. […] a single rule for Rip and a
> Field Rip."
