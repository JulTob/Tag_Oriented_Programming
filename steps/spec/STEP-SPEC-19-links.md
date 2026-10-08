# STEP-SPEC-19: Links

- **STEP:** SPEC-19
- **Desk:** spec
- **Title:** Links: a Tag that belongs to an Agent
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-07
- **Revised:** 2026-10-08, after the Director's first review

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A Tag may grant each of its Agents **a Tag of its own**: a **Link**.
`@Link` over a Tag declared inside another Tag gives every Agent of that
Tag its own Link, held under the declaration's name the way a Record is
held: `charlie.Knows`. Calling it links a **Contact**: `charlie.Knows(ruth)`
makes Ruth a member of the Field of Charlie's Link. Bob's Link is another
Tag with another Field, so Ruth in `charlie.Knows` says nothing about Ruth
in `bob.Knows`.

A Link points one way. Charlie reaches Ruth; nothing on Ruth leads back to
Charlie. Linking makes the Contact a member and writes nothing else on
her. What the Link knows about the two of them lives on the **Pair**, and
is read through the Owner: `charlie.Knows[ruth].since`.

```python
class Social(Tag):

    @Link
    class Knows(Tag):

        @Pre
        def Not_Oneself(agent, contact):          # agent: the Owner; contact: the one linked
            return contact is not agent

        @Record
        def since(agent, contact, *, since=None): # a fact about the Pair
            return since


Social(charlie)
Social(bob)

charlie.Knows(ruth, since=2010)                   # Charlie links Ruth

assert ruth in charlie.Knows                      # Charlie knows Ruth
assert ruth not in bob.Knows                      # Bob does not
assert charlie.Knows[ruth].since == 2010          # the Pair's own Record

for friend in charlie.Knows & bob.Knows:          # mutual acquaintances
    print(friend.name)

del charlie.Knows[ruth]                           # Rip: Charlie forgets Ruth
```

## Motivation

Every Tag today is a **one-place** statement: *Ruth is a Wizard*. Many
domains need **two-place** statements: *Charlie knows Ruth*, *the Guild
trusts Bob*, *this drone follows that one*, *this account may read that
file*. The second place is an Agent, and there are as many of those
statements as there are Owners.

Logic has a plain answer, and it is the whole idea of this STEP. A
two-place statement `Knows(charlie, ruth)` is the same thing as a
**family of one-place statements**, one per Owner: `Knows_Charlie(ruth)`,
`Knows_Bob(ruth)`, and so on. Fix the first place and what is left is an
ordinary Tag. So TOP needs no new kind of membership, only a way for each
Owner to have its own Tag. The gate, the Field, the algebra, Rip and its
protocols, and history then work on relations with no new law.

### What works today, and where it breaks

The family can be built by hand: a Record whose builder makes a fresh Tag
class for each Agent. It was tried on TopKit 0.2.0a4, and then probed
again by four reviewers on 2026-10-08:

```python
def Acquaintance_Tag_For(owner):
    class Known(Tag):
        @Pre
        def Not_Oneself(agent):
            return agent is not owner         # the Owner, kept in a closure
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
| 1 | **The Contact keeps the Owner alive.** Ruth's history holds Charlie's Tag, and the Tag holds Charlie through any condition that names him. Charlie was never collected while Ruth lived. | Every useful gate names the Owner, so the natural code leaks. |
| 2 | **Records from two Owners fight on the Contact.** Charlie's `since=2010` and Bob's `since=2024` are one slot on Ruth: `ruth.since == 2024`, with an Overwrite Warning each time another Owner links her. | A fact about a Pair has no home on either Agent alone. |
| 3 | **Promises from two Owners share one slot.** Two Links declaring `Still_Honest` overlay by name: Ruth's contract lists one `Still_Honest`, not two, and the Contract Warning calls the other Link a Base. | Charlie's promise about his Pair with Ruth is gone, replaced by Bob's. |
| 4 | **One broken Link makes the Contact defective everywhere.** A failed promise on Bob's Link made an unrelated Guild refuse Ruth's published Operation (§1.5). | A relation's state leaked into the Contact's whole contract. |
| 5 | **The Link's protocols land on the Contact.** Its `@Pre` is read on Ruth by name (`ruth.Not_Oneself`) and sits in her contract; its `@Rip` becomes a callable Action on Ruth, which Bob's Link overwrote with an Overwrite Warning, so `ruth.Forget()` ran Bob's teardown. | Whatever a Link declares ends up on the one it links. |

The cost of the workaround, for scale: about 54 µs per Owner (the
declaring Tag applied, and a class built for that Agent) and about 72 µs
per link. It was measured once on a development machine with 300 Owners
and 3,000 links.

## Specification

A new section, **§1.10 Links**, in Ring 1, and four rows in §0.2. It
depends on STEP-SPEC-21 (a Tag's end Rips its Field) for §8.3.

### 1. Vocabulary

| Term | Meaning |
| --- | --- |
| **Link** | A Tag that belongs to one Agent, its **Owner**, granted by a `@Link` declaration of a Tag the Owner carries. |
| **Owner** | The Agent a Link belongs to. Charlie is the Owner of `charlie.Knows`. |
| **Contact** | An Agent a Link holds: a member of the Link's Field. Ruth is Charlie's Contact. |
| **Relation** | The `@Link` declaration itself, `Social.Knows`: what every Owner's Link is made from. |
| **Pair** | One Owner and one Contact, linked. The Pair carries the Link's Records. |

### 2. Declaring

1. `@Link` marks a Tag class declared in the body of another Tag. The
   inner class is the **Relation**, reachable on the declaring Tag by its
   name, `Social.Knows`, like a Report.
2. A Link is an **Agent-scope** contribution, a third kind beside the
   Action and the Record (§1.1). Its slot is `(Agent, name)`, and its
   receiver is the Owner.
3. A Relation may declare:
   - `@Pre`, `@Imprint` and `@Rip`: the protocols of linking and
     unlinking;
   - `@Record`: the Pair's Records (§7);
   - `@Report` and `@Operation`: the Tag scope of each Link, received by
     the Link itself, `def capacity(link)`.
4. A Relation may not declare an Action, a `@Post`, a `@Requirement`, a
   `@Delete`, an `@Underlay`, or a `@Public` or `@Secret` member. It may
   not be a `@Flag` or a `@Pin`, or have a Base. A Shape may not
   redeclare its Base's Relation, and a `@Pin` may not declare a `@Link`.
   Each refusal is a Declaration Failure at class use, and its message
   names this rule.

### 3. The two seats

1. **The Owner first, the Contact second.** Every function a Relation
   declares, except its Reports and Operations, receives the Owner in its
   first seat and the Contact in its second. The Link is the Owner's
   contribution, so the Owner is its receiver (§1.1). The Contact comes
   second, as the Agent comes second in a published Operation (§1.5). The
   names are the author's; the Guide writes `agent` and `contact`.
2. **Both seats, always.** A Relation function with fewer than two
   positional parameters is a Declaration Failure at class use, and the
   message shows the spelling `def Has_Room(agent, contact)`. A Contact
   seat with a default value is refused the same way: a default says an
   input was meant.
3. **Inputs by name, after the seats.** Inputs bind by name to the
   parameters after the two seats (§0.5): `def Recent(agent, contact,
   since)`. An input named like either seat is a Composition Failure at
   step 1, nothing changed, and the message shows that spelling.
4. **Neither seat is ever `None`** (§8).
5. **The Owner's door.** A Relation's functions run inside the Owner's
   composition door (§1.5), and the Contact's door stays shut. A Link is
   the Owner's code: it reads the Owner's secrets, never the Contact's.
6. **Nothing lands on either party.** A Relation's `@Pre` gates the
   linking only. It is never read by name on the Contact, never listed in
   her contract, and never re-checked at her later boundaries. Its
   `@Imprint` and `@Rip` are protocols only, never Actions of the Owner or
   of the Contact.

### 4. Granting

1. When the declaring Tag applies to an Agent, the Agent's own Link is
   built at **step 2, Parts**, beside its Records (§0.6), so a failed call
   rolls it back. It is stored under the Relation's name: `charlie.Knows`.
2. Each Owner's Link is a **distinct Tag**: `charlie.Knows is not
   bob.Knows`, with its own Field.
3. **A held Link is read-only.** Assigning `charlie.Knows = ...` or
   `del charlie.Knows` is a Composition Failure. A Link ends Contact by
   Contact, or all at once (§8), never by dropping the name.
4. **One name, one Link.** A second Link, an Action or a Record arriving
   at a name that holds a Link is a Composition Failure at step 1,
   nothing changed (§1.1's cross-kind rule).
5. **Sticky, like every contribution.** Ripping `Social` from Charlie
   leaves `charlie.Knows` with him (§0.7), and `Scope(charlie, Social)`
   never ends his Links. Whether a Rogue or defective Owner may still
   link is the author's to say, in the gate: `return agent in Social and
   bool(agent)`.

### 5. Linking

A Link is a Tag. Every Ring 0 act works on it:

| Act | Spelling |
| --- | --- |
| link | `charlie.Knows(ruth, **inputs)` |
| is linked now? | `ruth in charlie.Knows` |
| was ever linked? | `isinstance(ruth, charlie.Knows)` |
| the sound / defective / whole Field | `for p in charlie.Knows`, `~charlie.Knows`, `charlie.Knows[:]` |
| algebra | `charlie.Knows & bob.Knows`, `\|`, `-` |
| the Pair | `charlie.Knows[ruth]` (§7) |
| unlink (Rip) | `del charlie.Knows[ruth]` |
| unlink everyone | `del charlie.Knows[:]` (STEP-SPEC-21) |

1. **Linking is a Tagging of the Contact** (§0.6). The gate runs. The
   Pair's Records are built at Parts. The Contact enters the Field at
   Commit. The Imprints run. The Contact's own promises are re-checked at
   this boundary, as at every tagging (§2.4); a broken one raises, and
   the link stays. The kit never checks the Owner's membership or
   soundness. A gate that cares says so.
2. **Reapplying is a no-op** (§0.5), so an Imprint that links back ends
   after one echo.
3. **A failure inside a Relation's Imprint is that Imprint's failure.**
   This includes a nested linking's refusal: it surfaces as
   `TagImprintError`, with the nested failure as its cause, and the link
   stays (§0.6). TopKit 0.2.0a4 rolls the outer call back instead. That
   defect is in every Tag, not only Links, and is fixed on its own
   before this STEP is built.
4. While an Owner's Links are ending (§8), linking through them is a
   Composition Failure.

### 6. One direction

1. **A Link points from its Owner to its Contacts.** TOP has no spelling
   that walks back, from a Contact to the Owners that hold her.
2. **Nothing public on a Contact leads to an Owner.** Her `Tags`, her
   `Outline`, her format specs and her contract never list the Links that
   hold her. She never finds a Link by name (§1.7): `ruth.Knows` is
   Ruth's own Link if she is Social, and otherwise a missing attribute.
   `isinstance(ruth, charlie.Knows)` still answers, because it is asked
   with the Link already in hand.
3. **A Link names no Owner.** Nothing public on a Link leads to its
   Owner. The kit keeps the Owner only where it must run the Link's
   teardowns (§8.4), weakly and out of public reach, so a Link never
   keeps its Owner alive (finding 1).
4. **Two ways is written, never assumed.** A Link that should answer
   back says so in its own Imprint (§9). Breaking the barrier is an
   explicit act.
5. **What the barrier is.** It is a boundary of TOP's spellings, not a
   sandbox. Python code in the same process can read any object's
   insides. The barrier guarantees that no public spelling reaches an
   Owner through a Contact. A search that starts from every Owner, with
   the declaring Tag in hand (`Social[:].Knows[:] == ruth`,
   STEP-SPEC-20), finds who knows Ruth. That is a different capability,
   and it is the one to guard.

### 7. The Pair

1. **`charlie.Knows[ruth]` is the Pair**: the Link's Records for that
   Contact. Its Records read and write as ordinary attributes:
   `charlie.Knows[ruth].since = 2011`. For an ordinary Tag, `Tag[agent]`
   is the Agent as seen through that Tag (§1.7). Through a Link, what is
   seen is the Pair.
2. Pair Records are built at step 2 of the linking. Their builders take
   the two seats, then inputs by name: `def since(agent, contact, *,
   since=None)`. A Pair Record has no stored seat, because a new Pair has
   nothing stored.
3. **A Pair lives as long as its link.** The Relation's own `@Rip` can
   still read it while it runs (§8.1). After that, reaching it is a
   Resolution Failure. Linking again builds it fresh (§0.7).
4. **A Pair Record never lands on the Contact.** `ruth.since` is Ruth's
   own attribute or nothing. A Pair is reached only through its Owner's
   Link: a Contact has no spelling for it.

### 8. Ending

1. **`del charlie.Knows[ruth]`** ends membership and removes Ruth from the
   Field. Then the Relation's `@Rip` runs with `(charlie, ruth)`. Then the
   Pair ends.
2. **`del charlie.Knows[:]`** unlinks every Contact, as a Field Rip
   (STEP-SPEC-21).
3. **The Owner's deletion ends its Links.** Inside the Owner's finalizer
   (§3.2), after its own teardowns, each of its Links is Field-Ripped.
   The dying Owner sits in the first seat, as the finalizer already holds
   it, so that seat is never `None`. The Link, held by no one, then ends,
   and its Field is already empty (STEP-SPEC-21). At interpreter exit
   this happens only under `At_Exit`, as every teardown does there.
4. **A Contact's deletion unlinks her.** She leaves every Link that holds
   her, as §3.2 Rips an Agent from its Tags, and the Relation's `@Rip`
   runs with the live Owner. If the Owner cannot be reached because it
   was collected in the same cycle, the Pair ends silently: she leaves,
   and no protocol runs.
5. **Each Pair's teardown runs at most once.** A self-link,
   `charlie.Knows(charlie)`, is reached from both sides.
6. **An Agent that is both Owner and Contact**, deleted: first its
   teardowns run, including its exits from other Owners' Links; then its
   own Links end.

### 9. The Relation itself

The Relation is a template, never a Tag in play. `Social.Knows(x)`,
`Social.Knows[x]`, `del Social.Knows[x]` and `Scope(x, Social.Knows)` are
Composition Failures. Each message points to a Link: "Knows is a
Relation: link through an Owner, charlie.Knows(ruth)".

### 10. Patterns this enables, with no further law

**Two ways, written down.** The Contact joins Social and links back, in
two visible lines. Reapplying is a no-op, so the echo stops:

```python
class Social(Tag):

    @Link
    class Friends(Tag):

        @Imprint
        def Both_Ways(agent, contact):
            Social(contact)                       # the Contact joins Social: explicit
            contact.Friends(agent)                # and links back: explicit
