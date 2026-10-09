# STEP-SPEC-23: Field Filters

- **STEP:** SPEC-23
- **Desk:** spec
- **Title:** Field Filters
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08. First drafted as STEP-SPEC-20; renumbered
  because 20 is claimed by another open STEP.
- **Revised:** 2026-10-08, after the Director's review: the everyday
  filter reads the Tag itself, `Wizard.level > 3`.

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

> **Superseded in part on 2026-10-09.** The Director decided:
> "Wizard.level is a report". Wherever this STEP writes a bare Tag
> before a dot (`Wizard.level`, `Wizard.Can_Cast(...)`, `Social.Knows`),
> that reading gives way. The root for the sound members is
> STEP-SPEC-29's question. The rest stands, read from a population such
> as `Wizard[:].level`.

A Tag can be asked about its members' attributes.

**A Projection.** `Wizard.level` reads the `level` of each sound Wizard,
the ones `for wizard in Wizard` walks, at the moment it is asked. The
population it reads is its **root**. Any population can be the root:
`Wizard[:].level` reads everyone, defective members included.

**A Filter.** Comparing a Projection gives a Filter. `Wizard.level > 3` is
the population of sound Wizards whose level is above 3. Like every
combined view it is alive, and it combines with `|`, `&` and `-`.

**Chains.** A chain fans out through Fields. `Social.Knows[:] == ruth` is
every sound Agent in Social who knows Ruth.

**Calls.** An Action's result filters too, so a Filter follows a system
that is changing: `Wizard.Can_Cast("Light") == True`.

```python
veterans = Wizard.level > 3                       # a Filter: alive, not a list
for wizard in veterans & Sworn:                   # the algebra of Fields
    print(wizard.name)

ari.level = 5
assert ari in veterans                            # it follows the system

old_friends = charlie.Knows.since < 2000          # on a Link, the Pair's Records (STEP-SPEC-22)
who_knows_ruth = Social.Knows[:] == ruth          # some Contact of theirs is Ruth
ready = Wizard.Can_Cast("Light") == True          # by an Action's result, at every walk
everyone_above = Wizard[:].level > 3              # the whole Field, defective members too
```

## Motivation

### The logic TOP already speaks

The Fields already form an algebra. Each Tag is a class of things, and
`|`, `&` and `-` combine the classes (STEP-SPEC-13, the Fields Guide).
This is the **algebra of classes** that George Boole wrote down in 1854,
and that Lewis Carroll turned into a board game:
- *The Game of Logic* (1886);
- *Symbolic Logic* (1896).

The names of this logic:
- **term logic**, or **syllogistic**, its older names, from Aristotle;
- **monadic predicate logic**, its modern name: every statement says one
  thing about one thing.

Carroll's game starts from a **Universe of Things**. **Attributes** divide
that universe into **Classes**: *the cakes that are new*, *the cakes that
are nice*, *the cakes that are new and not nice*. A syllogism then reasons
from one class to another:
- "No new cakes are nice."
- "Some cakes are new."
- Therefore, "some cakes are not nice."

TOP has the Things (Agents), the Classes (Tags) and the algebra. It lacks
the other half of the game: **dividing a class by an attribute's value**,
*the Wizards whose level is above 3*. Today that is a comprehension:

```python
veterans = [w for w in Wizard if w.level > 3]     # a list: frozen, and outside the algebra
```

The result is a list, frozen at the moment it was made. It cannot be
combined with `&`, cannot be kept as a view, and does not follow the
system when a level changes. The Fields Guide says to keep views, not
lists. `Wizard.level > 3` is that same question kept as a view.

