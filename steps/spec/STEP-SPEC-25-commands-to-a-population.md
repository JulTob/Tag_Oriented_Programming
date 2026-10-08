# STEP-SPEC-25: Commands to a Population

- **STEP:** SPEC-25
- **Desk:** spec
- **Title:** Commands to a Population
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

STEP-SPEC-23 taught a Tag to answer **questions** about its members:
`Wizard.level > 3`. This STEP is about **commands**: changing every
member at once.

**A write.** Assigning a name on a population writes it on each member.
`Enemy[:].hp = 10` sets the `hp` of every Enemy. It is one act:
- every member is checked before anyone is written;
- one refusal refuses the whole write, and nothing changes;
- a failure halfway undoes what was written.

**The Tag keeps its own names.** `Enemy.hp = 10` keeps the meaning Python
gives it: an attribute of the Tag itself. When `hp` is a name the Tag
gives its Agents, that assignment is a mistake, so it is refused, and the
message shows the spelling above.

**An Action.** A command that runs an Action on each member stays a
`for` statement, or an Operation of the Tag that walks its members.
`Enemy.Take_Damage(5)` stays a question, as STEP-SPEC-23 made it. It is
lazy, and it warns when nobody walks it.

```python
Enemy[:].hp = 10                          # every Enemy, sound or defective
(~Enemy).hp = 10                          # repair the defective ones
(Enemy.hp < 5).hp = 5                     # a Filter as the root: the weak ones
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

One rule shapes this whole STEP: **a command must never look like a
question.** If the two look alike, a reader cannot tell whether a line
changes the system or only asks about it. A Filter that runs a command at
every walk would change the system each time someone counts it.

Python already marks commands. A question is an **expression**: it has a
value. A command is a **statement**: assignment, `del`, `for`. This STEP
keeps every command a statement.

### What happens today

Checked on TopKit 0.2.0a4 with the change of pull request #26, on
2026-10-08. `Enemy` has a Record `hp`, an Action `Take_Damage`, and the
promise `Alive` (`hp > 0`).

| # | Written | What happens | Why it matters |
| --- | --- | --- | --- |
| 1 | `Enemy[:].hp = 10` | Stored on the Field object, which is the same object every time. `Enemy[:].hp` then reads 10. No Enemy changed. | Silent. It looks like it worked. STEP-SPEC-23 already requires this to be refused. |
| 2 | `Enemy.hp = 10` | Stored on the Tag. `Enemy.hp` reads 10. No Enemy changed, and a new Enemy still gets 20 from the builder. | Silent. Under STEP-SPEC-23 it is worse: the Projection `Enemy.hp` becomes the number 10, so `Enemy.hp > 3` is `True`, not a Filter. |
| 3 | `for e in Enemy: e.Take_Damage(5)`, and one member raises | The loop stops there. The members before it took damage; the members after it did not. | Loud, but half done, and the failure does not name the member. |
| 4 | the same loop, and one member's Action Rips a later member | The Ripped member still gets the command when its turn comes. | A walk commands an Agent that has already left. |
| 5 | `ari.Alive = False` (`Alive` is a condition) | Stored. `ari.Alive` reads `False` while `bool(ari)` is `True`. | A defect against §2.5, which says a condition read by name is "never stored". |
| 6 | `ari.Take_Damage = 5` | Stored. The Action is gone from Ari, with no warning. | A write that replaces behaviour. |

Findings 1 and 2 are the trap of this STEP. A program that tries to write
through a Tag today is told nothing. Findings 3 and 4 are why a plain loop
is not enough for writes. Finding 5 is a defect to fix on its own, before
this STEP is built (Acceptance requirements).

### Why not just a loop

The loop is the baseline, and it stays valid:

```python
for enemy in Enemy[:]:
    enemy.hp = 10
