# STEP-SPEC-22: Links

- **STEP:** SPEC-22
- **Desk:** spec
- **Title:** Links
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-07
- **Revised:** 2026-10-08, after three reviews by the Director. First
  drafted as STEP-SPEC-19. It was renumbered because 19 to 21 are
  claimed by other open work.

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A Tag may grant each of its Agents **a Tag of its own**: a **Link**.
`@Link` over a Tag declared inside another Tag gives every Agent of that
Tag its own Link. The Agent holds it under the declaration's name, the
way it holds a Record: `charlie.Knows`.

The Agent acts through its Link. `charlie.Knows(ruth)` makes Ruth a
**Contact** of Charlie's: a member of the Field of Charlie's Link. Bob's
Link is another Tag with another Field, so Ruth in `charlie.Knows` says
nothing about Ruth in `bob.Knows`.

A Link is a Tag in full. It has Records, Actions and promises, Bases and
Shapes, secrets and published members. What an ordinary Tag gives its
Agent, a Link gives the **Pair**: Charlie and Ruth, linked. So nothing
lands on Ruth but membership, and the Pair is read through the Agent:
`charlie.Knows[ruth].since`.

A Link points one way. Charlie reaches Ruth; nothing on Ruth leads back
to Charlie.

```python
class Social(Tag):

    @Link
    class Knows(Tag):

        @Pre
        def Not_Oneself(agent, contact):          # the Agent acts; the Contact is acted on
            return contact is not agent

        @Record
        def since(agent, contact, *, since=None): # a fact about the Pair
            return since

        def Greet(agent, contact):                # an Action of the Pair
            return f"{agent.name} waves at {contact.name}"


Social(charlie)
Social(bob)

charlie.Knows(ruth, since=2010)                   # Charlie links Ruth

assert ruth in charlie.Knows                      # Charlie knows Ruth
assert ruth not in bob.Knows                      # Bob does not
assert charlie.Knows[ruth].since == 2010          # the Pair's Record
assert charlie.Knows[ruth].Greet() == "Charlie waves at Ruth"

for contact in charlie.Knows & bob.Knows:         # Contacts of both
    print(contact.name)

del charlie.Knows[ruth]                           # Rip: Charlie forgets Ruth
```

## Motivation

Every Tag today is a **one-place** statement: *Ruth is a Wizard*. Many
domains need **two-place** statements:
- *Charlie knows Ruth*;
- *Charlie owns this house*;
- *this drone follows that one*;
- *this account may read that file*.

The second place is an Agent too, and there are as many such statements
as there are Agents in the first place.

Logic has a plain answer, and it is the whole idea of this STEP. A
two-place statement `Knows(charlie, ruth)` is the same thing as a
**family of one-place statements**, one for each Agent in the first
place: `Knows_Charlie(ruth)`, `Knows_Bob(ruth)`, and so on. Fix the first
place and what is left is an ordinary Tag. So TOP needs no new kind of
membership, only a way for each Agent to have its own Tag. The gate, the
Field, the algebra, Rip and its protocols, Bases and Shapes, and history
then work on two-place statements with no new law.

### What works today, and where it breaks

The family can be built by hand: a Record whose builder makes a fresh Tag
class for each Agent. It was tried on TopKit 0.2.0a4, then probed again
by reviewers on 2026-10-08:

```python
def Acquaintance_Tag_For(holder):
    class Known(Tag):
        @Pre
        def Not_Oneself(agent):
            return agent is not holder        # the holding Agent, kept in a closure
    Known.__name__ = f"Known_By_{holder.name}"
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
| 1 | **The Contact keeps the Agent alive.** Ruth's history holds Charlie's Tag, and the Tag holds Charlie through any condition that names him. Charlie was never collected while Ruth lived. | Every useful gate names the Agent, so the natural code leaks. |
| 2 | **Records from two Agents fight on the Contact.** Charlie's `since=2010` and Bob's `since=2024` are one slot on Ruth: `ruth.since == 2024`, with an Overwrite Warning each time another Agent links her. | A fact about a Pair has no home on either Agent alone. |
| 3 | **Promises from two Agents share one slot.** Two Links declaring `Still_Honest` overlay by name: Ruth's contract lists one `Still_Honest`, not two, and the Contract Warning calls the other Link a Base. | Charlie's promise about his Pair with Ruth is gone, replaced by Bob's. |
| 4 | **One broken Link makes the Contact defective everywhere.** A failed promise on Bob's Link made an unrelated Guild refuse Ruth's published Operation (§1.5). | A Link's state leaked into the Contact's whole contract. |
| 5 | **The Link's protocols land on the Contact.** Its `@Pre` is read on Ruth by name (`ruth.Not_Oneself`) and sits in her contract. Its `@Rip` becomes a callable Action on Ruth, which Bob's Link overwrote with an Overwrite Warning, so `ruth.Forget()` ran Bob's teardown. | Whatever a Link declares ends up on the one it links. |

All five have one cause: the hand-made Tag gives what it declares to the
one it is applied to, the Contact. This STEP gives it to the Pair.

The cost of the workaround, for scale: about 54 µs per Agent (the
declaring Tag applied, and a class built for that Agent) and about 72 µs
per linking. It was measured once on a development machine, with 300
Agents and 3,000 linkings.

## Specification

The changes to the Specification:
- a new section, **§1.10 Links**, in Ring 1;
- four rows in §0.2, and one row in §0.8;
- amendments to §1.1 (a third kind of Agent-scope contribution, and Pair
  scope), §1.7 (the Pair in place of the Agent-bound view on a Link) and
  §3.2 (`At_Exit` of an Agent also ends its Links).

It depends on STEP-SPEC-24 (Field Rip, and the end of a Tag) for rules
8.2 and 8.3. STEP-SPEC-23 (Field Filters) reads the Pair through its
Link (STEP-SPEC-23, rule 1.5).

In this STEP, § cites the Specification only. This STEP's own parts are
cited as "section N" or "rule N.M".

### 1. Vocabulary

| Term | Meaning |
| --- | --- |
| **Link** | A Tag that belongs to one Agent, granted by a `@Link` declaration of a Tag that Agent carries. The Agent holds the Link and acts through it. |
| **Contact** | An Agent that a Link holds: a member of the Link's Field. Ruth is Charlie's Contact. |
| **Relation** | The `@Link` declaration itself, `Social.Knows`: what every Agent's Link is made from. |
| **Pair** | One Agent and one Contact, linked. The Pair receives the Link's Actions, Records and conditions, as an Agent receives an ordinary Tag's. |

**Agents have the agency.** When a Link is discussed, "the Agent" is
always the one who holds the Link and acts through it, as in an Action or
a Record. By §0.2 a Contact is an Agent too: of the Link, and of her own
Tags. Inside a Link she is always called the Contact, as an Action's
target is called its target. This STEP never writes "the Link's Agent",
which §0.2 could read as the Contact. It writes "the Agent who holds the
Link". "Owner" is an informal word for that Agent, never a term: in a Link
such as `charlie.Owns(house)`, the domain has its own owners.

### 2. Declaring

1. `@Link` marks a Tag class declared in the body of another Tag, the
   **declaring Tag**. The inner class is the **Relation**. It is named in
   the declaring Tag's body, `Knows`, and in a class statement's Bases as
   `Social.Knows` (rule 2.6, section 9).
2. A Link is an **Agent-scope** contribution of the declaring Tag, a third
   kind beside the Action and the Record. Its slot is `(Agent, name)`
   (§1.1, amended in rule 4.4), and its receiver is the Agent who holds
   it.
3. **A Relation declares what any Tag declares**: Actions, Records,
   conditions (`@Pre`, `@Post`, `@Requirement`), `@Imprint`, `@Rip`,
   `@Delete`, `@Underlay`, `@Secret`, `@Public`, `@Flag`, `@Report` and
   `@Operation`. Only the receiver changes:
   - **Pair scope.** What an ordinary Tag gives its Agent, a Link gives
     the Pair: Actions, Records and conditions, and the teardowns, which
     are Actions too (§3.1). `charlie.Knows[ruth].Greet()`,
     `charlie.Knows[ruth].since`, `charlie.Knows[ruth].Still_Honest`.
     This amends §1.1: on a Link, Agent scope is Pair scope.
   - **Tag scope.** Reports and Operations belong to the Link itself, one
     Link per Agent: `def capacity(link)`.
   - **The modifiers keep their meaning, with the Pair in the Agent's
     place.** `@Secret` hides a Pair member from everything but the
     Link's own functions. `@Public` publishes a Link's Report or
     Operation onto its Pairs. A Link marked `@Flag` answers its words on
     the Pair, `"Trusted" in charlie.Knows[ruth]`, never on the Contact.
4. **A Relation's Bases are Relations, resolved per Agent.** A Relation
   may name as Bases other Relations of the same declaring Tag, or of one
   of that Tag's Bases. For each Agent, the Bases are that Agent's own
   Links. With `class Trusts(Knows)`, `charlie.Trusts` is a Shape of
   `charlie.Knows`: never of Bob's Link, and never of the Relation.
   Because the declaring Tag's Form grants the Base Relations, the Agent
   always holds them.
5. **No ordinary Tag as a Base of a Relation.** Such a Base would be
   applied to the Contact at every linking, which breaks the barrier
   (section 6) without a word. A Link that means to write a Tag on the
   Contact says so in an Imprint, `Vetted(contact)`, where it is seen. The
   refusal is a Declaration Failure at class use.
6. **A Shape of the declaring Tag may extend its Base's Relation by
   name.** `class Spy(Social)` may declare `@Link class Knows(Social.Knows)`.
   The new Relation must name the Relation it extends among its Bases. A
   Relation of the same name that does not would replace a Link that may
   already hold Contacts, so it is a Declaration Failure at class use.
   Rule 4.6 says what extending a Link does.
7. **Still refused**, each a Declaration Failure at class use, and each
   its own topic:
   - a Relation that is a `@Pin`, and a `@Link` inside a `@Pin`. Links
     between Tags need their own receiver rule (§1.9);
   - a Link or a Relation as a Base of an ordinary Tag.

### 3. The seats

1. **Two seats where an ordinary Tag has one.** Every function a Relation
   declares for the Pair receives the Agent who holds the Link in its
   first seat, and the Contact in its second. Reports and Operations
   receive the Link itself.
   - The Agent comes first because the Link is the Agent's contribution,
     so the Agent is its receiver (§1.1).
   - The Contact comes second, as the Agent comes second in a published
     Operation (§1.5).
   - The names are the author's to choose. The Guide writes `agent` and
     `contact`.
2. **After the two seats, each kind follows its own rule**, exactly as it
   does after the one Agent seat of an ordinary Tag:
   - an Action: its Underlay when marked (§1.2), then the call's
     arguments: `def Greet(agent, contact, greeting)`;
   - a Record: the stored seat (§1.3), then inputs by name, with `*`
     holding the stored seat empty: `def since(agent, contact, stored)`,
     `def since(agent, contact, *, since=None)`;
   - a condition: its Underlay when marked (§2.4); then, for a
     Precondition, inputs by name (§2.2);
   - an Imprint: inputs by name (§2.3);
   - a teardown: nothing more (§3.1).
3. **Both seats, always.** A Relation function with fewer than two
   positional parameters is a Declaration Failure at class use, and the
   message shows the spelling `def Has_Room(agent, contact)`. A Contact
   seat with a default value is refused the same way: a default says an
   input was meant.
4. **An input never fills a seat.** A linking that supplies an input
   named like a positional seat of a function it runs is refused at
   linking with a Declaration Failure, nothing changed, and the message
   shows the spelling with `*`. This is how §1.3 refuses an input named
   like the stored seat.
5. **Neither seat is ever `None`** (section 8).
6. **The doors.** A Link's functions run inside the composition door
   (§1.5) of the Agent who holds the Link and of the Pair, so the Agent's
   secrets and the Pair's secrets resolve. The Contact's door stays shut,
   on every path, the teardowns at either one's deletion included. A Link
   is the Agent's code about a Pair. It never reads the Contact's
   secrets. This reverses what a tagging opens today, which is the door
   of the Agent being tagged.
7. **Nothing lands on the Contact.** What a Relation declares for the
   Pair lands on the Pair. Nothing of it is read by name on the Contact,
   listed in her contract, or re-checked at her later boundaries.

### 4. Granting

1. When the declaring Tag applies to an Agent, that Agent's own Link is
   built at **step 2, Parts**, beside its Records (§0.6). So a call that
   fails at its gate or at Parts rolls the Link back with it. It is
   stored under the Relation's name: `charlie.Knows`.
2. Each Agent's Link is a **distinct Tag**: `charlie.Knows is not
   bob.Knows`, with its own Field.
3. **A held Link is read-only.** Assigning `charlie.Knows = ...` or
   `del charlie.Knows` is a Composition Failure. A Link ends Contact by
   Contact, or all at once (section 8), never by dropping the name.
4. **One name, one Link.** A Link's slot is closed to every other
   Agent-scope contribution, in either order and within one Form too,
   except for the extension of rule 2.6. This amends §1.1: a Shape's
   change of kind never reaches a Link.
   - A second Link that does not extend the first, an Action, a Record, a
     condition or a `@Delete` arriving at a name that holds a Link is a
     Composition Failure at step 1, nothing changed.
   - So is a Link arriving at a name that already holds an Action, a
     Record, a condition or a member the host defines, as §2.5 refuses a
     condition there.
   - Within one call the check covers the whole Form, so it also catches
     a name that will hold a Link once Parts has run.
   - Equal names in Tag scope do not collide (§1.1).
5. **Sticky, like every contribution.** Ripping `Social` from Charlie
   leaves `charlie.Knows` with him (§0.7), and `Scope(charlie, Social)`
   never ends his Links. Whether a Rogue or defective Agent may still
   link is the author's to say, in the gate: `return agent in Social and
   bool(agent)`.
6. **Extending a held Link.** When an Agent gains a Tag whose Relation
   extends a Relation of a Link it already holds (rule 2.6), the Link
   gains that Relation as a new Layer, in Form order. It keeps its
   identity, its Field and its history.

   The new Layer applies to every Pair the Link already holds, as a
   tagging of each one, inside the same call:
   - at step 1, the new Layer's gate runs for every Pair, and one refusal
     refuses the whole call, nothing changed;
   - at Parts, its Pair Records are built for every Pair, and a failure
     rolls the whole call back;
   - then its Imprints run for every Pair, and every promise of every
     Pair is checked (§0.6).

   Linkings made after that get every Layer. When the Tag that grants a
   Link and the Shape that extends it apply in one call, the Link is
   built with both Layers at once.

   A Pin may not patch what an ordinary Tag's Agents do (§1.9), because
   on a class the Agent scope and the Tag scope share one dictionary. A
   Link is composed by the kit for each Agent, so its Layers are the
   kit's to manage, as an Agent's Overlay is.

### 5. Linking

A Link is a Tag. Every Ring 0 act works on it:

| Act | Spelling |
| --- | --- |
| link | `charlie.Knows(ruth, **inputs)` |
| is linked now? | `ruth in charlie.Knows` |
| was ever linked? | `isinstance(ruth, charlie.Knows)` |
| the sound Contacts / the defective ones / all of them | `for contact in charlie.Knows`, `~charlie.Knows`, `charlie.Knows[:]` |
| algebra | `charlie.Knows & bob.Knows`, `\|`, `-` |
| the Pair, its Records and Actions | `charlie.Knows[ruth]`, `charlie.Knows[ruth].since`, `charlie.Knows[ruth].Greet()` |
| is the Pair sound? | `bool(charlie.Knows[ruth])` |
| unlink (Rip) | `del charlie.Knows[ruth]` |
| unlink every Contact | `del charlie.Knows[:]` (STEP-SPEC-24) |

1. **Linking is a tagging of the Contact** (§0.6), with the Pair as
   receiver:
   - the gate runs;
   - the Pair's Records are built at Parts;
   - the Contact enters the Field at Commit;
   - the Imprints run;
   - the Pair's promises are checked, and the Contact's own promises are
     re-checked at this boundary, as at every tagging (§2.4). A broken
     one raises, and the linking stays.

   If the Contact was not an Agent before, she becomes one, with what
   that brings: her runtime type may change, and copying her is refused
   (§0.1, Ring 4). Nothing else is written on her. The kit never checks
   the membership or the soundness of the Agent who links. A gate that
   cares says so.
2. **Through a Link's Form.** Linking through a Shape Link links through
   its Base Links first, Bases first, each once (§0.5).
   `charlie.Trusts(ruth)` makes Ruth a Contact of `charlie.Knows` too.
   Membership is closed upward (§0.3): `ruth in charlie.Knows`. Unlinking
   her from a Base Link while a Shape Link still holds her is refused
   (§0.7): `del charlie.Trusts[ruth]` comes first.
3. **One Pair for each Contact, across a Link's Form.** A Link and its
   Base Links share one Pair for each Contact, as an Agent is one object
   across the Tags of its Form. `charlie.Knows[ruth]` and
   `charlie.Trusts[ruth]` are the same Pair, and its Records and Actions
   overlay in Form order (§1.2, §1.3). Independent Links of one Agent
   have separate Pairs.
4. **Reapplying is a no-op** (§0.5), so an Imprint that links back ends
   after one echo.
5. **A failure inside a Relation's Imprint is that Imprint's failure.**
   This includes a nested linking's refusal: it surfaces as
   `TagImprintError`, with the nested failure as its cause, and the
   linking stays (§0.6). TopKit 0.2.0a4 rolls the outer call back
   instead. That defect affects every Tag, not only Links, and is fixed
   on its own before this STEP is built.
6. A linking made inside a call that later rolls back is undone with it
   (§0.6).
7. While an Agent's deletion is ending its Links (rule 8.3), linking
   through them is a Composition Failure. An explicit `del
   charlie.Knows[:]` follows STEP-SPEC-24, rule 1.5 instead: a Contact
   linked again during it stays.
8. **A Link that outlives the Agent who held it**, because a name still
   holds it (`k = charlie.Knows`), has an empty Field (rule 8.3). Linking
   through it is a Composition Failure, nothing changed: "this Link's
   Agent no longer exists". `k[ruth]` and `del k[ruth]` answer as for any
   Agent who is not linked: a Resolution Failure (§0.7, rule 7.4).

### 6. One direction

1. **A Link points from the Agent who holds it to its Contacts.** TOP has
   no spelling that walks back, from a Contact to the Agents whose Links
   hold her.
2. **Nothing public on a Contact names an Agent who links her.** Her
   `Tags`, her `Outline`, her format specs, her contract, her keywords
   and her attributes never list the Links that hold her.
   - By name, `ruth.Knows` is Ruth's own Link if she holds one (a Link
     is sticky, rule 4.5). Otherwise it is a missing attribute. It is
     never a view of another Agent's Link. This amends the by-name view
     of §1.7 for Links.
   - `isinstance(ruth, charlie.Knows)` still answers, because it is asked
     with the Link already in hand.
3. **A Link names no Agent.** Nothing public on a Link, or on a Pair,
   leads to the Agent who holds it. The kit keeps that Agent only where
   it must run the Link's functions (rules 3.6 and 8.4), weakly and out of
   public reach, so a Link never keeps its Agent alive (finding 1). A
   Pair's functions receive the Agent in their first seat, and that is
   the Link's own code.
4. **Two ways is written, never assumed.** A Link that should answer back
   says so in its own Imprint (section 10, *Two ways, written down*).
   Breaking the barrier is an explicit act.
5. **What the barrier is.** It is a boundary of the spellings on a Contact
   and on a Link. It is not a sandbox: Python code in the same process
   can read any object's insides. Nothing on Ruth, and nothing on a Link,
   names the Agent who links her.

   The barrier does not hide those Agents from a search. Code that holds
   the declaring Tag can find them with STEP-SPEC-23's Filters:
   - `Social.Knows[:] == ruth` finds the sound Agents who know Ruth, and
     `Social[:].Knows[:] == ruth` all of them;
   - `Social.Knows == link` finds who holds a Link.

   Any module that imports `Social` holds it, and `Tags(ruth)` lists it
   when Ruth carries Social herself. A plain loop over `Social[:]` finds
   the same, Filters or not. Either way, the search misses an Agent who
   was Ripped from Social, because Links are sticky. Open question 2 asks
   whether naming the declaring Tag is explicit enough.

### 7. The Pair

1. **`charlie.Knows[ruth]` is the Pair.** This amends §1.7 for Links:
   - On an ordinary Tag, `Tag[agent]` stays as §1.7 says: a read-only
     snapshot of the Overlay, as it was right after that Tag applied.
   - On a Link, `Link[contact]` is the Pair instead: live, and holding
     what the Link's Form gives the Pair. It is not a view of the Contact.
   - It needs a linking, not active membership: it lives from step 2 of
     the linking until the Link's teardowns have run (rule 7.4).
   - A Link has no Agent-bound view of its Contact, by class or by name.
2. **The Pair holds what a Link gives**, as an Agent holds what a Tag
   gives:
   - Records, read and written as ordinary attributes,
     `charlie.Knows[ruth].since = 2011`;
   - Actions, called on the Pair, `charlie.Knows[ruth].Greet()`;
   - conditions, each read by name as a plain boolean (§2.5),
     `charlie.Knows[ruth].Still_Honest`;
   - secrets, which resolve only inside the Link's own functions (rule
     3.6);
   - the published members of the Link (rule 2.3), and its keywords if
     it is a Flag.
3. **A Pair is sound or defective on its own.**
   - `bool(charlie.Knows[ruth])` is `True` exactly when every promise of
     the Pair holds.
   - A Pair's promises are checked at its linking (step 5), and at every
     extension of the Link (rule 4.6). They are read like an Agent's
     (§2.5).
   - The Link's sound population, `for contact in charlie.Knows`, holds
     the Contacts whose own contract holds and whose Pair holds.
     `~charlie.Knows` holds those with either one broken.
   - A broken Pair never makes the Contact defective anywhere else
     (finding 4): her own truth is her own contract.
4. **A Pair lives as long as its Contact is linked in the Form.** The
   Link's own teardowns can still read it while they run, on every path
   (rules 8.1, 8.3 and 8.4). That includes a Contact collected in a
   reference cycle, who has already left the Field when her finalizer
   runs: the Pair ends after the teardowns, not with the Field entry.
   After that, reaching it is a Resolution Failure. Linking again builds
   it fresh (§0.7).
5. **Nothing of the Pair lands on the Contact.** `ruth.since` is Ruth's
   own attribute or nothing. A Pair is reached only through the Link of
   the Agent who holds it: a Contact has no spelling for it.

### 8. Ending

1. **`del charlie.Knows[ruth]`** ends Ruth's membership and removes her
   from the Field. Then the Link's teardowns run, with `(charlie, ruth)`.
   Then the Pair ends, unless a Link of the same Form still holds her. In
   that case, what the Ripped Link gave the Pair stays on it, sticky
   (§0.7).
2. **`del charlie.Knows[:]`** unlinks every Contact, as a Field Rip
   (STEP-SPEC-24).
3. **The Agent's deletion ends its Links.**
   - Inside the Agent's finalizer (§3.2), after its own teardowns, each of
     its Links is Field-Ripped, Shape Links before their Bases. The dying
     Agent sits in the first seat, as the finalizer already holds it, so
     that seat is never `None`.
   - Each Link, now held by no one, then ends with its Field already
     empty (STEP-SPEC-24).
   - In a reference cycle, the language may end a Link before the
     Agent's finalizer runs. So a Link's own end never runs a teardown.
     The Agent's finalizer still finds the Link, because in a cycle
     every finalizer runs before anything is cleared, and Field-Rips it
     as above.
   - An interrupted teardown does not skip this (§3.2).
   - At interpreter exit, this runs only for an Agent registered with
     `At_Exit`, in that pass. That amends §3.2's `At_Exit` row: it also
     ends that Agent's Links. Otherwise nothing runs at exit
     (STEP-SPEC-24, rule 3.3).
4. **A Contact's deletion unlinks her.** She leaves every Link that holds
   her, as §3.2 Rips an Agent from its Tags, and the Link's teardowns run
   with the live Agent who held her. If that Agent cannot be reached,
   because it was collected in the same cycle, the Pair ends silently:
   she leaves, and no teardown runs.
5. **Each Pair's teardowns run at most once.** A self-link,
   `charlie.Knows(charlie)`, is reached from both sides.
6. **An Agent that holds Links and is also a Contact**, deleted: first its
   own teardowns run, including its exits from other Agents' Links. Then
   its own Links end.
7. **Contacts that the Agent's finalizer never reached** (it did not run,
   or it stopped before reaching the Link) get no teardown when the Link
   ends. Those Pairs end silently, as in rule 8.4.

### 9. The Relation itself

The Relation is a template, never a Tag in play, and it has no Field.
Nothing applies, asks, walks, views, combines or Rips membership through
it. What `Social.Knows` reads depends on STEP-SPEC-23.

**Without STEP-SPEC-23**, `Social.Knows` reads as the Relation. Every act
of §0.8 on it is a Composition Failure, so a reader of the first draft is
told plainly, not answered `False`. That covers:
- `Social.Knows(x)`;
- `x in Social.Knows` and `isinstance(x, Social.Knows)`;
- `for x in Social.Knows`, `len(Social.Knows)` and `if Social.Knows:`;
- `~Social.Knows`, `Social.Knows[:]` and `Social.Knows[x]`;
- the Relation in a population's operator seat: `Social.Knows &
  bob.Knows`, `|` and `-`;
- `del Social.Knows[x]` and `del Social.Knows[:]`;
- `Scope(x, Social.Knows)`.

Each message points to a Link: "Knows is a Relation: link through an
Agent, charlie.Knows(ruth)". `Social.Knows | None` keeps `type`'s own
meaning, as it does for every Tag.

**With STEP-SPEC-23**, a name read on a Tag follows its receiver
(STEP-SPEC-23, rule 1.1). A Link is an Agent-scope contribution, so
`Social.Knows` is a Projection: each sound Social Agent's Link. Then:
- `Social.Knows[:] == ruth` asks who knows Ruth (rule 6.5);
- the Projection refuses `in`, `del`, `~` and the population operators
  (STEP-SPEC-23, rule 1.8);
- it refuses to apply a Link, so `Social.Knows(x)` is not "everyone in
  Social links x" (STEP-SPEC-23, rule 1.9);
- `isinstance(x, Social.Knows)` and `Scope(x, Social.Knows)` are refused
  by the language itself, because a Projection is not a class.

**In a class statement's Bases**, `Social.Knows` always stands for the
Relation, so `class Knows(Social.Knows)` extends it (rule 2.6). Under
STEP-SPEC-23 this works through the language's own protocol for a Base
that is not a class (`__mro_entries__`, PEP 560), which hands the class
statement the Relation.

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

**Trust builds on knowing.** A Link whose Base is another Link of the
same Tag. Trusting someone links them as known, and a promise watches
the Pair, not Ruth:

```python
class Social(Tag):

    @Link
    class Knows(Tag):

        @Record
        def since(agent, contact, *, since=None):
            return since

    @Link
    class Trusts(Knows):

        @Post
        def Still_Honest(agent, contact):        # a promise about the Pair
            return contact.honest

        def Confide(agent, contact, secret):     # an Action of the Pair, with an argument
            return f"{agent.name} tells {contact.name}: {secret}"


