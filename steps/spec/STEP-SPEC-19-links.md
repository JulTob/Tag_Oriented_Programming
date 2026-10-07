# STEP-SPEC-19: Links

- **STEP:** SPEC-19
- **Desk:** spec
- **Title:** Links: a Tag that belongs to an Agent
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-07

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A Tag may grant each of its Agents **a Tag of its own**: a **Link**.
`@Link` over a Tag declared inside another Tag gives every Agent of that
Tag its own copy, held under the declaration's name the way a Record is
held, and applied the way an Action is called. `charlie.Knows(ruth)` puts
Ruth in Charlie's Field; Bob's is another Tag and another Field, so Ruth
in `charlie.Knows` says nothing about Ruth in `bob.Knows`. A Link leaves
only membership on its members: everything else it declares stays with
the owner or with the call.

```python
class Social(Tag):

    @Link
    class Knows(Tag):

        @Pre
        def Not_Oneself(agent, owner):        # the owner arrives by name
            return agent is not owner


Social(charlie)
Social(bob)

charlie.Knows(ruth)                           # apply Charlie's Link to Ruth

assert ruth in charlie.Knows                  # Charlie knows Ruth
assert ruth not in bob.Knows                  # Bob does not
assert ruth in Social.Knows                   # somebody knows Ruth
assert Owners(ruth, Social.Knows) == [charlie]

for friend in charlie.Knows & bob.Knows:      # mutual acquaintances
    print(friend.name)

del charlie.Knows[ruth]                       # Rip: Charlie forgets Ruth
```

## Motivation

Every Tag today is a **one-place** statement: *Ruth is a Wizard*. Many
domains need **two-place** statements: *Charlie knows Ruth*, *the Guild
trusts Bob*, *this drone follows that one*, *this account may read that
file*. The second place is an Agent, and there are as many of those
statements as there are owners.

Logic has a plain answer, and it is the whole idea of this STEP. A
two-place statement `Knows(charlie, ruth)` is the same thing as a
**family of one-place statements**, one per owner: `Knows_Charlie(ruth)`,
`Knows_Bob(ruth)`, and so on. Fix the first place and what is left is an
ordinary Tag. So TOP needs no new kind of membership, only a way for each
owner to have its own Tag. Everything TOP already has (the gate, the
Field, the algebra, Rip and its protocols, history) then works on
relations with no new law.

### What works today, and where it breaks

The family can be built today by hand: a Record whose builder makes a
fresh Tag class for each Agent. It was tried on TopKit 0.2.0a4:

```python
def Acquaintance_Tag_For(owner):
    class Known(Tag):
        @Pre
        def Not_Oneself(agent):
            return agent is not owner         # the owner, kept in a closure
    Known.__name__ = f"Known_By_{owner.name}"
    return Known


class Social(Tag):
    @Record
    def Knows(agent):
        return Acquaintance_Tag_For(agent)
```

Membership, the Field, `&`, `|`, `-`, the gate and Rip all behaved
correctly. Five things did not, and none of them can be fixed from
outside the kit:

| # | Found | Why it matters |
| --- | --- | --- |
| 1 | **The member keeps the owner alive.** Ruth's history holds Charlie's Tag (`isinstance(ruth, link)` must stay true), and the Tag holds Charlie through any condition that names him. Charlie was never collected while Ruth lived. | Breaks the spirit of §0.3, "a Field never keeps an Agent alive", in the reverse direction. Every useful gate names the owner, so the natural code leaks. |
| 2 | **Records from two owners fight on the member.** Charlie's `since=2010` and Bob's `since=2024` are one slot on Ruth: `ruth.since == 2024`, with an Overwrite Warning each time another Owner links her. | A fact about a pair has no home on either Agent alone. |
| 3 | **Promises from two owners share one slot.** Two Links declaring `Still_Honest` overlay by name: Ruth's contract lists one `Still_Honest`, not two, and the Contract Warning calls the other Link a Base. | Charlie's promise about his pair with Ruth is gone, replaced by Bob's. |
| 4 | **One broken Link makes the member defective everywhere.** A failed promise on Bob's Link made an unrelated Guild refuse Ruth's published Operation (§1.5). | A relation's state leaked into the Agent's whole contract. |
| 5 | **No inverse, no name.** "Who knows Ruth?" needs a scan of every Agent; the Link has no owner the kit can read; `f"{ruth:tags}"` shows whatever name the author forged. | A relation that cannot be read from both ends is half a relation. |

Cost of the workaround, for scale: about 54 µs per owner (the declaring
Tag applied, and a class built for that Agent) and about 72 µs per link,
measured once on a development machine with 300 owners and 3,000 links.

## Specification

A new section, **§1.10 Links**, in Ring 1, and three rows in §0.2.

### 1. Vocabulary

| Term | Meaning |
| --- | --- |
| **Link** | A Tag that belongs to one Agent, its **Owner**, granted by a `@Link` declaration of a Tag the Owner carries. |
| **Owner** | The Agent a Link belongs to. Charlie is the Owner of `charlie.Knows`. |
| **Relation** | The `@Link` declaration itself, `Social.Knows`: the shape every Owner's Link is made from, and the population of all of them. |