```

For a write, a single act can promise more than the loop can:
- **all or nothing.** The kit can check every member first, and can undo
  an attribute it wrote. A loop that fails halfway leaves half the
  population changed (finding 3);
- **a fixed set of members.** Writing `hp` while walking `Enemy.hp < 5`
  changes the Filter during the walk. A single act walks a snapshot;
- **one expression for the members.** The population is written once, in
  the algebra: `(~Wizard | ~Fighter).alive = True`.

For an Action, none of these hold. An Action can do anything, so the kit
cannot undo it. That difference is why the two halves of this STEP end in
different places (section 6).

## Specification

The changes to the Specification:
- a new section, **§2.10 Commands**, in Ring 2, after STEP-SPEC-23's §2.9
  Filters;
- one row in §0.8, and a sentence there: assigning a name the Tag gives
  its Agents is refused on the Tag;
- an amendment to §2.5: a walk looks at each member again when its turn
  comes (rule 6.5).

It amends two rules of STEP-SPEC-23:
- rule 1.4, "a population refuses assignment": a population still has no
  names of its own, but a public name assigned on it is its members' name;
- rule 3.3, the warning for a call never walked: its message names the
  loop.

In this STEP, § cites the Specification only. This STEP's own parts are
cited as "section N" or "rule N.M".

### 1. Writing through a population

1. **Assigning a public name on a population writes it on each member.**
   `root.name = value` does what `member.name = value` does, for each
   member of the root, as one act (sections 2 and 3). The root is any
   population:
   - the whole Field, `Enemy[:]`;
   - the defective population, `~Enemy`, written `(~Enemy).hp` because
     the language reads `~Enemy.hp` as `~(Enemy.hp)`;
   - a combined view, `(Wizard | Fighter)`;
   - a Filter, `(Enemy.hp < 5)` (STEP-SPEC-23, section 2).

   This mirrors reading (STEP-SPEC-23, rule 1.2). `Enemy[:].hp` reads
   each member's `hp`; `Enemy[:].hp = 10` writes it.
2. **A Tag is never the root of a write.** On a Tag, assignment keeps the
   language's meaning (section 4). The sound members are written through
   a population that says so: `(Enemy[:] & Enemy).hp = 10`.
3. **A command names its members.** There is no default population for a
   write. Which members a command is for is the domain's choice:
   - "every Enemy is healed" is `Enemy[:]`;
   - "repair the broken ones" is `~Enemy`;
   - "only those still fit to fight" is `Enemy[:] & Enemy`.

   A default would decide silently who is left out.
4. **One value, the same object, for every member.** The value is
   evaluated once, and every member receives that one object. Nothing is
   copied, as in the language's own `a = b = []`. So
   `Wizard[:].spells = []` gives every Wizard **one shared list**. For a
   fresh value per member, write the loop (open question 3).
5. **A Projection is never a value.** `Enemy[:].hp = Enemy[:].max_hp`
   would give every member the Projection object itself. It is refused
   with a `TypeError`, before anything changes. Writing a different value
   to each member is not in this STEP (section 7).
6. **On a Pin**, each member is a Tag. A write through a Pin's population
   writes that Tag's own attribute, as on one Tag (section 4).
   `Rare[:].rarity = "common"` writes the Report each pinned Tag holds.
7. **An empty root** is written with nothing changed, and no failure.

### 2. The door: what may be written

Before anything is written, every member of the snapshot (rule 3.1) is
checked. A member passes when `member.name = value` is a write that this
STEP allows, from where the act runs.

1. **Only a name each member already answers.** A write through a
   population never creates an attribute. A member that does not answer
   the name refuses the write. So a misspelt name, `Enemy[:].hp_ = 10`,
   is loud, as it is for a read (STEP-SPEC-23, rule 1.7). To give a
   population a new attribute, write the loop: creating a name is an
   explicit act.

   A member answers a name when its current access (§1.7) finds it:
   - its own attributes;
   - its Records;
   - its host class's attributes.
2. **Data only, never behaviour.** A write replaces a value. It never
   replaces what an Agent does. Refused:
   - a name that holds an Action, including a published Operation and a
     teardown (§1.2, §1.5, §3.1);
   - a host method.

   A Record whose value happens to be callable is data, and may be
   written. Behaviour changes through a Tag.
3. **Read-only names stay read-only.** Refused, as each is on one Agent:
   - a published Report (§1.5);
   - a condition read by name (§2.5);
   - a held Link (STEP-SPEC-22, rule 4.3);
   - a host property without a setter.
4. **Secrets stay behind the door** (§1.5). A secret Record of a member
   is written only from inside that member's own composition, as
   `member.name = value` would be. A write-through never opens a member's
   door.
5. **Names that begin with an underscore** are never written through
   (STEP-SPEC-23, rule 1.4). Assigning one on a population is refused.
6. **Rogue and defective members are written like any other.** Writing a
   Record is how a defective member is repaired: `(~Enemy).hp = 10`. A
   Rogue Agent keeps its Records (§0.7), and they can be written. A
   published Report is refused by rule 2.3 for every member, Rogue or
   not, so a write never raises a Rogue Access Failure.
7. **One refusal refuses the whole write.** It is a Composition Failure,
   and nothing has changed. The message names every refused member, the
   name, and the reason: the failure that member alone would give.

### 3. Order, snapshot and failure

1. **A snapshot.** The root is walked once, at the start, before the door.
   The members found then are the members written, in the root's order
   (the order `for` walks it). A write that changes the root during the
   act changes nothing about who is written:
   - `(Enemy.hp < 5).hp = 5` writes every Enemy that was weak at the
     start, though after the first write that Enemy is no longer weak;
   - `(~Enemy).hp = 10` writes every defective Enemy, though each one
     leaves `~Enemy` as it is repaired.
2. **All or nothing.** The door (section 2) checks every member before
   the first write. Then the writes run, in order.
3. **A failure after the door undoes the act.** A host's own
   `__setattr__` or setter can still fail. Then:
   - the writes already made are undone, newest first: each member gets
     back the value it held, or loses the attribute if a host setter had
     created it;
   - the failure is raised as a Composition Failure that names the member,
     with the host's failure as its cause.

   This is the call boundary of §0.6: nothing partial is published. An
   interruption, such as `KeyboardInterrupt`, also undoes the act, and is
   then raised as it was.

   Undoing writes the old value back, so it runs a host setter again. A
   setter's own side effect cannot be undone (Ring 4, raw side effects).
   If undoing fails too, that failure is attached to the one raised, and
   it names the member left changed.
4. **No promise is checked.** A write through a population is play, not
   a tagging boundary. Conditions never run during play (§2.4), and one
   write does not check promises, so a write to many members does not
   either.

   A member whose promise breaks becomes defective, and moves to `~Enemy`.
   A member whose promise is repaired moves back. Truth reads it at once
   (§2.5), and published members refuse a defective member by name (§1.5).
   Nothing is silent: the population shows it the next time anyone looks.
5. **One thread** (Ring 4). The act is not guarded against another thread
   writing the same members.

### 4. Assignment on a Tag

1. **On a Tag, assignment keeps the language's meaning.** `Enemy.name =
   value` sets an attribute of the Tag itself, as today (§0.8). A Report
   is written this way: `Secret_Agent.active += 1` (§1.4).
2. **Refused: a name the Tag gives its Agents.** Assigning, or deleting
   with `del`, on a Tag, a name that the Tag or a Base in its Form
   declares in Agent scope is a Composition Failure, and nothing changes.
   Agent scope covers:
   - Records and Actions;
   - conditions and teardowns;
   - Links (STEP-SPEC-22).

   The message shows the spelling that was probably meant:
   "hp is a Record of Enemy's Agents. To write it on each member, name
   the population: Enemy[:].hp = 10."

   This is the refusal §1.9 already makes for a Pin, for the same reason:
   on a class the two scopes share one dictionary. Today the write is
   stored silently (finding 2). Under STEP-SPEC-23 it would also turn the
   Projection `Enemy.hp` into the value.
3. **A new name that the members answer warns.** Assigning on a Tag a
   name it does not hold yet, which its sound members answer, raises a
   warning. The warning names the Tag, the name, and the population
   spelling. A host attribute, such as `level`, is not declared by the
   Tag, so rule 4.2 cannot see it. Without the warning, `Wizard.level = 3`
   would silently replace the Projection `Wizard.level` for good
   (STEP-SPEC-23, rule 1.3).

   This is the warning STEP-SPEC-23, rule 1.3, gives when a Pin lands
   such a name. The members are asked only when the name is new on the
   Tag, so writing a Report that already exists costs nothing more.

### 5. Through a Link

1. **A Link root writes the Pair.** STEP-SPEC-23, rule 1.5, reads a
   member reached through a Link through that Link. A write does the same:
   `charlie.Knows[:].since = 2011` writes `charlie.Knows[contact].since`
   for each Contact (STEP-SPEC-22, rule 7.2). This holds on:
   - the whole Field of a Link, `charlie.Knows[:]`;
   - its defective population, `~charlie.Knows`;
   - a Filter rooted on either, `(charlie.Knows.since < 2000)`.
2. **A write through a Link never reaches the Contact.** A name the Pair
   does not answer is refused at the door, even when the Contact answers
   it. A read through a Link may fall back to the Contact, because a read
   is a question. A write changes the Contact, and "Breaking a barrier
   should be explicit." To write the Contacts, write the loop:

   ```python
   for contact in charlie.Knows:
       contact.mood = "cheerful"                 # an explicit write on each Contact
   ```
3. **On the Link itself**, `charlie.Knows.since = 2011` is refused by
   rule 4.2: `since` is a Record the Link gives its Pairs. The message
   shows `charlie.Knows[:].since = 2011`.
4. **A combined view sees no Link** (STEP-SPEC-23, rule 1.5). So
   `(charlie.Knows & bob.Knows).mood = "cheerful"` writes each Contact's
   own `mood`, as `contact.mood = "cheerful"` would. The program wrote
   the combined view, so that is the explicit act.
5. **A fan-out is a Projection, not a population** (STEP-SPEC-23, rule
   1.8). `Social.Knows[:].since = 2011` is refused. Write the loop over
   the Agents and their Links.
6. **A Pair's Action** is broadcast like any Action (section 6):

   ```python
   for contact in charlie.Knows:
       charlie.Knows[contact].Greet()
   ```

### 6. Broadcasting an Action

1. **A called Projection stays a question.** `Enemy.Take_Damage(5)` is
   lazy and runs at walk time (STEP-SPEC-23, rule 3.1). This STEP adds no
   eager form of it. One spelling with two meanings, a question in a
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
3. **A command of the Agency is an Operation.** When a command belongs to
   the domain, the Tag can own it, in the program's own words. An
   Operation receives the Tag (§1.4), and walks its members:

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

   `Enemy.Volley(5)` runs at once, because a Tag-scope name reads the Tag
   and always wins (STEP-SPEC-23, rule 1.1). Its name must differ from
   the Action's: on a class the two scopes share one dictionary (§1.9).
4. **The warning names the loop.** STEP-SPEC-23, rule 3.3, warns when a
   called Projection is collected without being walked. Its message now
   names the spelling that was probably meant:
   "Enemy.Take_Damage(5) was never walked. A call on a Tag is a question,
   asked at every walk. To command each member, write: for enemy in
   Enemy: enemy.Take_Damage(5)."
5. **A walk looks at each member again when its turn comes.** This amends
   §2.5, for every walk of a population, not only for commands:
   - the walk takes its members from a snapshot made when it starts, as
     TopKit's Field already does;
   - when a member's turn comes, it is walked only if it still belongs
     to the population. A member that a previous turn Ripped, or made
     defective in a sound walk, is skipped (finding 4);
   - an Agent that joins during the walk is not walked.

   This is how STEP-SPEC-24, rule 1.5, walks a Field Rip. It costs one
   membership check per member.
6. **The first failure stops the loop**, as the language stops any loop.
   It is loud: the failure is raised where it happened. The members
   before it were commanded, and their Actions are not undone, because
   the kit cannot undo an Action. That is the same rule as an Imprint
   that fails after commit: the product left the line (§0.6). A program
   that wants every member commanded, and the failures collected, writes
   it with the language's own `ExceptionGroup`:

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

   Whether TOP should give this its own spelling is open question 2.

### 7. Not in this STEP

- **A different value for each member.** `Enemy[:].hp -= 5` reads
  `Enemy[:].hp`, a Projection, and a Projection has no `-`. So it fails
  with a `TypeError` before anything is written. Arithmetic on
  Projections, and a Projection as the value of a write, are their own
  topic (rule 1.5).
- **Deleting through a population.** `del Enemy[:].hp` is refused. It
  reads too much like `del Enemy[:]`, which Rips the whole Field
  (STEP-SPEC-24). Write the loop.
- **Writing through a fan-out** (rule 5.5).
- **Applying a Tag to a population**, which STEP-SPEC-23, rule 1.9,
  refuses.
- **A kit spelling for a broadcast with collected failures** (open
  question 2).

## Rationale

**Commands are statements.** The language already separates a question
from a command: an expression has a value, a statement does something.
`Enemy[:].hp = 10` is an assignment. It cannot sit inside a Filter, a
`len` or an `if`, so it can never run by accident while someone counts.
`Enemy.Take_Damage(5)` is an expression, and STEP-SPEC-23 made it a
question. Giving it a second meaning as a command would make the line
`Enemy.Take_Damage(5)` mean "do nothing and warn" in one place and "hurt
everyone" in another. So the command stays a `for` statement.

**The population, not the Tag, for writes.** §0.8 promises the program
the Tag's dotted namespace, and Python gives `Enemy.hp = 10` a meaning
already. Routing that assignment to the members would make its meaning
depend on where `hp` comes from:
- `hp` declared by the Tag: written on every member;
- `level` from the host class: stored on the Tag, silently.

Two lines that look the same would do different things. A population has
no names of its own (STEP-SPEC-23, rule 1.4), so on a population an
assignment has exactly one meaning: the members'. And it is the mirror of
the read, `Enemy[:].hp`.

**No default population for commands.** A question defaults to the sound
members, because that is what a Tag means in a loop (STEP-SPEC-23). A
command has no such default, because the cost of a wrong guess is
different:
- writing only the sound members leaves the defective ones stale. When
  they are repaired, they come back with the old value, and nobody was
  told;
- writing everyone may write members the program meant to leave alone.

Either guess is silent about who was left out. Naming the root costs a
few characters and says it.

**All or nothing, for writes.** A write through a population is one act,
so it gets one outcome. The kit can check every member before it writes,
and it can put an attribute back. That gives the promise §0.6 makes at
the gate: a failed act publishes nothing. The loop cannot promise it.

**Collected failures and undoing, for Actions: no.** An Action can do
anything: print, send, spend, Rip. The kit cannot put that back, so it
cannot make a broadcast all or nothing. What remains is the choice
between stopping at the first failure and running everyone and
collecting. The language's loop stops, and `ExceptionGroup` collects.
Both can be written plainly, in the program's own words. A kit form would
need a name, and §0.8 keeps names for acts the language has no spelling
for. Here the language has one: `for`.

**Never create, never replace behaviour.** STEP-SPEC-23 made a misspelt
read loud: "A filter that quietly drops members because of a typo ... is
the bug this STEP must never make easy." The write's version of that bug
is `Enemy[:].hp_ = 10`, which would create `hp_` on every Enemy and leave
`hp` alone. Refusing names a member does not answer makes it loud.
Refusing Actions keeps a write a change of value (*estar*), never a change
of what an Agent is (*ser*), which belongs to Tags.

**No promise check after a write.** A write through a population is many
plain writes, done safely. A single `enemy.hp = -1` checks no promise
(§2.4), so ten of them should not either. If they did, the same change
would raise when written once with a population and pass when written
ten times in a loop. The defective population shows the result at once.

**Through a Link, the Pair only.** The Director: "Breaking a barrier
should be explicit." A read that falls back to a Contact's own attribute
only looks. A write changes the Contact. Done through the Link's spelling,
it would let `charlie.Knows[:].mood = ...` change people who never chose
Charlie, in a line that reads as if it changed Charlie's Pairs. The loop
says plainly that the program is writing on the Contacts.

**The language's own structures.** Every spelling here is the
language's: assignment, `for`, `[:]`, the operators. The Director: "I
don't like 'Function calls' in TOP." This STEP adds none.

## Backwards compatibility

What changes:
1. **Assignment on a population** was silently stored on the population
   object (finding 1). STEP-SPEC-23 refuses it. With this STEP it writes
   the members.
2. **Assigning or deleting, on a Tag, a name the Tag gives its Agents**
   was silently stored (finding 2). Now it is a Composition Failure.
   Code that did this on purpose kept a value on the Tag under an Agent's
   name. It should rename the value, or make it a Report.
3. **Assigning a new name on a Tag** that its sound members answer now
   warns.
4. **Every walk of a population** skips a member that left during the
   walk (rule 6.5). Before, a Field walk still reached it.
5. **STEP-SPEC-23's warning message** for a call never walked now names
   the loop.

What does not change: assignment on a Tag of its own names (Reports,
what a Pin lands, any other name the program puts there), and every
write on one Agent.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| The loop alone, for writes | Valid, and it stays. Set aside as the only spelling: it cannot be all or nothing, and a Filter root changes while it walks. |
| `Wizard.hp = 10` routed by the receiver rule, for every name the members answer | Rejected: the meaning of a line would depend on today's members, and on an empty Tag it would create a Tag attribute. |
| `Wizard.hp = 10` routed only for names the Tag declares in Agent scope | Possible, and open question 1. Its cost: `Wizard.hp = 10` writes the members while `Wizard.level = 3`, a host attribute, writes the Tag. |
| `Wizard.hp[:] = 10`, the slice assignment of lists and arrays | Rejected. A Projection does to each value what is written on it, so `Wizard.spells[:] = []` would mean `wizard.spells[:] = []` for each Wizard: clearing each list in place. Its read, `Wizard.hp[:]`, is already a fan-out (STEP-SPEC-23, rule 4.2). |
| An eager `Enemy.Take_Damage(5)` | Rejected: the same spelling would be a question inside a Filter and a command on its own line. |
| Running a called Projection by walking it, `list(Enemy.Take_Damage(5))` | It runs, but it reads as a question, and STEP-SPEC-23's Guide says to filter by questions, never by commands. Not taught. |
| A kit function or command object, `Each(Enemy).Take_Damage(5)` | Set aside for now: a function call, and the loop already says it. Open question 2. |
| Collected failures for a write | Rejected in favour of all or nothing: a write can be undone, so it should be. |
| A Promise check after a write | Rejected: one write checks none, so many writes check none (rule 3.4). |
| Copying the value for each member | Rejected: copying is magic, and not every value can be copied. Open question 3. |
| A write that creates names | Rejected: a typo would add a name to every member, silently. |
| A write through a Link that falls back to the Contact, as a read does | Rejected: it would change Contacts behind a line that reads as a change to Pairs. |

## Open questions for the Director

1. **`Enemy.hp = 10` itself (section 4).** You wrote the example as
   `Wizard.hp = 10`. This STEP refuses it, and teaches `Wizard[:].hp =
   10`. The alternative routes the assignment to the members when the Tag
   declares `hp` for its Agents, and keeps the Tag's own meaning
   otherwise. It is shorter for the common case. But `Wizard.level = 3`,
   where `level` comes from the host, would still write the Tag, so two
   lines that look alike would do different things. The STEP recommends
   the refusal.
2. **A broadcast with collected failures (rule 6.6).** Should TOP give
   "run this Action on every member, then report every failure once" its
   own spelling? The language has none, so it would be a function or an
   object, such as `Each(Enemy).Take_Damage(5)`. The STEP recommends the
   loop, with `ExceptionGroup` in the Guide.
3. **One shared value (rule 1.4).** `Wizard[:].spells = []` gives every
   Wizard the same list. The alternatives:
   - refuse a value that cannot be hashed, a sign that it can change,
     with a message showing the loop;
   - share it, as the language's `a = b = []` does, and warn in the
     Guide.

   Not every object that can change refuses a hash, so the first is a
   guess. The STEP recommends sharing, said plainly.
4. **The sound population as a root (rule 1.2).** Writing only the sound
   members is spelt `(Enemy[:] & Enemy).hp = 10`. STEP-SPEC-23 set aside
   a short spelling for the sound population, `+Enemy`. Is the long one
   explicit enough, or does the write bring that question back? The STEP
   recommends the long one, since commands should name their members
   (rule 1.3).

## Acceptance requirements

- **First, on its own:** assigning a condition's name on an Agent is
  refused, as §2.5 requires (finding 5).
- `tests/test_topkit.py`: a `WriteThroughTests` class, covering:
  - every root: the Field, `~Tag`, a combined view, a Filter, a Pin's
    population, an empty root;
  - the snapshot: a Filter on the written name, and the repair of `~Tag`;
  - every refusal at the door, each with nothing changed: a name a member
    does not answer, an Action, a published Operation, a host method, a
    published Report, a condition, a held Link, a host property without
    a setter, a secret from outside, an underscore name, a Projection as
    the value; and a message that names every refused member;
  - a secret written from inside that member's own composition;
  - undoing: a host `__setattr__` that fails on the third member, an
    attribute a host setter created, a `KeyboardInterrupt`, and an undo
    that fails too;
  - no promise checked: a write that breaks one moves the member to
    `~Tag`, and raises nothing;
  - one shared value (rule 1.4);
  - Links: a Pair written through the Link, the Field and a Filter; a
    name only the Contact answers refused; a combined view writing the
    Contacts; a fan-out refused;
  - `del` through a population refused.
- `tests/test_topkit.py`: a `TagAssignmentTests` class, covering:
  - assigning and deleting a Record, an Action, a condition, a teardown
    and a Link on its Tag, and on a Shape whose Base declares it, each
    refused with the population spelling in the message;
  - a Report, a Pin's landed name and a new program name still written;
  - the warning for a new name the sound members answer, and none for a
    name already on the Tag.
- `tests/test_topkit.py`: a `WalkTests` class: a member Ripped by an
  earlier turn is skipped, in the Field, the partitions, combined views
  and Filters, and an Agent that joins during the walk is not walked.
- STEP-SPEC-23's warning test checks the new message.
- TopKit: populations set their own state without their public
  `__setattr__`, which now writes through.
- The Fields Guide: a section "Commands", with the repair queue rewritten
  as `(~Wizard | ~Fighter).alive = True`, the loop and the Operation for
  Actions, and the `ExceptionGroup` pattern.
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