Social(charlie)
charlie.Trusts(ruth, since=2015)

assert ruth in charlie.Knows                      # trusting her, Charlie knows her
assert charlie.Knows[ruth] is charlie.Trusts[ruth]   # one Pair across the Form
assert charlie.Knows[ruth].since == 2015
```

**A spy rewrites what knowing means.** Over the Summary's `Social`,
whose `Knows` has `Greet`, a Shape of the declaring Tag extends its Base's
Link by name. Every Contact Charlie already knows gets the new Layer
(rule 4.6):

```python
class Spy(Social):

    @Link
    class Knows(Social.Knows):

        @Secret
        @Record
        def cover_story(agent, contact):          # hidden outside the Link's own functions
            return "a cousin from Lyon"

        @Action
        @Underlay
        def Greet(agent, contact, underlay):      # an Action of the Pair, extended
            return underlay() + f", as {agent.Knows[contact].cover_story}"
```

**A bounded Link.** A Report on the Link, read by the gate:

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

**Old friends**, with STEP-SPEC-23's Filters. Every Pair here was linked
with a `since`. A Pair whose `since` is `None` would stop the walk,
because `None < 2000` cannot be compared:

```python
for old_friend in charlie.Knows.since < 2000:    # Charlie's sound Contacts, by their Pair's since
    print(old_friend.name)
