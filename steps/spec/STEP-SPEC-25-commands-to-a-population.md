# STEP-SPEC-25: Commands to a Population

- **STEP:** SPEC-25
- **Desk:** spec
- **Title:** Commands to a Population
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08
- **Revised:** 2026-10-08, after three independent reviews: Spec
  consistency, Python semantics, and design and clarity.

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

STEP-SPEC-23 taught a Tag to answer **questions** about its members,
`Wizard.level > 3`. This STEP is about **commands**: changing every
member at once.

- **A write through a population.** `Enemy[:].hp = 10` sets the `hp` of
  every Enemy. It is one act. Every member is checked before anyone is
  written. One refusal refuses the whole write, and a failure halfway
  undoes what was written.
- **The Tag keeps its own names.** `Enemy.hp = 10` keeps the meaning
  Python gives it: an attribute of the Tag itself. When `hp` is a name
  the Tag gives its Agents, that line is a mistake. Today it silently
  breaks the Tag. Now it is refused, and the message shows the spelling
  above.
- **No new spelling for broadcasting an Action.** This STEP argues that
  a broadcast Action should stay a `for` statement (section 6). It does
  not add one. `Enemy.Take_Damage(5)` stays a question, as STEP-SPEC-23
  made it. The kit adds a safer walk, and a warning that names the loop.

```python
Enemy[:].hp = 10                          # every Enemy, sound or defective
(~Enemy).hp = 10                          # repair the defective ones
(Enemy[:].hp < 5).hp = 5                  # a Filter as the root: every weak Enemy
(Enemy[:] & Enemy).hp = 10                # only the sound ones

for enemy in Enemy:                       # an Action, to each sound Enemy
    enemy.Take_Damage(5)

charlie.Knows[:].since = 2011             # through a Link: every Pair's since
```

## Motivation

### A question and a command

STEP-SPEC-23, section 6, left two acts out:
- writing through a Projection, such as `Wizard.hp = 10`;
- broadcasting an Action for its effect, such as `Enemy.Take_Damage(5)`.

It said: "These are commands, not questions, and each deserves its own
STEP." The Director: "I like the Writing through a Projection and
Broadcasting an Action ideas. Let's start a branch and step for it".

One rule shapes this whole STEP: **a command must not look like a
question.** If the two look alike, a reader cannot tell whether a line
changes the system or only asks about it. A Filter that ran a command at
every walk would change the system each time someone counted it.

Python already tells the two apart. A question is an **expression**: it
has a value. A command is a **statement**: assignment, `del`, `for`. This
STEP keeps every command a statement.

### What happens today

Checked on TopKit 0.2.0a4 with the change of pull request #26, on
2026-10-08. `Enemy` has a Record `hp`, an Action `Take_Damage`, and the
promise `Alive` (`hp > 0`).

| # | Written | What happens | Why it matters |
| --- | --- | --- | --- |
| 1 | `Enemy[:].hp = 10` | Stored on the Field object, which is the same object every time. `Enemy[:].hp` then reads 10, and no Enemy changed. `(~Enemy).hp = 10` is stored on a new object, and lost. | Silent. It looks like it worked. STEP-SPEC-23 already requires this to be refused. |
| 2 | `Enemy.hp = 10` | Before the Tag's first use, it **destroys the Record**: every later Enemy has no `hp`. After first use, it is stored on the Tag, `Enemy.hp` reads 10, and no Enemy changes. | Silent, and it can break the Tag for good. Under STEP-SPEC-23 the Projection `Enemy.hp` also becomes the number 10. |
| 3 | `for e in Enemy: e.Take_Damage(5)`, and one member raises | The loop stops there. The members before it took damage; the members after it did not. | Loud, but half done, and the failure does not name the member. |
| 4 | the same loop, and one member's Action Rips a later member | The Ripped member still gets the command when its turn comes. | A walk commands an Agent that has already left. |
| 5 | `ari.Alive = False` (`Alive` is a condition) | Stored. `ari.Alive` reads `False` while `bool(ari)` is `True`. | A defect against §2.5, which says a condition read by name is "never stored". |
| 6 | `ari.Take_Damage = 5` | Stored. The Action is gone from Ari, with no warning. | A write that replaces behaviour. |

Findings 1 and 2 are the trap this STEP closes. A program that tries to
write through a Tag today is told nothing. Findings 3 and 4 are why a
plain loop is not enough for writes. Finding 5 is a defect to fix on its
own, before this STEP is built. Finding 6 is its own topic (section 7).

### Why not just a loop