```

**A bounded relation.** A Report on the Link, read by the gate:

```python
class Social(Tag):

    @Link
    class Knows(Tag):

        @Report
        def capacity(link):
            return 150

        @Pre
        def Has_Room(agent, contact):
            return len(agent.Knows[:]) < agent.Knows.capacity
```

**Old friends**, with STEP-SPEC-20's filters:

```python
for old_friend in charlie.Knows[:].since < 2000:
    print(old_friend.name)
```

## Rationale

**A family of one-place Tags, not a new kind of membership.** Fixing the
Owner turns a relation into an ordinary Tag, so the Field, the algebra,
the gate, Rip and history come for free and mean what they already mean.

**Held like a Record, but a Tag.** The Director: "It wouldn't 'conflict'
with a record. It would BE the record. They could be another kind of
grants by a tag, themselves." The Link sits in the Record's seat: it is
built at Parts, stored on the Owner, and stays after Rip. But it is a
Tag: something the Owner's relation *is* (*ser*), not a value the Owner
currently holds (*estar*). So it is never reassigned.

**The Owner first.** This was the Director's proposal: "an agent
parameter to operate on the agent that owns the link and a contact
parameter to operate on the target." Four reviewers tested it against
the Specification and the kit, and each concern went to a skeptic. The
proposal held, for four reasons:
- **It is §1.1's receiver rule, applied faithfully.** The Link is the
  Owner's contribution. With the Contact in the first seat, the receiver
  rule lands the Link's protocols on the Contact, which is finding 5.
- **It matches §1.5.** The holder comes first and the Agent second, as in
  `dispatch(agency, sender, message)`.
- **One word, one meaning.** Inside `class Social`, `agent` is Charlie on
  every line, and one indentation down it still is.
- **The deletion path already holds the Owner.** The finalizer has the
  dying Owner in hand, so the first seat is never `None`. The first draft
  passed `owner=None`, and the review showed it did not need to.

**Both seats, always.** A one-seat body copied from an ordinary Tag, such
as `def Is_Person(agent)`, would check the Owner when the author meant
the Contact. Requiring both seats turns that slip into a message at class
use. Today an input named like the second seat would silently receive
the Contact, so it is refused the way §1.3 refuses an input named like
the stored seat.

**The Owner's door only.** If the Contact's door opened too, a Link would
be a way to read a stranger's secrets: link her, then look inside. That
would cross the same barrier the Director drew in the other direction.

**One direction.** The Director: "They are one directional, so you should
declare the link to be bidirectional in the linking ... Sometimes roads
walk in only one direction, and you may not want to be able to access
charlie from ruth. ... the safety comes from not being able to be tracked
from your contact if it's compromised, unless you declare it so. Breaking
a barrier should be explicit."

**The Pair.** The Director: "we may need records on a link too... like a
relationship's attribute ... `charlie.Knows[ruth].since`". The spelling
reuses `Tag[agent]`, "the Agent as seen through this Tag". Through a
Link, what is seen is the Pair. That puts the fact about two Agents in
the one place that belongs to both of them and to neither (finding 2).

**Ending with the Owner.** The Director: "eliminating the agent of the
link ... should functionally rip the agents ... as normal Tag deletion."
With STEP-SPEC-21, a Link's end is a Field Rip like any Tag's. The Owner
ends its Links first, while it can still fill the first seat.

## Backwards compatibility

Nothing changes for code that does not write `@Link`. One new public
name: `Link`. No parameter name is reserved.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| A Record holding a hand-made Tag (the workaround) | Works for membership; set aside for findings 1 to 5, which only the kit can close. Not taught in the Guide: it would teach the leak. |
| A Record holding a set of Agents (`charlie.known = WeakSet()`) | Cheap, and right when nothing else is needed. But it has no gate, no Rip protocols, no history and no algebra: "a value can be flipped back, membership is a state of the architecture" (Guide, Pattern 11). |
| One Tag with an input, `Knows(ruth, by=charlie)` | Reapplying an active Tag does nothing (§0.5), so Ruth could be known by one Owner only. |
| A Pin | Wrong receiver: a Pin puts meaning on a Tag, not on an Agent (§1.9). |
| The Contact first and the Owner by name, `def Not_Oneself(agent, owner)` (the first draft) | Set aside: with the Contact first, the receiver rule lands the protocols on the Contact (finding 5). A seat passed by name would also be a new kind of seat. |
| The Contact first and the Owner positional second (one reviewer's repair) | Set aside for the same landing. It would also make `agent` mean Ruth inside `class Social`, one indentation below where it means Charlie. |
| An optional Contact seat, passed only when declared | Rejected: a one-seat body would silently check the Owner. |
| Both composition doors open | Rejected: linking would become a way to read the Contact's secrets. |
| A query from the Contact back to her Owners, `Owners(ruth, Social.Knows)` or `ruth in Social.Knows` (the first draft) | Withdrawn by the Director: links point one way, and TOP speaks in the language's own structures, not in query functions. |
| The Owner in the Link's display, `Knows[Charlie]` (the first draft) | Withdrawn: it would lead from the Contact to the Owner. |
| A marker for two-way Links, `@Link(both_ways=True)` | Set aside: the Imprint says it in two visible lines, and a marker would hide what runs. |
| The Relation as a Base of every Link | Rejected: Rip never cascades (§0.7), so membership in the Relation would outlive the last link. |

## Open questions for the Director

1. **The word `contact`.** It is your word, and it reads well for people.
   Two reviewers raised two concerns:
   - It is one letter away from `Contract`, which already names a guide,
     a query and a format spec in TOP. For a reader with dyslexia, that
     is a costly pair.
   - It fits *knows* and *friends*, but reads less well in *this drone
     follows that one* or *this account may read that file*.

   The names in a signature stay the author's either way. The question
   is only which word the Specification and the Guide use. The candidate
   the reviewers found is `member`, the word §0.8 already uses for an
   Agent in a Field.
2. **Pair Actions and Pair promises.** Should a Pair have Actions,
   `charlie.Knows[ruth].Greet()`? Should it have promises, so that a Pair
   is sound or defective on its own, and `~charlie.Knows` sorts Contacts
   by their Pair's promises instead of by their whole contract?

## Acceptance requirements

- The nested-Imprint defect (§5.3) is fixed first, in every Tag.
- STEP-SPEC-21 is Cleared, for §8.3.
- `tests/test_topkit.py`: a `LinkTests` class that covers:
  - every numbered rule above, each refusal with nothing changed;
  - findings 1 to 5 as regression tests: the Owner collected while a
    Contact lives; two Owners linking one Contact with no warning and no
    shared slot; nothing of the Link readable on the Contact;
  - the barrier: no public spelling from a Contact leads to an Owner.
- `tests/spec_examples.py`: the §1.10 examples.
- `tests/oracle_topkit.py`: Links in the random walk, with Owners and
  Contacts deleted mid-walk.
- `benchmarks/scenarios.py`: a linking scenario. The Links of one
  Relation should share its functions and one runtime composition,
  rather than build a class and a scan per Owner.
- The Guide: a pattern, "Your contacts", written when this STEP is
  Deployed.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