```

**Houses.** "Owner" stays a domain word:

```python
class Estate(Tag):

    @Link
    class Owns(Tag):

        @Pre
        def Is_A_House(agent, contact):
            return contact in House

Estate(charlie)
charlie.Owns(cottage)                             # Charlie is the Agent; the cottage is the Contact
```

## Rationale

**A family of one-place Tags, not a new kind of membership.** Fixing the
first place turns a two-place statement into an ordinary Tag. The Field,
the algebra, the gate, Rip, Bases and Shapes, and history then come for
free, and mean what they already mean.

**A Tag in full, with the Pair as its Agent's place.** The Director: "A
link could, indeed, have records, actions, and contracts, as any tag
has", and "a link could extend a link declared in the same tag, for
example, or a link could extend or rewrite a link in a base tab."

The first two drafts refused Actions, promises, secrets and Bases, and
the Director asked for that choice to be justified. Its reason was real
in the first draft, and it did not survive the Pair:
- **In the first draft,** a Link gave what it declared to the Contact,
  because a Tag gives to whom it is applied. Two Agents linking Ruth then
  fought over one slot on her (findings 2 to 5). Refusing Agent-scope
  declarations was the only way to keep Ruth clean.
- **The Pair removed that reason.** It was introduced for Records, but
  the same move answers everything. Give the Pair what an ordinary Tag
  gives its Agent, and nothing reaches Ruth, whatever the Link declares.
  The second draft applied it to Records only, and left Actions and
  promises as an open question. The Director answered it.
- **Bases needed a rule, not a refusal.** "Which Base?" has one sensible
  answer: the same Agent's Link. With that answer, the laws of Ring 0
  (Bases first, membership closed upward, Rip refused while a Shape
  needs the Base) give a Link family its meaning: trusting is a kind of
  knowing.
- **Two refusals keep a real reason.** An ordinary Tag as the Base of a
  Relation would be written on the Contact at every linking, breaking
  the barrier without a word; an Imprint says the same thing out loud. A
  Link between Tags (a Pin) needs its own receiver rule, and is its own
  topic.

**Extending a held Link touches every Pair.** A Shape extends its Base
for every Agent it applies to. For a Link, the Agents' place is the
Pairs, so extending Charlie's Link extends every Pair it holds, through
the same gate, Parts and promises as a tagging. The other choices both
break something. Building a new Link for the Shape would drop Charlie's
existing Contacts out of `charlie.Knows`. Giving the new Layer only to
later linkings would leave one Field with two kinds of Pair.

**Held like a Record, but a Tag.** The Director: "It wouldn't 'conflict'
with a record. It would BE the record. They could be another kind of
grants by a tag, themselves." The Link sits in the Record's seat: it is
built at Parts, stored on the Agent, and stays after Rip. But it is a
Tag: something the Agent's relationship *is* (*ser*), not a value the
Agent currently holds (*estar*). So it is never reassigned.

**The Agent first.** The Director proposed it: "maybe links should have
an agent parameter to operate on the agent that owns the link and a
contact parameter to operate on the target. first input by default agent
owning the tag, and the second the contact agent." And later: "an agent
and a contact makes clear who is the main subject and who is the object
in the sytax ... agents always have the agency is a good rule of thumb."

Four reviewers tested the order against the Specification and the kit,
and each concern went to a skeptic. It held, for four reasons:
- **It is §1.1's receiver rule, applied faithfully.** The Link is the
  Agent's contribution. With the Contact in the first seat, the receiver
  rule lands the Link's protocols on the Contact, which is finding 5.
- **It matches §1.5.** The holder comes first and the Agent second, as in
  `dispatch(agency, sender, message)`.
- **One word, one meaning.** Inside `class Social`, `agent` is Charlie on
  every line, and one indentation down it still is.
- **The deletion path already holds the Agent.** The finalizer has the
  dying Agent in hand, so the first seat is never `None`.

**Two seats, then the ordinary rules.** One sentence carries every kind:
after the two seats, an Action, a Record, a condition, an Imprint or a
teardown reads exactly as it does after an ordinary Tag's one seat.
Nothing new to learn past the second seat. In TopKit it is one more seat
bound by position before the inputs.

**Agent and Contact, not Owner.** The Director: "I don't like the Owner
language. I'd keep the agent, as it is the same as for actions and
records, and owner can be informal but not formal term." A formal "Owner"
would also clash with domains that have owners of their own, such as
`charlie.Owns(cottage)`.

**Both seats, always.** A one-seat body copied from an ordinary Tag, such
as `def Is_Person(agent)`, would check the Agent who links when the
author meant the Contact. Requiring both seats turns that slip into a
message at class use.

**The Agent's door and the Pair's, never the Contact's.** If the Contact's
door opened too, a Link would be a way to read a stranger's secrets: link
her, then look inside. That crosses the same barrier the Director drew,
from the other side.

**One direction.** The Director: "They are one directional, so you should
declare the link to be bidirectional in the linking ... Sometimes roads
walk in only one direction, and you may not want to be able to access
charlie from ruth. ... the safety comes from not being able to be tracked
from your contact if it's compromised, unless you declare it so. Breaking
a barrier should be explicit."

**The Pair, under the view's spelling.** The Director: "we may need
records on a link too... like a relationship's attribute ...
`charlie.Knows[ruth].since`". §1.7's `Tag[agent]` is a read-only snapshot
of the Agent right after that Tag applied. On a Link, a snapshot of the
Contact would show nothing the Link gave her, because a Link gives her
nothing but membership. So the spelling is put to better use: on a Link
it is the Pair. That puts the facts about two Agents in the one place
that belongs to both of them and to neither (finding 2).

**Ending with the Agent.** The Director: "eliminating the agent of the
link ... should functionally rip the agents ... as normal Tag deletion."
With STEP-SPEC-24, a Link's end is a Field Rip like any Tag's. The Agent
ends its Links first, while it can still fill the first seat.

## Backwards compatibility

Nothing changes for code that does not write `@Link`. One new public
name: `Link`. No parameter name is reserved.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| A Record holding a hand-made Tag (the workaround) | Works for membership. Set aside for findings 1 to 5, which only the kit can close. Not taught in the Guide: it would teach the leak. |
| A Record holding a set of Agents (`charlie.known = WeakSet()`) | Cheap, and right when nothing else is needed. But it has no gate, no Rip protocols, no history and no algebra: "a value can be flipped back, membership is a state of the architecture" (Guide, Pattern 11). |
| One Tag with an input, `Knows(ruth, by=charlie)` | Reapplying an active Tag does nothing (§0.5), so only one Agent could ever know Ruth. |
| A Pin | Wrong receiver: a Pin puts meaning on a Tag, not on an Agent (§1.9). |
| A Link without Actions, promises, secrets or Bases (the first two drafts) | Withdrawn after the Director's review: the refusals guarded the Contact, and the Pair now guards her better. |
| An ordinary Tag as a Base of a Relation | Refused: it would write that Tag on the Contact at every linking, without a word. An Imprint says it out loud. |
| A Shape's Relation of the same name as a new Link | Rejected: existing Contacts would fall out of `charlie.Knows`. |
| A Shape's Relation that reaches only later linkings | Rejected: one Field would hold Pairs of two kinds. |
| The Contact first and the holder by name, `def Not_Oneself(agent, owner)` (the first draft) | Set aside: with the Contact first, the receiver rule lands the protocols on the Contact (finding 5). A seat passed by name would also be a new kind of seat. |
| The Contact first and the holder positional second (one reviewer's repair) | Set aside for the same landing. It would also make `agent` mean Ruth inside `class Social`, one indentation below where it means Charlie. |
| "Owner" as the term for the holding Agent | Withdrawn by the Director: the Agent has the agency, and "owner" stays a domain word. |
| `member` instead of `contact` | Set aside by the Director: "an agent and a contact makes clear who is the main subject and who is the object". `member` also already names contributions in §1.5 ("a published member"). |
| An optional Contact seat, passed only when declared | Rejected: a one-seat body would silently check the Agent who links. |
| The Contact's door open too | Rejected: linking would become a way to read the Contact's secrets. |
| A query from the Contact back to the Agents who link her, `Owners(ruth, Social.Knows)` or `ruth in Social.Knows` (the first draft) | Withdrawn by the Director: links point one way, and TOP speaks in the language's own structures, not in query functions. The spelling is now a Composition Failure (section 9). |
| The holding Agent in the Link's display, `Knows[Charlie]` (the first draft) | Withdrawn: it would lead from the Contact to the Agent. |
| A marker for two-way Links, `@Link(both_ways=True)` | Set aside: the Imprint says it in two visible lines, and a marker would hide what runs. |
| The Relation as a Base of every Link | Rejected: Rip never cascades (§0.7), so membership in the Relation would outlive the last linking. |

## Open questions for the Director

1. **Extending a held Link (rule 4.6).** Extending Charlie's Link touches
   every Pair it holds, inside the call that applies the Shape. So
   `Spy(charlie)` costs one tagging per Contact, and one Contact the new
   gate refuses refuses `Spy(charlie)` as a whole. The alternative
   allows a same-name extension only before the Link holds any Contact,
   and refuses it after. That is cheaper, but `Social(charlie);
   charlie.Knows(ruth); Spy(charlie)` would then fail while
   `Spy(charlie)` alone works. The STEP recommends extending every Pair.
2. **The barrier and Filters.** You asked for "who knows ruth" as
   `Social[:].Knows[:] == ruth`, which under STEP-SPEC-23 is also
   `Social.Knows[:] == ruth` for the sound members. You also said
   "Breaking a barrier should be explicit."
   - With STEP-SPEC-23, any code that holds `Social` finds Charlie from
     Ruth.
   - `Social` is a module global, and `Tags(ruth)` lists it when Ruth
     carries it herself.
   - The same code finds who holds a Link with `Social.Knows == link`.

   Is naming the declaring Tag explicit enough? Or should a Projection
   refuse to read a Link (both `.Knows[:]` and `.Knows`) unless the
   Relation declares that it may be searched?

## Acceptance requirements

- The nested-Imprint defect (rule 5.5) is fixed first, in every Tag.
- STEP-SPEC-24 is Cleared, for rules 8.2 and 8.3.
- `tests/test_topkit.py`: a `LinkTests` class that covers:
  - every numbered rule above, each refusal with nothing changed;
  - findings 1 to 5 as regression tests: the Agent collected while a
    Contact lives; two Agents linking one Contact with no warning and no
    shared slot; nothing of the Link readable on the Contact;
  - the Pair: Records, Actions with arguments, conditions read by name,
    secrets resolving only inside the Link, published members, Flag
    words, soundness and the sound and defective populations;
  - seats: each kind after the two seats (Underlay, stored, inputs), and
    every refusal of rules 3.3 and 3.4;
  - Bases: per-Agent resolution, linking through a Shape Link, Rip
    refused on a Base Link, one Pair across the Form, an ordinary Tag
    refused as a Base;
  - extending a held Link: the gate for every Pair at once, a failing
    Pair Record rolling the call back, Imprints and promises for every
    Pair, and the Link's identity, Field and history kept;
  - the closed slot of rule 4.4, in both orders, `@Delete` included;
  - the doors of rule 3.6: the Agent's and the Pair's secrets resolve,
    the Contact's do not, at linking and in teardowns at either one's
    deletion;
  - every spelling of section 9 refused on the Relation;
  - the Agent in a reference cycle, built both before and after its Link:
    each teardown runs once, with the Agent, and none with `None`;
  - a Contact in a reference cycle: the teardown reads the Pair;
  - a Link held after its Agent's death: linking refused, and a
    Resolution Failure for `k[x]` and `del k[x]`;
  - the barrier: no spelling on a Contact, a Link or a Pair names the
    Agent who links her (rules 6.2 and 6.3). The search from the
    declaring Tag (rule 6.5) is tested under STEP-SPEC-23, once the
    Director decides open question 2.
- `tests/spec_examples.py`: the §1.10 examples.
- `tests/oracle_topkit.py`: Links in the random walk, with Link families,
  extensions, and Agents and Contacts deleted mid-walk.
- `benchmarks/scenarios.py`: a linking scenario, and the cost of
  extending a Link that holds many Contacts. The Links of one Relation
  should share its functions and one runtime composition, rather than
  build a class and a scan per Agent.
- The Guide: a pattern, "Your contacts", written when this STEP is
  Deployed.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