The loop is the baseline, and it stays valid:

```python
for enemy in Enemy[:]:
    enemy.hp = 10
```

For a write, one act can promise more than the loop can:
- **all or nothing.** The kit can check every member first, and can put
  back a value it wrote. A loop that fails halfway leaves half the
  population changed (finding 3);
- **a fixed set of members.** Writing `hp` while walking `Enemy[:].hp <
  5` changes the Filter during the walk. One act walks a snapshot;
- **one expression for the members.** The population is written once, in
  the algebra: `(~Wizard | ~Fighter).alive = True`.

For an Action, none of these hold. An Action can do anything, so the kit
cannot put it back. That is why the two halves of this STEP end in
different places (section 6).

## Specification

The changes to the Specification:
- a new section, **§2.10 Commands**, in Ring 2, after STEP-SPEC-23's §2.9
  Filters;
- one row in §0.8, and a sentence there: on a Tag, a name the Tag gives
  its Agents cannot be assigned or deleted;
- an amendment to §2.5: a walk of a Field skips a member that has left
  it (rule 6.5).

It amends STEP-SPEC-23, which refuses assignment on a population in
four places:
- rule 1.4;
- section 6;
- its Acceptance requirements, in the refusal tests and in "TopKit:
  populations refuse assignment of names".

A population still has no names of its own. Now a public name assigned on
it is its members' name (rule 1.1). STEP-SPEC-23, rule 3.3, also changes:
its warning names the loop (rule 6.4).

In this STEP, § cites the Specification only. This STEP's own parts are
cited as "section N" or "rule N.M".

### 1. Writing through a population

1. **Assigning a public name on a population writes it on each member.**
   `root.name = value` does what `member.name = value` does, for each
   member of the root, as one act (sections 2 and 3). The root is any
   population:
   - the whole Field, `Enemy[:]`;
   - the defective population, `(~Enemy)`. The brackets are needed: the
     language reads `~Enemy.hp` as `~(Enemy.hp)`;
   - a combined view, `(Wizard[:] | Fighter[:])`;
   - a Filter, `(Enemy[:].hp < 5)` (STEP-SPEC-23, section 2).

   This mirrors reading (STEP-SPEC-23, rule 1.2): `Enemy[:].hp` reads
   each member's `hp`, and `Enemy[:].hp = 10` writes it.
2. **A Tag is never the root of a write.** §0.8 gives the Tag's dotted
   names to the program. So on a Tag, assignment keeps the language's
   meaning (section 4), and a write always names a population. The sound
   members are written through a population that says so:
   `(Enemy[:] & Enemy).hp = 10`.
3. **A root means what it means everywhere.** A write reaches exactly the
   members a read of that root would reach (STEP-SPEC-23):
   - "every Enemy is healed" is `Enemy[:]`;
   - "repair the broken ones" is `~Enemy`;
   - "only those still fit to fight" is `Enemy[:] & Enemy`;
   - a Tag inside a root is its sound population, as in every operator
     seat (§2.5). So `(Enemy.hp < 5)` holds only sound Enemies, and
     `(Wizard | Fighter)` only sound Wizards and Fighters. To include the
     defective ones, write `Enemy[:].hp < 5`.
4. **One value, the same object, for every member.** The value is
   evaluated once, and every member receives that one object. Nothing is
   copied, as in the language's own `a = b = []`. So
   `Wizard[:].spells = []` gives every Wizard **one shared list**. For a
   fresh value per member, use a `for` loop (open question 3).
5. **A Projection is never a value.** `Enemy[:].hp = Enemy[:].max_hp`
   would give every member the Projection object itself. It is refused
   with a `TypeError` before anything changes. Writing a different value
   to each member is not in this STEP (section 7). A population is a
   value like any other, so `Enemy[:].target = (Hero.hp > 0)` gives every
   Enemy the same live Filter.
6. **On a Pin**, each member is a Tag. A write through a Pin's population
   writes that Tag's own attribute, as an assignment on that one Tag
   would (section 4). `Rare[:].rarity = "common"` writes the Report each
   pinned Tag holds.
7. **An empty root** is written with nothing changed, and no failure.

### 2. The check before writing

Before anything is written, every member of the snapshot (rule 3.1) is
checked. This STEP calls it **the check before writing**. A member passes
when `member.name = value` is a write this STEP allows. The check reads
nothing through a host's code: it runs no property, no host
`__getattr__`, and no condition.

