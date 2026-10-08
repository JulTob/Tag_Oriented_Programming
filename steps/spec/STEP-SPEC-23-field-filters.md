# STEP-SPEC-23: Field Filters

- **STEP:** SPEC-23
- **Desk:** spec
- **Title:** Field Filters
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08. First drafted as STEP-SPEC-20; renumbered
  because 20 is claimed by another open STEP.

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A population can be asked about its members' attributes.

**A Projection.** `Wizard[:].level` reads each member's `level` at the
moment it is asked. The population it is read from is its **root**.

**A Filter.** Comparing a Projection gives a Filter. `Wizard[:].level > 3`
is the population of the root's members whose level is above 3. Like
every combined view it is alive, and it combines with `|`, `&` and `-`.

**Chains.** A chain fans out through Fields. `Social[:].Knows[:] == ruth`
is everyone in Social who knows Ruth.

**Calls.** An Action's result filters too, so a Filter follows a system
that is changing: `Wizard[:].Can_Cast("Light") == True`.

```python
veterans = Wizard[:].level > 3                    # a Filter: alive, not a list
for wizard in veterans & Sworn:                   # the algebra of Fields
    print(wizard.name)

ari.level = 5
assert ari in veterans                            # it follows the system

old_friends = charlie.Knows[:].since < 2000       # on a Link, the Pair's Records (STEP-SPEC-22)
who_knows_ruth = Social[:].Knows[:] == ruth       # some Contact of theirs is Ruth
ready = Wizard[:].Can_Cast("Light") == True       # by an Action's result, at every walk
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
lists. A Filter is a view that TOP does not yet give.

With Links (STEP-SPEC-22), TOP also gets **two-place statements**:
*Charlie knows Ruth*. That is the step from Carroll's monadic logic to
the **logic of relations** (De Morgan; Peirce's "logic of relatives"). A
Filter is how a program asks it questions: `Social[:].Knows[:] == ruth`.

### Why not functions

A filter function, `Where(Wizard, lambda w: w.level > 3)`, would work.
TOP keeps functions for queries that need a name (§0.8: `Form`, `Tags`,
`Outline`), and spells its acts in the language's own syntax: `in`,
`for`, `[:]`, `del`, the operators. A filter needs no name. *Greater
than* is a comparison, and the language already has the operator for it.

## Specification

A new section, **§2.9 Filters**, in Ring 2, beside the population algebra
of §2.5, and one row in §0.8.

In this STEP, § cites the Specification only. This STEP's own parts are
cited as "section N" or "rule N.M".

### 1. Projection

1. **A population answers its members' names.** Reading a public name on
   a population gives a **Projection**. The population is the
   Projection's **root**. For each member of the root, in the root's
   order, the Projection reads the value that `member.name` reads at that
   moment. This is the current access of §1.7: Records, Actions,
   published members, conditions read by name (§2.5), and host
   attributes.

   The populations are:
   - the whole Field, `Wizard[:]`, which holds the defective members too;
   - the defective population, `~Wizard`, projected in brackets:
     `(~Wizard).level`, because the language reads `~Wizard.level` as
     `~(Wizard.level)`;
   - every combined view;
   - every Filter.

   A Relation is not a population: `Social.Knows[:]` is refused
   (STEP-SPEC-22, section 9). Ask through the Agents who hold the Links:
   `Social[:].Knows[:]`.
2. **A Tag's own dotted names stay its own** (§0.8). `Wizard.level` is
   whatever the Tag's namespace holds, a Report or the declaration of a
   Record, and never a Projection. To project, name a population:
   `Wizard[:].level`.

   The sound members, the ones `for w in Wizard` walks, are kept with the
   algebra: `(Wizard[:].level > 3) & Wizard`. A Tag in an operator seat
   is its sound population. Open question 4 asks for a shorter spelling.
3. **Names that begin with an underscore are never projected.** They
   belong to the kit and the language. A population has no public names
   of its own, and refuses assignment of any. The Field's `Add` and
   `Remove` became private in TopKit's change of pull request #26, which
   carries this STEP.
4. **Through a Link.** A member reached through a Link is read through
   that Link:
   - a name the Pair answers (a Record, an Action, a condition or a
     published member that the Link's Form gives the Pair) reads the
     Pair, `charlie.Knows[member].since` (STEP-SPEC-22, section 7);
   - any other name reads the Contact, `member.name` (rule 1.1).

   This holds for:
   - a Link's Field, `charlie.Knows[:]`;
   - its defective population, `~charlie.Knows`;
   - a Filter rooted on either one: a Filter always reads as its root
     does;
   - each leaf of a fan-out through Links (section 4), read through the
     Link it was walked from: `Social[:].Knows[:].since` reads
     `agent.Knows[leaf].since`.

   A combined view sees its members through no Link, because a member may
   have one Pair in each operand. So `(charlie.Knows & bob.Knows).since`
   reads each Contact's own `since`. To filter on a Pair there, filter one
   Link's Field and combine: `(charlie.Knows[:].since < 2000) & bob.Knows`.
5. **On a Pin's Field**, each member is a pinned Tag, and a Projection
   reads that Tag's own names. `Rare[:].rarity` reads `tag.rarity` for
   each pinned Tag (for Wizard, `Wizard.rarity`), never a name on the
   Tag's Agents (§1.9).
6. **A member that cannot answer the name stops the walk.** The failure
   is the one the language raises for that name.
   - A member that has left the Tag that published the name is a Rogue
     Agent of that Tag. Reading its published Report, or calling its
     published Operation through a Projection's call (section 3), raises
     `TagRogueAccessError` (§1.5).
   - A defective member is refused a published member, and the refusal
     names the broken promise (§1.5). So a published name over the whole
     Field stops at the first defective member. Keep the sound members
     first (rule 1.2).
   - A secret read from outside fails as it does anywhere (§1.7).

   To project a mixed population, narrow it first:
   `(Wizard[:] & Caster[:]).spells`.
7. **A Projection is not a population.** It is the values of one
   question, not a set of Agents.
   - It walks its values, one per root member, or one per leaf after a
     fan-out (section 4), so `sum(Wizard[:].level)` adds the levels.
     `len` counts those values.
   - It refuses `in` and `not in`, with a `TypeError` whose message says
     to compare first: `ruth in (P > 3)`.
   - It refuses assignment and `del`. Of indexes it answers only `[:]`
     (section 4).

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
   `Wizard[:].Can_Cast("Light") == True`.
2. **A Filter by a call is dynamic.** Every walk calls again, so its
   population follows the system as it changes. `len(f)` walks too. An
   Action that changes something will change it again at every walk. The
   Guide says it plainly: filter by questions, never by commands.
3. **A call that is never walked says so.** A called Projection that is
   dropped without ever being walked or compared raises a warning when it
   is collected. This is the same warning Python gives for a coroutine
   that is never awaited. So `Enemy[:].Take_Damage(5)` on a line of its
   own does nothing, and the warning says so. Broadcasting a command is
   not in this STEP (section 6).

### 4. Chains

1. **A Projection projects further**: `Wizard[:].familiar.name`.
2. **`[:]` on a Projection fans out.** When each value is a Tag, a Link
   or a population, `[:]` walks the members of each one. A value that is
   none of these stops the walk with a `TypeError` that names it.
3. **A comparison at the end of a chain keeps a root member when some
   leaf compares true.** This is the "some" of Aristotle and Carroll.
   `Social[:].Knows[:] == ruth` is every Agent in Social whose Link
   holds Ruth among its Contacts: "anyone who knows Ruth".
4. **"All" is the difference of a "some".** *Everyone whose Contacts are
   all friendly* is *Social less those with some unfriendly Contact*.
   Here `friendly` is the Contact's own attribute (rule 1.4):
   `Social[:] - (Social[:].Knows[:].friendly == False)`.

   An Agent with no Contacts is in that population. Modern logic reads
   it this way, after Boole: "all" over nothing is true. Aristotle and
   Carroll read "all x are y" as also saying that some x exist.
5. **"Not" is a difference too, never `!=` over a fan-out.** Over a
   fan-out, `!=` keeps a root member when *some* leaf differs.
   `Social[:].Knows[:] != ruth` is everyone with some Contact who is not
   Ruth. *Those who do not know Ruth* is
   `Social[:] - (Social[:].Knows[:] == ruth)`.

   Without a fan-out there is one value per member, and `!=` is the plain
   opposite of `==`.

### 5. Truth

**A Projection, a Filter, and any combination that contains a Filter
refuse `bool()`.** The refusal is a `TypeError` whose message names the
spelling to use instead: `len(f) > 0` to ask "anyone?", and
`(a < P) & (P < b)` for a range.

The reason is the language's chained comparison. Python reads `2000 < P
< 2020` as `(2000 < P) and (P < 2020)`, and `and` asks the truth of the
first Filter. If a Filter had a truth value there, the result would be
the second Filter alone, and the lower bound would be dropped in silence
whenever anyone was above it. The refusal makes that mistake loud.

`ruth in P > 3` is the same kind of chain: Python reads `(ruth in P) and
(P > 3)`. There `in` already answers a plain `True` or `False`, so no
refusal of `bool()` could see it. It fails loudly because a Projection
refuses `in` (rule 1.7), and the message names `ruth in (P > 3)`.

`any(f)` is not "anyone?" either. It asks each member's own truth, and an
Agent's truth is its contract (§2.5), so a Filter of broken Agents would
answer `False`. `len(f) > 0` asks the population.

### 6. Not in this STEP

- Writing through a Projection, such as `Wizard[:].hp = 10`. It is
  refused (rule 1.7).
- Broadcasting an Action for its effect, such as `Enemy[:].Take_Damage(5)`.
  It does nothing, and warns (rule 3.3).

Both are commands, not questions, and each deserves its own STEP.

## Rationale

**The language's own structures.** Comparison operators and attribute
reads on a population read like the domain: *the Wizards whose level is
greater than three*. The idea is the boolean mask that Python's data
tools made familiar (`df[df.level > 3]`), with populations in place of
masks. That keeps it inside TOP's algebra: a Filter is combined with
`&`, kept as a view, and walked with `for`.

**The root, and "some".** A chain fans out, but the answer is always the
population the chain started from. That is the only reading under which
`Social[:].Knows[:] == ruth` means what it says: *those in Social who know
Ruth*, not *Ruth*. "Some" is the quantifier a fan-out needs, and "all"
comes from `-`, as it does in Carroll's game.

**Loud, never silent.** These all fail where they happen:
- a member that cannot answer;
- a comparison that answers something other than a truth value;
- a chained comparison;
- `in` on a Projection;
- a call that is never walked.

A filter that quietly drops members because of a typo
(`Wizard[:].levle > 3` coming back empty) is the bug this STEP must never
make easy.

**Dynamic by design.** The Director: "The fact we could filter by action
results also means is a dynamic system. I like the idea." A Filter holds
no values. It holds the question, and asks it again at every walk.

## Backwards compatibility

Nothing that works today changes.
- Reading a public name on a population was an `AttributeError` before.
  The Field's `Add` and `Remove` were the exception, and they became
  private in pull request #26.
- Comparing a population fell back to the language's defaults: identity
  for `==`, a `TypeError` for `<`.
- `bool()` of a Projection or a Filter is new, and refused.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Comprehensions, `[w for w in Wizard if w.level > 3]` | They stay valid Python, but give a frozen list outside the algebra. |
| A filter function, `Where(Wizard, lambda w: w.level > 3)` | A filter needs no name, so it is spelt with the language's operators (§0.8); the Director prefers language structures to function calls. |
| Mask indexing, `Wizard[:][Wizard[:].level > 3]` | `Tag[...]` is already the view and the Field; it would also name the population twice. |
| Projections on the Tag itself, `Wizard.level > 3` | The Tag's dotted namespace belongs to the program (§0.8). |
| A Filter with a truth value, "is anyone in it?" | Rejected: it makes chained comparisons silently wrong (section 5). |
| Members without the name skipped silently | Rejected: a misspelt name would filter everyone out with no error. |
| "All" as the meaning of a fan-out | Rejected: "some" is what `== ruth` asks, and "all" is one `-` away. |
| Eager calls, made when the Projection is called | Rejected: the Filter would stop following the system. |

## Open questions for the Director

1. **Truth (section 5).** A refused `bool()` means `if Social[:].Knows[:]
   == ruth:` must be written `if len(Social[:].Knows[:] == ruth) > 0:`.
   The alternative keeps a truth value, as Tags have one (`if Wizard:`),
   and teaches `&` for ranges, accepting that `a < P < b` will be
   silently wrong. The STEP recommends the refusal.
2. **Missing names (rule 1.6).** Stop the walk (recommended), or treat a
   member that cannot answer as not matching?
3. **Lookup through a Link (rule 1.4).** On a Link's Field, and after a
   fan-out through a Link, a name the Pair answers wins over the Contact's own
   attribute of the same name. Is that the reading you want, or should a
   shared name be refused?
4. **The sound population.** `Wizard[:]` holds the defective members too,
   and `Wizard.level` belongs to the Tag. A short spelling for the sound
   population as a population, such as `+Wizard` (the mirror of
   `~Wizard`), would make `(+Wizard).level > 3` the Filter that
   `[w for w in Wizard if w.level > 3]` means. The brackets are needed,
   as for `~Wizard`. Add it, or keep `(Wizard[:].level > 3) & Wizard`?

## Acceptance requirements

- `tests/test_topkit.py`: a `FilterTests` class, covering:
  - every numbered rule;
  - liveness: a member joins, or a level changes, after the Filter was
    made;
  - every refusal: `bool()`, `in` on a Projection, a non-boolean
    comparison, a missing name, a Rogue or defective member reaching a
    published name, assignment;
  - chained comparisons failing loudly: `a < P < b` at the `and`, and
    `ruth in P > 3` and `ruth not in P > 3` at the `in`;
  - the warning for a call that is never walked;
  - reading through a Link: the comprehension reads `link[m].x` for a
    name the Pair answers, and `m.x` otherwise.
- TopKit: populations refuse assignment of names, and the test that a
  Field has no public names covers every kind of population.
- The Fields Guide: a section "Filters", with Carroll's cakes as the
  first example.
- `tests/oracle_topkit.py`: Filters over random populations, checked
  against comprehensions on the same walk.
- `benchmarks/scenarios.py`: the cost of a walk, a Filter against a
  comprehension.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's review.* The Director asked for this on
> 2026-10-08: "Record/action filters are a neat thing. ... We should
> implement it."