With Links (STEP-SPEC-22), TOP also gets **two-place statements**:
*Charlie knows Ruth*. That is the step from Carroll's monadic logic to
the **logic of relations** (De Morgan; Peirce's "logic of relatives"). A
Filter is how a program asks it questions: `Social.Knows[:] == ruth`.

### Why not functions

A filter function, `Where(Wizard, lambda w: w.level > 3)`, would work.
TOP keeps functions for queries that need a name (§0.8: `Form`, `Tags`,
`Outline`), and spells its acts in the language's own syntax: `in`,
`for`, `[:]`, `del`, the operators. A filter needs no name. *Greater
than* is a comparison, and the language already has the operator for it.

## Specification

The changes to the Specification:
- a new section, **§2.9 Filters**, in Ring 2, beside the population
  algebra of §2.5;
- one row in §0.8;
- an amendment to §0.8, which "leaves the Tag's dotted namespace,
  `Wizard.something`, to the program" (the Guide says it as "Nothing
  TOP-level lives at `Wizard.something`"). The Tag's own names stay its
  own and always win, and so do a pinned Tag's Pin-bound views and Pin
  conditions by name (§1.9, §2.5). An Agent's name read on the Tag,
  whether the Tag declares it for its Agents or does not hold it at all,
  reads across the Tag's sound Agents (rule 1.1).

In this STEP, § cites the Specification only. This STEP's own parts are
cited as "section N" or "rule N.M".

### 1. Projection

> **Superseded in part on 2026-10-09.** The Director decided: "Wizard.level
> is a report". The dot on a Tag reads only the Tag, so rule 1.1's
> projection of an Agent's name on the Tag, and rule 1.3, give way.
> Projections start from a population; the spelling of the root for the
> sound members is set in STEP-SPEC-29 (The Population Algebra). The
> rest of this section stands, read from a population root: rule 1.2 and
> rules 1.4 to 1.9.

1. **A name read on a Tag lives in the scope that receives it** (§1.1).
   - **An Agent's name projects.** The Tag stores what it declares for its
     Agents (§1.1: "the Tag stores it once"), but those names are its
     Agents': an Action (a teardown is one, §3.1), a Record, a condition
     read by name (§2.5), or a Link (STEP-SPEC-22), declared in its own
     body or a Base's. So is any public name the Tag does not hold.
     Reading an Agent's name on the Tag gives a **Projection** over the
     Tag's sound population, the Agents `for wizard in Wizard` walks
     (§2.5), in their order. That population is the Projection's
     **root**.
   - **Every other name reads the Tag.** That covers:
     - a Report and an Operation, its own or a Base's;
     - what a Pin lands;
     - the Pin-bound view by name, `Wizard.Rare` (§1.9);
     - a Pin's condition read by name, `Wizard.Has_Members` (§2.5);
     - a protocol such as an Imprint;
     - any value the program sets on the Tag.

     These read the Tag's own value, as today (§0.8). They always win.

   For each member of the root, the Projection reads the value that
   `member.name` reads at that moment. This is the current access of
   §1.7: Records, Actions, published members, conditions read by name
   (§2.5), and host attributes. So `Wizard.level` reads each sound
   Wizard's `level`, and `Wizard.spells` each sound Wizard's `spells`.
2. **Any population projects the same way.**
   - The whole Field: `Wizard[:].level`, the defective members included.
   - The defective population, in brackets: `(~Wizard).level`. The
     language reads `~Wizard.level` as `~(Wizard.level)`.
   - A combined view: `(Wizard | Fighter).level`.
   - A Filter: `(Wizard.level > 3).spells`.
3. **A name both scopes hold reads the Tag.** §1.1 lets a Report `colour`
   and the Agents' Record `colour` live side by side. `Wizard.colour` is
   then the Report. To project the Agents' `colour`, read it through a
   population: `Wizard[:].colour` for every member, or
   `(Wizard[:] & Wizard).colour` for the sound ones. A Tag in an operator
   seat is its sound population (§2.5). A Projection takes no population
   operator (rule 1.8), so `& Wizard` goes inside the brackets.

   A Pin can land a Tag-scope name, its own view by name among them, after
   a Projection was written. If
   the pinned Tag's members already answer that name, `Wizard.name`
   changes meaning. So the kit warns at pinning, and the warning names
   the Pin, the Tag and the name. A Pin is already refused a name the
   Tag declares in Agent scope (§1.9).
4. **Names that begin with an underscore are never projected.** They
   belong to the kit and the language. A population has no public names
   of its own, and refuses assignment of any. The Field's `Add` and
   `Remove` became private in TopKit's change of pull request #26, which
   carries this STEP.
5. **Through a Link.** A Link is a Tag, so `charlie.Knows.since` projects
   over Charlie's sound Contacts. A member reached through a Link is read
   through that Link:
   - a name the Pair answers (a Record, an Action, a condition or a
     published member that the Links holding the Contact give the Pair)
     reads the Pair, `charlie.Knows[member].since` (STEP-SPEC-22,
     section 7);
   - any other name reads the Contact, `member.name` (rule 1.1).

   This holds for:
   - the Link itself, `charlie.Knows.since`;
   - its whole Field and its defective population, `charlie.Knows[:]`
     and `~charlie.Knows`;
   - a Filter rooted on any of these: a Filter always reads as its root
     does;
   - each leaf of a fan-out through Links (section 4), read through the
     Link it was walked from: `Social.Knows[:].since` reads
     `agent.Knows[leaf].since`.

   A combined view sees its members through no Link, because a member may
   have one Pair in each operand. So `(charlie.Knows & bob.Knows).since`
   reads each Contact's own `since`. To filter on a Pair there, filter one
   Link and combine: `(charlie.Knows.since < 2000) & bob.Knows`.
6. **On a Pin**, each member is a pinned Tag, and a Projection reads that
   Tag's own names. `Rare.rarity` reads `tag.rarity` for each sound pinned
   Tag (for Wizard, `Wizard.rarity`), never a name on the Tag's Agents
   (§1.9).
7. **A member with no value for the name.** A member that lacks the
   name, or holds `None` under it, has no value, as SQL's `NULL` (the
   Director, 2026-10-08: "== None is the way to check for non-defined
   gains (records, contracts, actions...) and != None so it simply
   exists").
   - `P == None` keeps the members with no value, and `P != None` the
     members with one: `Wizard.Dance != None` is every sound Wizard that
     has a `Dance`.
   - Every other comparison never matches a member with no value, and
     never raises for it. `Wizard.dance == True` keeps the Wizards whose
     `dance` is defined and `True`; `Wizard.dance == False` those whose
     `dance` is defined and `False`.
   - Walking the values skips members with no value, as SQL's `SUM`
     skips `NULL`: `sum(Wizard.level)` adds the levels there are.
   - A walk in which no member has the name at all warns
     (`RuntimeWarning`), so a misspelt name, `Wizard.levle`, is still
     loud.
   - `P == None` calls the Projection's own `__eq__`: the language
     cannot overload `is`. Style checkers flag `== None` (pycodestyle
     E711), because for a plain value `is None` is right. SQLAlchemy keeps
     the same spelling for SQL's `IS NULL`, for the same reason. The Guide
     says why TOP writes it.

   A member that has the name but refuses to answer it stops the walk,
   with the failure the refusal raises:
   - A member that has left the Tag that published the name is a Rogue
     Agent of that Tag. Reading its published Report, or calling its
     published Operation through a Projection's call (section 3), raises
     `TagRogueAccessError` (§1.5).
   - A defective member is refused a published member, and the refusal
     names the broken promise (§1.5). A Projection read on the Tag walks
     only sound members, so it never meets one. A Projection over the
     whole Field stops at the first.
   - A secret read from outside fails as it does anywhere (§1.7).

   To project a mixed population, narrow it first:
   `(Wizard & Caster).spells`.
8. **A Projection is not a population.** It is the values of one
   question, not a set of Agents.
   - It walks its values, one per root member that has one (rule 1.7),
     or one per leaf after a fan-out (section 4), so `sum(Wizard.level)`
     adds the levels. `len` counts those values.
   - It refuses `in` and `not in`, with a `TypeError` whose message says
     to compare first: `ruth in (P > 3)`.
   - It refuses assignment, `del`, `~` and the population operators. Of
     indexes it answers only `[:]` (section 4).
9. **A Projection never applies a Tag.** Applying a Tag is a command, not
   a question (section 6). The refusal is a `TypeError`, and no Agent is
   tagged:
   - **at the call**, when the name is a Link that the root's Tag grants
     (STEP-SPEC-22, rule 2.2), so every member of the root holds one. The
     root's Tag is `Social` for `Social.Knows`, `Social[:].Knows`,
     `(~Social).Knows`, and a Filter rooted on any of them. So
     `Social.Knows(ruth)` is refused at once: it is not "everyone in
     Social links Ruth";
   - **at the walk**, for any other value that turns out to be a Tag or a
     Link, such as a Record that holds a Tag. The walk stops before that
     value is called, and the message names it. A call of this kind that
     is never walked only warns (rule 3.3).

### 2. Filter

1. **Comparing a Projection gives a Filter.** The operators are `==`,
   `!=`, `<`, `<=`, `>` and `>=`. A Filter is the population of the
   root's members whose value compares true, in the root's order.

   Write the Projection on the left. Python asks the left operand first,
   so when a host's own `==` answers, the Projection is never asked.
2. **Values compare as the language compares them.** For an Agent without
   its own `__eq__`, `==` is identity, as a Field's membership is (§0.3).
   A host that defines equality is compared by its equality.
3. **A comparison must answer `True` or `False`** (§2.1). A comparison
   that answers anything else stops the walk with a Contract Failure:
   an array, a number, or `numpy.bool_`, which is not `bool`. TOP never
   coerces a truth value.
4. **A Filter is a population.** It walks its root's members, answers `in`
   and `len`, combines with `|`, `&` and `-`, and projects again. It is
   alive: it reads its root and recomputes every value at every walk, so
   it is never stale (Fields Guide, section 3).

### 3. Calls

1. **Calling a Projection calls each member's value**, with the same
   arguments, at walk time. The result is a Projection of the results:
   `Wizard.Can_Cast("Light") == True`.
2. **A Filter by a call is dynamic.** Every walk calls again, so its
   population follows the system as it changes. `len(f)` walks too. An
   Action that changes something will change it again at every walk. The
   Guide says it plainly: filter by questions, never by commands.
3. **A call that is never walked says so.** A called Projection that is
   dropped without ever being walked or compared raises a
   `RuntimeWarning` when it is collected, the kind of warning Python gives
   for a coroutine that is never awaited. So `Enemy.Take_Damage(5)` on a
   line of its own
   does nothing, and the warning says so. Broadcasting a command is not
   in this STEP (section 6).

### 4. Chains

1. **A Projection projects further**: `Wizard.familiar.name`.
2. **`[:]` on a Projection fans out.** When each value is a Tag, a Link
   or a population, `[:]` walks the members of each one. A value that is
   none of these stops the walk with a `TypeError` that names it.
3. **A comparison at the end of a chain keeps a root member when some
   leaf compares true.** This is the "some" of Aristotle and Carroll.
   `Social.Knows[:] == ruth` is every sound Agent in Social whose Link
   holds Ruth among its Contacts: "anyone who knows Ruth".
   `Social[:].Knows[:] == ruth` asks the same of the whole Field.
4. **"All" is the difference of a "some".** *Everyone whose Contacts are
   all friendly* is *Social less those with some unfriendly Contact*.
   Here `friendly` is the Contact's own attribute (rule 1.5):
   `Social - (Social.Knows[:].friendly == False)`.

   An Agent with no Contacts is in that population. Modern logic reads
   it this way, after Boole: "all" over nothing is true. Aristotle and
   Carroll read "all x are y" as also saying that some x exist.
5. **"Not" is a difference too, never `!=` over a fan-out.** Over a
   fan-out, `!=` keeps a root member when *some* leaf differs.
   `Social.Knows[:] != ruth` is everyone with some Contact who is not
   Ruth. *Those who do not know Ruth* is
   `Social - (Social.Knows[:] == ruth)`.

   Without a fan-out there is one value per member, and `!=` is the plain
   opposite of `==`.

### 5. Truth

**A Projection, a Filter, and any combination that contains a Filter
refuse `bool()`.** The refusal is a `TypeError` whose message names the
spelling to use instead: `len(f) > 0` to ask "anyone?", and
`(P > a) & (P < b)` for a range, with the Projection on the left (rule
2.1).

The reason is the language's chained comparison. Python reads `2000 < P
< 2020` as `(2000 < P) and (P < 2020)`, and `and` asks the truth of the
first Filter. If a Filter had a truth value there, the result would be
the second Filter alone, and the lower bound would be dropped in silence
whenever anyone was above it. The refusal makes that mistake loud.

`ruth in P > 3` is the same kind of chain: Python reads `(ruth in P) and
(P > 3)`. There `in` already answers a plain `True` or `False`, so no
refusal of `bool()` could see it. It fails loudly because a Projection
refuses `in` (rule 1.8), and the message names `ruth in (P > 3)`.

`any(f)` is not "anyone?" either. It asks each member's own truth, and an
Agent's truth is its contract (§2.5), so a Filter of broken Agents would
answer `False`. `len(f) > 0` asks the population.

### 6. Not in this STEP

- Writing through a Projection, such as `Wizard.hp = 10`. Until a STEP
  gives it a spelling, write the loop: `for wizard in Wizard: wizard.hp =
  10`. On a Tag, that
  assignment sets a value of the Tag itself, as Python does today: a
  Report written by hand. The Director: "if it looks like a report, then
  it is, and we just have more than one way to handle that." It then
  wins over the Projection (rule 1.1), so `Wizard.hp` stops reading the
  members. Over a declared Report it is the documented way to change the
  shared value (§1.4). Over a Record or an Action it is a category
  error, in the Director's words "probably a misconception", and today
  its result depends on timing: before the Tag's first use it erases the
  declaration, so new Wizards and its Shapes' Agents get no `hp`; after,
  every Agent still gets the Record, because the kit read the
  declaration at first use, but `Wizard.hp` now reads 10, so the Tag and
  its Agents disagree. The kit should refuse it, as it already refuses a
  Pin that replaces what a Tag's Agents do. On any other population,
  assignment is refused (rule 1.4). STEP-SPEC-25 refuses it (rule 4.2), and
  STEP-SPEC-28 names the failure, `TagCategoryError`.
- Broadcasting an Action for its effect, such as `Enemy.Take_Damage(5)`.
  It does nothing, and warns (rule 3.3).
- Applying a Tag through a Projection (rule 1.9).

These are commands, not questions, and each deserves its own STEP.

## Rationale

**The sound members, by default.** The Director: "Isn't this better
stated as just Wizard.level > 3? Do we need the full universe of wizards?
that my example requested all doesn't mean all filters need to have it."
He is right. A Tag already means its sound population in a loop, `for
wizard in Wizard`, and in an operator seat, `Wizard & Sworn`. Reading a
name on it is the third seat, and it means the same population.
`Wizard.level > 3` is then exactly the comprehension it replaces, kept
alive. The whole Field and the repair queue stay one step away, as
`Wizard[:]` and `~Wizard`.

**The receiver decides, for reads too.** §1.1 already says the receiver
decides a contribution's scope. Reading follows it: a Tag-scope name reads
the Tag, and an Agent's name reads the Agents. §0.8 promised the program
the Tag's dotted namespace. That promise holds for every Tag-scope name
the program puts there, because those names win (rule 1.1). What changes
is what an Agent's name means on the Tag. One the Tag declares for its
Agents gave TopKit's raw declaration, and one it does not hold was an
`AttributeError`.

**The language's own structures.** Comparison operators and attribute
reads on a Tag read like the domain: *the Wizards whose level is greater
than three*. The idea is the boolean mask that Python's data tools made
familiar (`df[df.level > 3]`), with populations in place of masks. That
keeps it inside TOP's algebra: a Filter is combined with `&`, kept as a
view, and walked with `for`.

**The root, and "some".** A chain fans out, but the answer is always the
population the chain started from. That is the only reading under which
`Social.Knows[:] == ruth` means what it says: *those in Social who know
Ruth*, not *Ruth*. "Some" is the quantifier a fan-out needs, and "all"
comes from `-`, as it does in Carroll's game.

**Loud, never silent.** These all fail where they happen:
- a member that cannot answer;
- a comparison that answers something other than a truth value;
- a chained comparison;
- `in` on a Projection;
- a call that is never walked;
- a Projection asked to apply a Tag;
- a Pin landing a name that changes what a Projection reads.

A filter that quietly drops members because of a typo (`Wizard.levle > 3`
coming back empty) is the bug this STEP must never make easy.

**Dynamic by design.** The Director: "The fact we could filter by action
results also means is a dynamic system. I like the idea." A Filter holds
no values. It holds the question, and asks it again at every walk.

## Backwards compatibility

What changes:
- **A public name the Tag did not answer** was an `AttributeError` on the
  Tag. Now it is a Projection, so `hasattr(Wizard, "level")` is `True`.
  Code that probed a Tag with `hasattr` must ask another way.
  `vars(Wizard)` alone is not enough: it misses a Report a Shape
  inherits, and the names a pinned Tag answers by name (§1.9, §2.5).
- **A name the Tag declares for its Agents**, a Record, an Action or a
  condition read on the Tag (`Wizard.spells`, `Wizard.Has_Book`), gave
  TopKit's raw function. That was never a documented spelling. Now it is
  a Projection.
- **Reading a public name on a population** was an `AttributeError`,
  apart from the Field's `Add` and `Remove`, which became private in pull
  request #26.
- **Comparing a population** fell back to the language's defaults:
  identity for `==`, a `TypeError` for `<`.
- **`bool()` of a Projection or a Filter** is new, and refused.

What does not change: Reports, Operations, what a Pin lands, a pinned
Tag's Pin-bound views and Pin conditions by name, and every other
Tag-scope name the program puts on a Tag read exactly as before.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Comprehensions, `[w for w in Wizard if w.level > 3]` | They stay valid Python, but give a frozen list outside the algebra. |
| A filter function, `Where(Wizard, lambda w: w.level > 3)` | A filter needs no name, so it is spelt with the language's operators (§0.8); the Director prefers language structures to function calls. |
| Projections only on populations, `Wizard[:].level`, with the Tag's dotted names left alone (the first draft) | Withdrawn after the Director's review: the everyday question is about the sound members, and the whole Field made it a two-step spelling, `(Wizard[:].level > 3) & Wizard`. |
| A spelling for the sound population, `(+Wizard).level` (the first draft's open question) | Set aside: the Tag already means its sound population, and needs no new operator or brackets. |
| Projecting only the names the Tag declares (its Records and Actions) | Set aside: `level` belongs to the host, as most attributes a program filters on do, and `Wizard.level` must work. |
| Mask indexing, `Wizard[:][Wizard[:].level > 3]` | `Tag[agent]` is already the view and `Tag[:]` the Field; it would also name the population twice. |
| A Filter with a truth value, "is anyone in it?" | Rejected: it makes chained comparisons silently wrong (section 5). |
| Members without the name skipped silently | Rejected: a misspelt name would filter everyone out with no error. |
| "All" as the meaning of a fan-out | Rejected: "some" is what `== ruth` asks, and "all" is one `-` away. |
| Eager calls, made when the Projection is called | Rejected: the Filter would stop following the system. |

## Open questions for the Director

1. **Lookup through a Link (rule 1.5).** Through a Link, a name the Pair
   answers wins over the Contact's own attribute of the same name. Is
   that the reading you want, or should a shared name be refused? The
   design panel below recommends refusing it, so the answer can never
   change silently.
2. **An explicit root for the members.** On 2026-10-08 the Director
   refused rule 1.3's spelling: "I refuse that monstrosity with redundant
   information", of `(Wizard[:] & Wizard).colour`. He found rule 1.1
   implicit: "Wizard.level makes it so the record looks like a report, an
   also doesn't individually tell you what is going on. It's a lot of
   implicit going on there. Maybe we can do a for Wizard[].level as l:".
   And he asked for a one-line write over the valid members, which
   STEP-SPEC-25 spells only as `(Enemy[:] & Enemy).hp = 10`. The three
   are one gap: no object means "the sound members" and also takes a dot.

   **Decided on 2026-10-09:** "Wizard.level is a report", so the dot on
   a Tag reads only the Tag; and the named key below is rejected:
   "Wizard[Sound] looks horrible. It takes over programmer's choices,
   not language options. Skip." The root for the sound members is now
   STEP-SPEC-29's question. What follows is the panel's first answer,
   kept for the record.

   `Wizard[]` is not Python. A design panel (three designers, one judge)
   recommended:
   - **The dot on a Tag reads only the Tag.** `Wizard.colour` is the
     Report. A name the Tag gives its Agents, `Wizard.level`, is refused
     with a hint, as an `AttributeError`, so `hasattr` answers False.
   - **`Wizard[Sound]` names the sound members**, with `Sound` imported
     from TopKit, "sound" being TOP's own word: `Wizard[Sound].level > 3`,
     `for level in Wizard[Sound].level:`, and the write
     `Wizard[Sound].hp = 10` (STEP-SPEC-25). The bare Tag keeps every
     seat it has today (`for`, `len`, `if`, the operators).
   - **Rule 1.3 goes.** `Wizard.colour` and `Wizard[Sound].colour` say
     which one is meant.

   Weighed and set aside: `Wizard[()]`, legal and closest to `Wizard[]`,
   but one shape away from a position, `Wizard[0]`; `Wizard[True]`,
   because `True` is `1` in Python and an Agent's truth is not always its
   contract; `(+Wizard).level`, because `+Wizard.level` is read
   `+(Wizard.level)`; string keys, `Wizard["level"]`; and a function,
   `Each(Wizard).level`. Adopting it rewrites rules 1.1, 1.3, 1.5 and 1.6
   and the examples. The panel's other proposals, positions
   (`Wizard[0]`), the only one (`Wizard[Only]`) and `P[True]` for a
   boolean Projection, belong to a STEP of their own.

## Acceptance requirements

- `tests/test_topkit.py`: a `FilterTests` class, covering:
  - every numbered rule;
  - the receiver rule for reads: Reports, Operations, Pin-landed names,
    a pinned Tag's Pin-bound views and Pin conditions by name, and values
    set on the Tag read the Tag; Records, Actions and conditions the Tag
    declares, and every public name it does not hold, project over the
    sound members; a name both scopes hold reads the Tag; the warning
    when a Pin lands a name the members answer;
  - no value (rule 1.7): `== None` and `!= None` for a missing name and
    for `None`, for a Record, a condition and an Action; `== True` and
    `== False` skipping members with no value; a walk of values skipping
    them; the warning when no member has the name;
  - liveness: a member joins, a member breaks a promise, or a level
    changes, after the Filter was made;
  - every refusal: `bool()`, `in` on a Projection, a non-boolean
    comparison, a Rogue or defective member reaching a
    published name, assignment on a population, a Projection that would
    apply a Tag (at the call for a Link the root's Tag grants, and at the
    walk, before any value is called, for a Record that holds a Tag);
  - chained comparisons failing loudly: `a < P < b` at the `and`, and
    `ruth in P > 3` and `ruth not in P > 3` at the `in`;
  - the warning for a call that is never walked;
  - reading through a Link: the comprehension reads `link[m].x` for a
    name the Pair answers, and `m.x` otherwise.
- TopKit: populations refuse assignment of names, and the test that a
  population has no public names covers every kind.
- The Guide and the Fields Guide: "Nothing TOP-level lives at
  `Wizard.something`" restated as rule 1.1, and a section "Filters" in
  the Fields Guide, with Carroll's cakes as the first example.
- `tests/oracle_topkit.py`: Filters over random populations, checked
  against comprehensions on the same walk.
- `benchmarks/scenarios.py`: the cost of a walk, a Filter against a
  comprehension.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Decided by the Director on 2026-10-08, ahead of the whole STEP:*
> section 5 stands. A Filter refuses `bool()`, to protect chained
> comparisons: "your reasoning makes sense. we'll refuse to protect that."
> "Anyone?" is `len(f) > 0` for now; the Director will come back to that
> spelling.
>
> *Decided by the Director on 2026-10-08:* rule 1.7, a member with no
> value is `NULL`-like: "== None is the way to check for non-defined
> gains (records, contracts, actions...) and != None so it simply
> exists".
>
> *Decided by the Director on 2026-10-09:* a walk of values skips the
> members with no value ("sum(Wizard[].level) skipping nulls is
> sound"); the dot on a Tag reads only the Tag ("Wizard.level is a
> report"); no named root key ("Wizard[Sound] looks horrible. It takes
> over programmer's choices, not language options. Skip."). The root for the sound members goes to STEP-SPEC-29.
>
> *Drafted for the Director's review.* The Director asked for this on
> 2026-10-08: "Record/action filters are a neat thing. ... We should
> implement it." And: "Isn't this better stated as just Wizard.level >
> 3? Do we need the full universe of wizards?"