1. **Only a name each member already holds.** A write through a
   population never creates an attribute. A member that does not hold the
   name refuses the write. So a misspelt name, `Enemy[:].hp_ = 10`, is
   loud, as it is for a read (STEP-SPEC-23, rule 1.7). To give a
   population a new attribute, use a `for` loop: creating a name is an
   explicit act.

   An Agent **holds** a name when one of these has it:
   - the Agent's own attributes;
   - what its Tags gave it: Records, Actions, conditions, views and
     published members;
   - its host class, looked up without running it (in Python,
     `inspect.getattr_static`). A slot the class declares counts, even
     when it is not set yet.

   A name that only a host's `__getattr__` answers is not held.

   A **Tag** holds a name when the Tag or a Base in its Form holds it in
   Tag scope: a Report, an Operation, what a Pin landed, or another name
   the program put there. A Projection is never a held name
   (STEP-SPEC-23, rule 1.1), so `Rare[:].rarty = "x"` is refused.
2. **Data only, never behaviour.** A write replaces a value. It never
   replaces what an Agent or a Tag does. Refused:
   - an Action, including a published Operation and a teardown (§1.2,
     §1.5, §3.1);
   - on a Tag, an Operation, including one a Pin landed (§1.9);
   - a host method: a function, `classmethod` or `staticmethod` found on
     the host class.

   A Record whose value happens to be callable is data, and may be
   written. Behaviour changes through a Tag.
3. **Read-only names stay read-only.** Refused, as each is on one Agent:
   - a published Report (§1.5);
   - a condition read by name (§2.5);
   - an Agent-bound view by name, `ari.Paladin` (§1.7);
   - a held Link (STEP-SPEC-22, rule 4.3);
   - a host property without a setter.

   On a Tag member, rule 4.2 is part of the check: a name the Tag gives
   its Agents is refused here, before anything is written.
4. **Secrets stay secret** (§1.5). Each member is written as
   `member.name = value` would be at that moment. A secret is written
   only while its composition door is open:
   - for an Agent, while an Action, Imprint, Record builder, condition
     or Rip protocol bound to that Agent is running (§1.5);
   - for a Pair, while one of its Link's own functions is running
     (STEP-SPEC-22, rule 3.6);
   - for a pinned Tag, while that Tag's own protocols or pinned
     Operations are running (§1.9).

   A write through a population never opens a door. In practice a secret
   passes only when the write runs inside the one member it is written
   on.
5. **Names that begin with an underscore** are never written through
   (STEP-SPEC-23, rule 1.4). Assigning one on a population is refused.
6. **Rogue and defective members are written like any other.** Writing a
   Record is how a defective member is repaired: `(~Enemy).hp = 10`. A
   Rogue Agent keeps its Records (§0.7), and they can be written. A
   published Report is refused by rule 2.3 for every member, Rogue or
   not, so a write never raises a Rogue Access Failure.
7. **One refusal refuses the whole write.** It is a Composition Failure,
   and nothing has changed. Its message names each refused member, the
   name, and the reason. Its cause is an `ExceptionGroup` that holds the
   failure each refused member alone would give. A misspelt read stops at
   the first member, with the language's own failure (STEP-SPEC-23, rule
   1.7). A write is one act over many members, so it reports them all at
   once, as a Field Rip does (STEP-SPEC-24, rule 1.2).

### 3. Order, snapshot and failure

1. **A snapshot.** The root is walked once, at the start, before the
   check before writing. The members found then are the members written,
   in the root's order (the order `for` walks it). A write that changes
   the root during the act changes nothing about who is written:
   - `(Enemy[:].hp < 5).hp = 5` writes every Enemy that was weak at the
     start, though after its write that Enemy is no longer weak;
   - `(~Enemy).hp = 10` writes every defective Enemy, though each one
     leaves `~Enemy` as it is repaired.
2. **All or nothing.** The check before writing (section 2) looks at every
   member before the first write. Then the writes run, in order.
3. **A failure during the writes undoes the act.** A host's own
   `__setattr__`, or a setter, can still fail. Then:
   - the writes already made are undone, newest first;
   - the failure is raised as a Composition Failure that names the
     member, with the host's failure as its cause.

   To undo, the kit remembers, for each member before writing it, the
   value the name read and where that value lived:
   - **on the member itself** (in Python, its own `__dict__` or a set
     slot): the old value is written back;
   - **in a host data descriptor**, such as a property with a setter:
     the old value is written back through the descriptor;
   - **on the host class, as a plain value**: the write made the member
     its own attribute, so that attribute is deleted. The member reads
     the class's value again, and follows it, as before.

   This is the call boundary of §0.6: nothing partial is published. An
   interruption, such as `KeyboardInterrupt`, also undoes the act, and is
   then raised as it was.

   Undoing runs host code again: a setter, or a host `__setattr__`. A
   host's own side effect cannot be undone (Ring 4, raw side effects). If
   undoing fails too, that failure is attached to the one raised, and it
   names the member left changed.