### 2. Declaring

1. `@Link` marks a Tag class declared in the body of another Tag. The
   inner class is the **Relation**; it is reachable on the declaring Tag
   by its name, `Social.Knows`, like a Report.
2. A Link is an **Agent-scope** contribution, a third kind beside the
   Action and the Record (§1.1). Its slot is `(Agent, name)`.
3. **A Link leaves only membership on its members.** A Relation may
   declare `@Pre`, `@Imprint`, `@Rip`, `@Report` and `@Operation`. It may
   not declare an Action, a Record, a `@Post`, a `@Requirement`, a
   `@Delete`, a `@Public` or `@Secret` member, nor be a `@Flag`, a `@Pin`,
   or have a Base. Each of those would land on the member, where every
   Owner who links it would fight for one slot (findings 2, 3 and 4). The
   refusal is a Declaration Failure at class use, and its message names
   this rule.

### 3. Granting

1. When the declaring Tag applies to an Agent, the Agent's own Link is
   built at **step 2, Parts**, beside its Records (§0.6), so a failed call
   rolls it back. It is stored under the Relation's name:
   `charlie.Knows`.
2. Each Owner's Link is a **distinct Tag**: `charlie.Knows is not
   bob.Knows`, with its own Field.
3. **A held Link is read-only.** Assigning `charlie.Knows = ...` or
   `del charlie.Knows` is a Composition Failure. A Link is ended member
   by member (§5), never dropped: dropping it would orphan a Field.
4. **One name, one Link.** A second Link, an Action or a Record arriving
   at a name that holds a Link is a Composition Failure at step 1,
   nothing changed. This is §1.1's cross-kind rule, with no Shape
   exception for Links in this STEP.
5. **Sticky, like every contribution.** Ripping `Social` from Charlie
   leaves `charlie.Knows` with him (§0.7). Whether a Rogue Owner may still
   link is the author's to say, in the gate: `return owner in Social`.

### 4. Linking

A Link is a Tag. Every Ring 0 act works on it unchanged:

| Act | Spelling |
| --- | --- |
| link | `charlie.Knows(ruth, **inputs)` |
| is linked now? | `ruth in charlie.Knows` |
| was ever linked? | `isinstance(ruth, charlie.Knows)` |
| the sound / defective / whole Field | `for p in charlie.Knows`, `~charlie.Knows`, `charlie.Knows[:]` |
| algebra | `charlie.Knows & bob.Knows`, `\|`, `-` |
| the exact view | `charlie.Knows[ruth]` |
| unlink (Rip) | `del charlie.Knows[ruth]` |

1. **The Owner seat.** Every protocol a Relation declares may name a
   parameter `owner`; it receives the Link's Owner. It binds by name, as
   an input does (§0.5), but it is not an input: the caller cannot supply
   it (a Composition Failure, nothing changed), and a `@Rip` protocol
   receives it though Rip takes no inputs.
2. **A Link never keeps its Owner alive.** It holds the Owner weakly, so
   history (`isinstance(ruth, charlie.Knows)`) never pins Charlie in
   memory (finding 1). `Owner(link)` reads the Owner, or `None` once it
   is gone.
3. **Reapplying is a no-op**, as for every Tag (§0.5): linking twice does
   not rerun Imprints.
4. A Link applies to whatever an ordinary Tag applies to. Whether an
   Owner may link itself is a domain choice, said in the gate.
5. **A Link is never found by name on its members.** `ruth.Knows` is
   Ruth's own Link if she is Social, and otherwise a missing attribute;
   it is never a view of somebody else's Link (§1.7 finds views by name).
   The exact view is `charlie.Knows[ruth]`.

### 5. Ending

1. `del charlie.Knows[ruth]` is an ordinary Rip: membership ends, the
   Relation's `@Rip` protocols run with `owner`, history stays.
2. **A Link ends with its Owner.** When the Owner ceases to exist, each
   remaining member leaves the Link as if Ripped, and the Relation's
   `@Rip` protocols run with `owner=None`. This happens as part of the
   Owner's deletion (§3.2), so it is as guaranteed as that is: best
   effort under `del`, certain under `Scope`. History stays.

### 6. Reading a Relation

1. `ruth in Social.Knows` is True while Ruth is a member of at least one
   live Link of that Relation: *somebody knows Ruth*. `for p in
   Social.Knows` walks those members, each once. The Relation itself is
   never applied: `Social.Knows(ruth)` is a Composition Failure ("Knows
   is a Relation: link through an Owner, charlie.Knows(ruth)").
2. `Owners(ruth, Social.Knows)` lists the live Owners whose Link holds
   Ruth, in linking order: *who knows Ruth*.
3. A Link displays as its name and its Owner as the host prints it,
   `Knows[Charlie]`, in `f"{ruth:tags}"`, `Outline` and failure messages.

### 7. Patterns this enables, with no further law

**A symmetric relation.** An Imprint links back; reapply being a no-op
stops the echo:

```python
class Social(Tag):

    @Link
    class Friends(Tag):

        @Imprint
        def Both_Ways(agent, owner):
            if agent in Social and owner not in agent.Friends:
                agent.Friends(owner)
