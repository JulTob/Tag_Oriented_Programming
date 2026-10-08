# STEP-SPEC-20: Field Filters

- **STEP:** SPEC-20
- **Desk:** spec
- **Title:** Field Filters: populations by attribute
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A population can be asked about its members' attributes. `Wizard[:].level`
is a **Projection**: each member's `level`, read at the moment it is
asked. Comparing a Projection gives a **Filter**: `Wizard[:].level > 3`
is the population of Wizards whose level is above 3. Like every combined
view it is alive, and it combines with `|`, `&` and `-`. A chain fans
out through Fields: `Social[:].Knows[:] == ruth` is everyone in Social
who knows Ruth. An Action's result filters too, so a Filter can follow a
system that is changing: `Wizard[:].Can_Cast("Light") == True`.

```python
veterans = Wizard[:].level > 3                    # a Filter: alive, not a list
for wizard in veterans & Sworn:                   # the algebra of Fields
    print(wizard.name)

ari.level = 5
assert ari in veterans                            # it follows the system

old_friends = charlie.Knows[:].since < 2000       # on a Link, the Pair's Records (STEP-SPEC-19)
who_knows_ruth = Social[:].Knows[:] == ruth       # some contact of theirs is Ruth
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
lists. A filter is a view that the language does not yet give.

With Links (STEP-SPEC-19), TOP also gets **two-place statements**: *Charlie
knows Ruth*. That is the step from Carroll's monadic logic to the
**logic of relations** (De Morgan; Peirce's "logic of relatives"), and a
Filter is how a program asks it questions: `Social[:].Knows[:] == ruth`.

### Why not functions

A filter function, `Where(Wizard, lambda w: w.level > 3)`, would work. But
it takes the reader out of the language's own structures. TOP spells
every act with the language's syntax (§0.8): `in`, `for`, `[:]`, `del`,
the operators. Comparison operators are the language's own way to say
*greater than*, and a population is the thing being compared.

## Specification

A new section, **§2.9 Filters**, in Ring 2, beside the population algebra
of §2.5.

### 1. Projection

1. **Any population answers its members' names.** Reading a public name on
   a population gives a **Projection**: for each member, in the
   population's order, the value that `member.name` reads at that moment.
   This is the current Agent access of §1.7: Records, Actions, published
   members, conditions read by name (§2.5), and host attributes.

   The populations are:
   - the whole Field, `Wizard[:]`;
   - the defective population, `~Wizard`;
   - every combined view;
   - every Filter.
2. **A Tag's own dotted names stay its own** (§0.8). `Wizard.level` is a
   Report or nothing, never a Projection. To project, name a population:
   `Wizard[:].level`. The sound members are reached through the algebra,
   `Wizard & (Wizard[:].level > 3)`, because a Tag in an operator seat is
   its sound population.
3. **Names that begin with an underscore are never projected.** They
   belong to the kit and the language. Populations have no public names of
   their own: TopKit's `Add` and `Remove` on a Field are private since
   STEP-SPEC-19's pull request.
4. **On a Link's Field**, a Projection reads the Pair's Records first and
   then the Contact's own members: `charlie.Knows[:].since` reads each
   Pair (STEP-SPEC-19 §7).
5. **On a Pin's Field**, a Projection reads the pinned Tags' members:
   `Rare[:].rarity`.
6. **A member that cannot answer the name stops the walk.** The failure is
   the one the language raises, and it names the member and the name. A
   Rogue member reaching a published member raises `TagRogueAccessError`
   (§1.5), and a secret read from outside fails as it does anywhere
   (§1.7). To project a mixed population, narrow it first:
   `(Wizard[:] & Caster[:]).spells`.

### 2. Filter

1. **Comparing a Projection gives a Filter.** The operators are `==`,
   `!=`, `<`, `<=`, `>` and `>=`, with the Projection on either side. A
   Filter is the population of the Projection's **root** members whose
   value compares true, in the root's order.
2. **Values compare as the language compares them.** For an Agent without
   its own `__eq__`, `==` is identity. A host that defines equality is
   compared by it.
3. **A comparison must answer `True` or `False`** (§2.1). A comparison
   that answers anything else, such as an array or a number, stops the
   walk with a Contract Failure. TOP never coerces a truth value.
4. **A Filter is a population.** It walks its root members, answers `in`
   and `len`, combines with `|`, `&` and `-`, and projects again. It is
   alive: it reads its root and recomputes every value at every walk, so
   it is never stale (Fields Guide, section 3).

### 3. Calls

1. **Calling a Projection calls each member's value**, with the same
   arguments, at walk time. The result is a Projection of the results:
   `Wizard[:].Can_Cast("Light") == True`.
2. **A Filter by a call is dynamic.** Every walk calls again, so its
   population follows the system as it changes. An Action that changes
   something will change it again at every walk. The Guide says it
   plainly: filter by questions, never by commands.

### 4. Chains

1. **A Projection projects further**: `Wizard[:].familiar.name`.
2. **`[:]` on a Projection fans out.** When each value is a Tag, a Link or
   a population, `[:]` walks the members of each one.
3. **A comparison at the end of a chain keeps a root member when some
   leaf compares true.** This is Carroll's and Aristotle's "some".
   `Social[:].Knows[:] == ruth` is every Agent in Social who has at least
   one Contact that is Ruth: "anyone who knows Ruth".
4. **"All" is the difference of a "some".** *Everyone whose Contacts are
   all friendly* is *Social less those with some unfriendly Contact*:
   `Social[:] - (Social[:].Knows[:].friendly == False)`. As in
   syllogistic, "all" over nothing is true: an Agent with no Contacts is
   in that population.
5. **"Not" is a difference too, never `!=`.** Over a fan-out, `!=` keeps
   a root member when *some* leaf differs: `Social[:].Knows[:] != ruth`
   is everyone with some Contact who is not Ruth. *Those who do not know
   Ruth* is `Social[:] - (Social[:].Knows[:] == ruth)`. Without a fan-out
   there is one value per member, and `!=` is the plain opposite of `==`.

### 5. Truth

**A Projection and a Filter refuse `bool()`.** The refusal is a
`TypeError` whose message names the spelling to use instead: `len(f) >
0` to ask "anyone?", and `(a < P) & (P < b)` for a range.

The reason is the language's chained comparison. Python reads `2000 < P
< 2020` as `(2000 < P) and (P < 2020)`, and `and` asks the truth of the
first Filter. If a population had a truth value there, the result would
be the second Filter alone: the lower bound would be dropped in silence
whenever anyone was above it. `ruth in P > 3` hides the same trap. A
refusal makes both mistakes loud.

`any(f)` is not "anyone?" either. It asks each member's own truth, and an
Agent's truth is its contract (§2.5), so a Filter of broken Agents would
answer `False`. `len(f) > 0` asks the population.

### 6. Not in this STEP

- Writing through a Projection, such as `Wizard[:].hp = 10`.
- Broadcasting an Action for its effect, such as `Enemy[:].Take_Damage(5)`.

Both are commands, not questions, and each deserves its own STEP. A
Projection refuses assignment.

## Rationale

**The language's own structures.** Comparison operators and attribute
reads on a population read like the domain: *the Wizards whose level is
greater than three*. The idea is the boolean mask that Python's data
tools made familiar (`df[df.level > 3]`), with populations instead of
masks. That keeps it inside TOP's algebra: a Filter is combined with
`&`, kept as a view, and walked with `for`.

**The root, and "some".** A chain fans out, but the answer is always the
population the chain started from. That is the only reading under which
`Social[:].Knows[:] == ruth` means what it says: *those in Social who
know Ruth*, not *Ruth*. "Some" is the quantifier a fan-out needs, and
"all" falls out of `-`, as it does in Carroll's game.

**Loud, never silent.** A member that cannot answer, a comparison that
answers something other than a truth value, and a chained comparison all
fail where they happen. A filter that quietly drops members because of a
typo (`Wizard[:].levle > 3` coming back empty) is the bug this STEP must
never make easy.

**Dynamic by design.** The Director: "The fact we could filter by action
results also means is a dynamic system. I like the idea." A Filter holds
no values. It holds the question, and asks it again at every walk.

## Backwards compatibility

Nothing that works today changes. Reading a public name on a population
was an AttributeError before, apart from the Field's `Add` and `Remove`,
which became private in STEP-SPEC-19's pull request. Comparing a
population was the language's default (identity for `==`, a TypeError for
`<`). `bool()` of a Projection or Filter is new, and refused.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Comprehensions, `[w for w in Wizard if w.level > 3]` | They stay valid Python, but give a frozen list outside the algebra. |
| A filter function, `Where(Wizard, lambda w: w.level > 3)` | It takes the reader out of the language's structures (§0.8); the Director prefers language structures to function calls. |
| Mask indexing, `Wizard[:][Wizard[:].level > 3]` | `Tag[...]` is already the view and the Field; it would also name the population twice. |
| Projections on the Tag itself, `Wizard.level > 3` | The Tag's dotted namespace belongs to the program (§0.8). |
| A Filter with a truth value, "is anyone in it?" | Rejected: it makes chained comparisons silently wrong (§5). |
| Members without the name skipped silently | Rejected: a misspelt name would filter everyone out with no error. |
| "All" as the meaning of a fan-out | Rejected: "some" is what `== ruth` asks, and "all" is one `-` away. |

## Open questions for the Director

1. **Truth (§5).** A refused `bool()` means `if Social[:].Knows[:] == ruth:`
   must be written `if len(Social[:].Knows[:] == ruth) > 0:`. The
   alternative keeps a truth value, as Tags have (`if Wizard:`), and
   teaches `&` for ranges, accepting that `a < P < b` will be silently
   wrong. The STEP recommends the refusal.
2. **Missing names (§1.6).** Stop the walk (recommended), or treat a
   member that cannot answer as not matching?
3. **Link lookup order (§1.4).** On a Link's Field, the Pair's Records win
   over the Contact's own names when the two share a name. Is that the
   reading you want, or should a shared name be refused?

## Acceptance requirements

- `tests/test_topkit.py`: a `FilterTests` class, covering:
  - every numbered rule;
  - liveness: a member joins, or a level changes, after the Filter was
    made;
  - every refusal: `bool()`, a non-boolean comparison, a missing name, a
    Rogue member, assignment;
  - chained comparisons failing loudly.
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