4. **No promise is checked.** A write through a population is play, not a
   tagging boundary. Conditions "run at tagging boundaries, never
   continuously during play" (Ring 2), and "do not check themselves
   during play" (§2.4). One write checks no promise, so a write to many
   members does not either.

   A member whose promise breaks becomes defective, and moves to
   `~Enemy`. A member whose promise is repaired moves back. Truth reads
   it at once (§2.5), and published members refuse a defective member by
   name (§1.5). This is as loud as one write is today. A warning after
   the write would need every member's promises checked, which is the
   very check Ring 2 keeps out of play.
5. **One thread** (Ring 4). The act is not guarded against another thread
   writing the same members.

### 4. Assignment on a Tag

1. **On a Tag, assignment keeps the language's meaning.** `Enemy.name =
   value` sets an attribute of the Tag itself, as today (§0.8). A Report
   is written this way: `Secret_Agent.active += 1` (§1.4). So is a Pin's
   un-patching, `tag.Control = original.Control` (§1.9).
2. **Refused: a name the Tag gives its Agents.** Assigning or deleting,
   on a Tag, a name that the Tag or a Base in its Form declares **for
   its Agents** is a Composition Failure, and nothing changes. On a Link,
   its Agents' place is the Pair (STEP-SPEC-22, rule 2.3), so this covers
   what the Link gives its Pairs. These are the names §1.9 already
   refuses to a Pin:
   - Records and Actions;
   - protocols: Preconditions, Imprints, Postconditions, teardowns,
     `@Delete` and `__del__` Layers;
   - Links (STEP-SPEC-22);
   - a name every Tag answers through its metaclass.

   Also refused: on a pinned Tag, the name of one of its own conditions,
   which it reads by name (§2.5, `Wizard.Has_Members`). It is
   read-only, as on an Agent (finding 5).

   **A name with a Tag-scope slot stays writable.** §1.1 lets a Report
   `colour` and a Record `colour` live side by side, as two slots. When
   the Tag holds the name in Tag scope too, assignment writes that slot,
   as today.

   The message shows the spelling that was probably meant: "hp is a
   Record of Enemy's Agents. To write it on each member, name the
   population: Enemy[:].hp = 10."

   This is the refusal §1.9 makes for a Pin, for the same reason: in
   Python, the Tag's own names and its Agents' declarations share one
   class dictionary. Today the write is stored silently, and before the
   Tag's first use it destroys the declaration (finding 2). The kit
   therefore reads the Tag's declarations before it accepts any write on
   the Tag.

   `Enemy.hp -= 5` reads `Enemy.hp`, a Projection, and fails at the `-`
   before it assigns (section 7). That failure's message names the
   population spelling too.
3. **A new public name that the members hold warns.** Assigning, on a
   Tag, a public name that neither the Tag nor its Bases hold yet raises
   a warning when a member of its Field holds it (rule 2.1). The warning
   names the Tag, the name, and the population spelling.

   Rule 4.2 cannot see a host attribute such as `level`, because the Tag
   does not declare it. Without the warning, `Wizard.level = 3` would
   silently replace the Projection `Wizard.level` for good (STEP-SPEC-23,
   rule 1.3, which gives this warning when a Pin lands such a name).

   Its limits, said openly:
   - it asks only when the name is new on the Tag. Writing a Report that
     already exists costs nothing more;
   - a new name costs one walk of the Field, without checking promises,
     that stops at the first member that holds the name;
   - on an empty Field it cannot warn;
   - names that begin with an underscore are never asked about.
4. **The kit's own writes are not assignments by the program.** Pinning,
   its rollback, and every write the kit makes on a Tag go around rules
   4.2 and 4.3.

### 5. Through a Link

1. **A Link population writes the Pair.** STEP-SPEC-23, rule 1.5, reads a
   member reached through a Link through that Link. A write does the
   same: `charlie.Knows[:].since = 2011` writes
   `charlie.Knows[contact].since` for each Contact (STEP-SPEC-22, rule
   7.2). This holds on:
   - the whole Field of a Link, `charlie.Knows[:]`;
   - its defective population, `(~charlie.Knows)`;
   - a Filter rooted on the Link, `(charlie.Knows.since < 2000)`, which
     holds the sound Contacts, or on either population above,
     `(charlie.Knows[:].since < 2000)`.

   The Link itself is never a root, as no Tag is (rule 1.2). So the
   sound Pairs alone have no root of their own: a combined view would
   lose the Link (rule 5.3). Use a Filter rooted on the Link, or a `for`
   loop over `charlie.Knows` (open question 4).
2. **A write through a Link never reaches the Contact.** A name the Pair
   does not hold is refused before writing, even when the Contact holds
   it. A read through a Link may fall back to the Contact, because a read
   only looks. A write changes the Contact, and "Breaking a barrier
   should be explicit." To change the Contacts, use a `for` loop:

   ```python
   for contact in charlie.Knows:
       contact.mood = "cheerful"                 # an explicit write on each Contact
   ```
3. **A combined view that holds a Link population refuses writes.** A
   combined view sees no Link (STEP-SPEC-23, rule 1.5), so it reads each
   Contact's own attributes. `(charlie.Knows & bob.Knows).since = 2011`
   would write Ruth's own `since`, in a line that reads like a change to
   Pairs. So a write whose root combines any population of a Link, with
   anything, is refused before writing, and the message shows the `for`
   loop. Reads are unchanged, so a write never reaches a member other
   than the one a read of that root reads (rule 1.3).
4. **On the Link itself**, `charlie.Knows.since = 2011` is refused by
   rule 4.2: `since` is a Record the Link gives its Pairs. The message
   shows `charlie.Knows[:].since = 2011`.
5. **A fan-out is a Projection, not a population** (STEP-SPEC-23, rule
   1.8). `Social.Knows[:].since = 2011` is refused. Use a `for` loop over
   the Agents and their Links.
6. **A Pair's Action** is broadcast like any Action (section 6):

   ```python
   for contact in charlie.Knows:
       charlie.Knows[contact].Greet()
   ```

### 6. Broadcasting an Action

1. **A called Projection stays a question.** `Enemy.Take_Damage(5)` is
   lazy and runs at walk time (STEP-SPEC-23, rule 3.1). This STEP adds no
   eager form of it. One spelling with two meanings, a question inside a
   Filter and a command on its own line, is the trap this STEP must not
   build.
2. **A command to each member is a `for` statement.** The program names
   the population, and the Action runs at once, member by member:

   ```python
   for enemy in Enemy:                       # each sound Enemy
       enemy.Take_Damage(5)
   ```

   The loop is eager and returns nothing. A program that wants the
   results keeps them itself, for example in a list it fills.
3. **A command of the Agency can be an Operation.** When a command
   belongs to the domain, the Tag can own it, in the program's own words.
   An Operation receives the Tag (§1.4), and walks its members:

   ```python
   class Enemy(Tag):

       def Take_Damage(agent, amount):       # an Action: one Enemy
           agent.hp -= amount

       @Operation
       def Volley(tag, amount):              # an Operation: the whole Field
           for enemy in tag:
               enemy.Take_Damage(amount)


   Enemy.Volley(5)                           # a Tag-scope name: it reads the Tag, and runs now
   ```

   `Enemy.Volley(5)` runs at once, because a Tag's own name reads the Tag
   and always wins (STEP-SPEC-23, rule 1.1). Its name must differ from
   the Action's (rule 4.2).

   This has a cost, said openly. `Enemy.Volley(5)` runs now, and
   `Enemy.Take_Damage(5)` only asks. The two lines look alike, and only
   the declaration tells them apart. It is accepted because it is not
   new: an Operation is called on its Tag today (§1.4), and STEP-SPEC-23
   made the Tag's own names win. The Guide adds one piece of advice:
   name an Operation as the Agency's act (`Volley`, `Sound_The_Alarm`),
   never like an Agent's Action. Open question 1 asks whether that is
   enough.
4. **The warning names the loop.** STEP-SPEC-23, rule 3.3, warns when a
   called Projection is collected without being walked. Its message now
   names the spelling that was probably meant:
   "Enemy.Take_Damage(5) was never walked. A call on a Tag is a question,
   asked at every walk. To command each member, write: for enemy in
   Enemy: enemy.Take_Damage(5)."
5. **A Field walk skips a member that has left.** This amends §2.5:
   - a walk of a Field takes its members from a snapshot made when it
     starts, as TopKit already does;
   - when a member's turn comes, it is walked only if it is still a
     member of that Field. A member that an earlier turn Ripped is
     skipped (finding 4);
   - an Agent that joins during the walk is not walked. A combined view
     takes the snapshots of all its Fields when its walk starts, not
     when it reaches each side.

   Every population walks through its Fields, so the sound and defective
   populations, combined views and Filters all inherit this. None of
   them checks anything more: a Filter does not ask its question twice.
   The cost is one membership lookup per member. A sound walk already
   checks each member's promises when its turn comes, so a member that
   an earlier turn made defective is already skipped there. This is how
   STEP-SPEC-24, rule 1.5, walks a Field Rip.
6. **The first failure stops the loop**, as the language stops any loop.
   It is loud: the failure is raised where it happened. The members
   before it were commanded, and their Actions are not undone, because
   the kit cannot undo an Action. That is the rule for an Imprint that
   fails after commit: the product left the line (§0.6). A program that
   wants every member commanded, and the failures collected, writes it
   with the language's own `ExceptionGroup`:

   ```python
   failures = []

   for enemy in Enemy:
       try:
           enemy.Take_Damage(5)
       except Exception as failure:
           failure.add_note(f"Take_Damage(5) failed on {enemy!r}")
           failures.append(failure)

   if failures:
       raise ExceptionGroup("Take_Damage(5) failed on some Enemies", failures)
   ```

### 7. Not in this STEP

- **A different value for each member.** `Enemy[:].hp -= 5` reads
  `Enemy[:].hp`, a Projection. A Projection has no arithmetic, so the
  `-` fails with a `TypeError` before anything is assigned, and the
  message names the loop. This STEP requires that a Projection keep no
  arithmetic until a STEP gives it one. Arithmetic on Projections, and a
  Projection as the value of a write, are their own topic (rule 1.5).
- **A range in one comparison.** `(0 < Enemy.hp < 5).hp = 5` fails
  loudly, before anything is written, because a Filter refuses `bool()`
  (STEP-SPEC-23, section 5). Write `((0 < Enemy.hp) & (Enemy.hp < 5))`.
- **Chained writes.** `Enemy[:].weapon.damage = 3` assigns on a
  Projection, `Enemy[:].weapon`, which refuses it (STEP-SPEC-23, rule
  1.8).
- **Deleting through a population.** `del Enemy[:].hp` is refused. It
  reads too much like `del Enemy[:]`, which Rips the whole Field
  (STEP-SPEC-24). Use a `for` loop.
- **Writing through a fan-out** (rule 5.5).
- **Applying a Tag to a population**, which STEP-SPEC-23, rule 1.9,
  refuses.
- **A kit spelling for a broadcast** (open question 1).
- **Assigning over an Action on one Agent**, `ari.Take_Damage = 5`
  (finding 6). A write through a population refuses it (rule 2.2). The
  single write is its own topic.

## Rationale

**Commands are statements.** An assignment cannot sit inside a Filter, a
`len` or an `if`, so it never runs by accident while someone counts.
`Enemy.Take_Damage(5)` is an expression, and STEP-SPEC-23 made it a
question. If it were also a command, the same line would "do nothing and
warn" in one place and "hurt everyone" in another.

**The population, not the Tag, for writes.** §0.8 promises the program
the Tag's dotted names, and Python already gives `Enemy.hp = 10` a
meaning. Routing that line to the members would make its meaning depend
on where `hp` was declared: on every member if the Tag declares it, on
the Tag if the host does (`level`). Two lines that look the same would do
different things. A population has no names of its own, so on a
population an assignment has one meaning: the members'.

**No new default.** A write uses the roots STEP-SPEC-23 already defined,
with the meanings it gave them (rule 1.3). The Tag cannot be a root, so
the sound members need a longer spelling. That cost is open question 4.

**All or nothing, for writes.** A write through a population is one act,
so it gets one outcome. The kit can check every member first, and can
put a value back. That gives the promise §0.6 makes at the gate: a failed
act publishes nothing.

**A loop, for Actions.** An Action can do anything: print, send, spend,
Rip. The kit cannot put that back, so a broadcast cannot be all or
nothing. What is left is a choice between stopping at the first failure
and collecting. The loop stops; `ExceptionGroup` collects. Both are plain
Python, in the program's own words. A kit form would need a name, and
§0.8 keeps names for acts the language cannot spell. This one it can:
`for`.

**Never create, never replace behaviour.** STEP-SPEC-23 said: "A filter
that quietly drops members because of a typo ... is the bug this STEP
must never make easy." For a write, that bug is `Enemy[:].hp_ = 10`. It
would create `hp_` on every Enemy and leave `hp` alone. Refusing names a
member does not hold makes it loud. Refusing Actions keeps a write a
change of value (*estar*). What an Agent *is* (*ser*) changes through
Tags.

**No promise check after a write.** One `enemy.hp = -1` checks no
promise, so ten writes in one act check none either. Otherwise the same
change would raise when written with a population, and pass when written
in a loop.

**Through a Link, the Pair only.** The Director: "Breaking a barrier
should be explicit." A read that falls back to a Contact only looks. A
write changes her, and a line that reads like a change to Charlie's Pairs
must not change people who never chose Charlie.

**The language's own structures.** Every spelling here is the language's:
assignment, `for`, `[:]`, the operators. The Director: "I don't like
'Function calls' in TOP." This STEP adds none.

## Backwards compatibility

What changes:
1. **Assignment on a population** was stored on the population object,
   or lost (finding 1). STEP-SPEC-23 refuses it. With this STEP it writes
   the members.
2. **Assigning or deleting, on a Tag, a name the Tag gives its Agents**
   was stored silently, or destroyed the declaration (finding 2). Now it
   is a Composition Failure. Code that kept a value on the Tag under an
   Agent's name should rename it, or make it a Report. No such use was
   found in the repository: the Specification, the tests, the examples
   and the Guide only write Tag-scope names on Tags.
3. **Assigning a new public name on a Tag** that a member holds now
   warns.
4. **A Field walk** skips a member that left during the walk (rule 6.5).
   Before, it still reached it.
5. **STEP-SPEC-23's warning message** for a call never walked now names
   the loop.

What does not change: assignment on a Tag of its own names (Reports,
Operations, what a Pin lands, any other name the program puts there),
and every write on one Agent.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| The loop alone, for writes | Valid, and it stays. Set aside as the only spelling: it cannot be all or nothing, and a Filter root changes while it walks. |
| `Wizard.hp = 10` routed to the members for every name they hold | Rejected: the meaning of a line would depend on today's members, and on an empty Tag it would write the Tag. |
| `Wizard.hp = 10` routed only for names the Tag declares for its Agents | Possible: open question 2. Its cost: `Wizard.hp = 10` writes the members while `Wizard.level = 3`, a host attribute, writes the Tag. |
| `Wizard.hp[:] = 10`, the slice assignment of lists and arrays | Rejected. A Projection does to each value what is written on it, so `Wizard.spells[:] = []` would mean `wizard.spells[:] = []` for each Wizard: clearing each list in place. And `Wizard.hp[:]` already reads a fan-out (STEP-SPEC-23, rule 4.2). |
| An eager `Enemy.Take_Damage(5)` | Rejected: the same spelling would be a question inside a Filter and a command on its own line. |
| `Enemy.Take_Damage(5)` eager only when it stands alone as a statement | Rejected: the kit could guess it from the result being dropped, but that is magic, and it would run at an unpredictable moment, when the result is collected. |
| Running a called Projection by walking it, `list(Enemy.Take_Damage(5))` | It runs, but it reads as a question. Not taught. |
| A kit function or command object, `Each(Enemy).Take_Damage(5)` | Set aside for now: a function call, and the loop already says it. Open question 1. |
| Collected failures for a write | Rejected in favour of all or nothing: a write can be undone, so it should be. |
| A promise check, or a warning, after a write | Rejected: one write checks none, so many writes check none (rule 3.4). |
| Copying the value for each member | Rejected: copying is magic, and not every value can be copied. Open question 3. |
| A write that creates names | Rejected: a typo would add a name to every member, silently. |
| A write through a Link that falls back to the Contact, as a read does | Rejected: it would change Contacts in a line that reads as a change to Pairs. |

## Open questions for the Director

1. **No spelling for broadcasting an Action (section 6).** You liked the
   idea of broadcasting an Action. This STEP recommends against a new
   spelling for it, and keeps the `for` statement. Two related choices:
   - Should TOP still give "run this Action on every member, then report
     every failure once" a spelling of its own? The language has none, so
     it would be a function or an object, such as
     `Each(Enemy).Take_Damage(5)`.
   - An Operation of the Tag (`Enemy.Volley(5)`) runs now, while
     `Enemy.Take_Damage(5)` only asks, and the two look alike (rule
     6.3). Is a naming convention in the Guide enough?

   The STEP recommends the loop, with `ExceptionGroup` in the Guide, and
   the naming convention.
2. **`Enemy.hp = 10` itself (section 4).** You wrote the example as
   `Wizard.hp = 10`. This STEP refuses it, and teaches `Wizard[:].hp =
   10`. The alternative routes the assignment to the members when the Tag
   declares `hp` for its Agents. It is shorter for the common case. But
   `Wizard.level = 3`, where `level` comes from the host, would still
   write the Tag, so two lines that look alike would do different things.
   The STEP recommends the refusal.
3. **One shared value (rule 1.4).** `Wizard[:].spells = []` gives every
   Wizard the same list. The alternatives:
   - refuse a value that cannot be hashed, a sign that it can change,
     with a message showing the `for` loop;
   - share it, as the language's `a = b = []` does, and warn in the
     Guide.

   Not every object that can change refuses a hash, so the first is a
   guess. The STEP recommends sharing, said plainly.
4. **The sound members as a root (rule 1.2).** Writing only the sound
   members is spelt `(Enemy[:] & Enemy).hp = 10`. STEP-SPEC-23 set aside
   a short spelling for the sound population, `+Enemy`. Does the write
   bring that question back? On a Link it matters more: the sound Pairs
   have no root at all (rule 5.1). The STEP recommends the long spelling
   for now, and the loop on a Link: both say what they mean.

## Acceptance requirements

- **First, on its own:** assigning a condition's name on an Agent, or a
  pinned Tag's own condition name on that Tag, is refused, as §2.5
  requires (finding 5).
- `tests/test_topkit.py`: a `WriteThroughTests` class, covering:
  - every root: the Field, `~Tag`, a combined view, a Filter, a Pin's
    population, an empty root;
  - the snapshot: a Filter on the written name, and the repair of `~Tag`;
  - every refusal of section 2, each with nothing changed: a name a
    member does not hold, a name only a host `__getattr__` answers, an
    Action, a published Operation, a host method, an Operation on a Tag
    member, a published Report, a condition, a view by name, a held
    Link, a host property without a setter, a secret from outside, an
    underscore name, a Projection as the value, a typo through a Pin;
  - the message and its `ExceptionGroup`, with every refused member;
  - the check runs no property, no host `__getattr__` and no condition;
  - a secret written from inside that member's own function;
  - undoing: a host `__setattr__` that fails on the third member, a name
    that came from the host class (deleted on undo, so the member follows
    the class again), a property with a setter (written back), an unset
    slot, a `KeyboardInterrupt`, and an undo
    that fails too;
  - no promise checked: a write that breaks one moves the member to
    `~Tag`, and raises nothing;
  - one shared value (rule 1.4);
  - Links: the Pair written through the Field, `~` and Filters; a name
    only the Contact holds refused; any combined view with a Link
    population refused; a fan-out refused;
  - `del` through a population refused, and `-=` failing before any
    write, with the loop in the message.
- `tests/test_topkit.py`: a `TagAssignmentTests` class, covering:
  - assigning and deleting each kind rule 4.2 lists, on its Tag and on a
    Shape whose Base declares it, each refused with the population
    spelling in the message, before and after the Tag's first use;
  - a Report sharing its name with a Record, a Pin's landed name, a Pin's
    un-patching, and a new program name, all still written;
  - the warning for a new public name a member holds; none for a name
    the Tag or a Base already holds, none for an underscore name, and
    no second warning when a Pin lands such a name (STEP-SPEC-23, rule
    1.3, gives one already).
- `tests/test_topkit.py`: a `WalkTests` class: a member Ripped by an
  earlier turn is skipped, through the Field, both partitions, combined
  views and Filters; an Agent that joins during the walk is not walked,
  including on the right side of `|`; a Filter by a call calls once per
  member per walk.
- STEP-SPEC-23's warning test checks the new message.
- TopKit:
  - populations set their own state without their public `__setattr__`,
    which now writes through;
  - the kernel writes on Tags (Pin landing, binding, rollback) without
    the Tag's public `__setattr__` and `__delattr__`;
  - the Tag's declarations are read before any assignment on it is
    accepted.
- The Fields Guide: a section "Commands", with the repair queue rewritten
  as `(~Wizard | ~Fighter).alive = True`, the loop and the Operation for
  Actions, the naming advice for Operations, and the `ExceptionGroup`
  pattern.
- `tests/oracle_topkit.py`: writes through random populations, checked
  against the loop on the same snapshot, and refusals checked to change
  nothing.
- `benchmarks/scenarios.py`: a write through the Field against the loop,
  and the cost of the walk's check (rule 6.5) on a plain loop.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's review.* The Director asked for this on
> 2026-10-08: "I like the Writing through a Projection and Broadcasting an
> Action ideas. Let's start a branch and step for it".