```

**A bounded relation.** A Report on the Relation, read by the gate:

```python
class Social(Tag):

    @Link
    class Knows(Tag):

        @Report
        def capacity(link):
            return 150

        @Pre
        def Has_Room(agent, owner):
            return len(owner.Knows[:]) < owner.Knows.capacity
```

**Facts about the pair**, until a STEP gives them a home (Open question
1): a Record of the declaring Tag, held by the Owner and keyed by the
member, written in the Link's Imprint.

## Rationale

**A family of one-place Tags, not a new kind of membership.** Fixing the
Owner turns a relation into an ordinary Tag, so the Field, the algebra,
the gate, Rip and history come for free and mean what they already mean.
The only new things are where the Tag is held (on the Owner), how it is
made (once per Owner), and what it may leave behind (membership only).

**Held like a Record, but not a Record.** The Director: "It wouldn't
'conflict' with a record. It would BE the record. They could be another
kind of grants by a tag, themselves." The Link sits in the Record's seat:
built at Parts, stored on the Owner, sticky after Rip. But it is a Tag,
something the Owner's relation *is* (*ser*), not a value it currently
holds (*estar*). So it is not reassigned, and it is a third Agent kind
rather than a Record with a class in it.

**Membership only, on purpose.** The workaround showed that anything
else a Link leaves on its member is shared by every Owner that links the
same member: Records overwrite, promises overlay by name, and one
relation's broken promise closes the member's published doors
everywhere. Refusing those declarations is the smallest rule that makes
a Link mean *this pair* and nothing more. Lifting it, with pair-scoped
Records and promises, is a separate topic.

**The Owner by name.** Protocols already receive what the call brings
by name. The Owner reads the same way, `def Not_Oneself(agent, owner)`,
and needs no positional seat to learn.

**Weak Owners, ending with the Owner.** A Field never keeps an Agent
alive (§0.3); a Link must not either, from the other end. And a relation
whose Owner is gone is not a relation any more, so its members leave,
with the Owner's deletion, through the Rip protocols the author already
wrote.

## Backwards compatibility

Nothing changes for code that does not write `@Link`. New public names:
`Link`, `Owner`, `Owners`. `owner` becomes a reserved parameter name
inside a Relation only.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| A Record holding a hand-made Tag (the workaround) | Works for membership; set aside for findings 1 to 5, which only the kit can close. Not taught in the Guide: it would teach the leak. |
| A Record holding a set of Agents (`charlie.known = WeakSet()`) | Cheap, and right when nothing else is needed. But no gate, no Rip protocols, no history, no algebra: "a value can be flipped back, membership is a state of the architecture" (Guide, Pattern 11). |
| One Tag with an input, `Knows(ruth, by=charlie)` | Reapplying an active Tag does nothing (§0.5), so Ruth could be known by one Owner only; the input's Record would collide. |
| A Pin | Wrong receiver: a Pin puts meaning on a Tag, not on an Agent (§1.9). |
| The Relation as a Base of every Link | Rejected: Rip never cascades (§0.7), so `ruth in Social.Knows` would stay True after her last Link let her go. The Relation's population is the union of live Links instead. |
| A Link as an Action only (call, never read) | Rejected: a relation is read as often as it is made (`ruth in charlie.Knows`). Held like a Record, called like an Action: both. |
| Allow Records, Actions and promises on Links now | Deferred: they need pair storage and pair-scoped soundness. See Open question 1. |

## Open questions for the Director

1. **Pair state.** Should a follow-up STEP give a Link Records and
   promises about the pair, read through the exact view
   (`charlie.Knows[ruth].since`), with soundness scoped to the Link?
2. **The display.** `Knows[Charlie]` uses the host's own `str` of the
   Owner. A host without one prints `Knows[<Person object at …>]`. Accept,
   or display `Knows` alone and leave the Owner to `Owner(link)`?
3. **Scope of this STEP.** `Owners` and `ruth in Social.Knows` (§6) make
   the relation readable from both ends. Keep them here, or split them
   into their own STEP?
4. **The Owner seat's spelling.** By name, `owner`, as proposed; or a
   positional seat like `underlay` and `stored`?

## Acceptance requirements

- `tests/test_topkit.py`: a `LinkTests` class covering every numbered
  rule above, each refusal with nothing changed, and findings 1 to 5 as
  regression tests (the Owner collected while a member lives; two Owners
  linking one member with no warning and no shared slot).
- `tests/spec_examples.py`: the §1.10 examples.
- `tests/oracle_topkit.py`: Links in the random walk, with Owners
  deleted mid-walk.
- `benchmarks/scenarios.py`: a linking scenario. The kit should share one
  runtime composition per Relation rather than build one per Link.
- The Guide: a pattern, "Tags that belong to someone", written when this
  STEP is Deployed.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
