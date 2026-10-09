# STEP-SPEC-29: The Population Algebra

- **STEP:** SPEC-29
- **Desk:** spec
- **Title:** The Population Algebra
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-09

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

This STEP is the one place that defines the algebra of populations: which
spellings exist, what each means, what it gives back, and what happens
when nobody is there. Other STEPs keep their topics and point here.

In one breath: a bare Tag means its sound members. `+X` is the sound
part of a root, and `~X` its broken part. Inside `[ ]` goes only "who":
`[:]` for everyone, `[...]` for the safehouse, an Agent, or a place. A
comparison on a Projection is the mask. `del X[:]` Rips a population from
its home. Everything else is Python's own tools.

> **Superseded in part on 2026-10-09.** A plain Tag has no places. The
> Director: "So I would not implement [0] and[-1] then because that would demand any number to be an input there." And: "I would then make it so Wizard, the plain tag, doesn't accept the [] call with numbers (the tag is itself not ordered, but +Wizard would, as it returns a list. I know this is weird, but it forces a separation of masks+lists vs tags"
> So `Wizard[0]`, `Wizard[-1]` and every number key on a bare Tag are
> refused (*Decided*). Rules 6.1 and 6.2 no longer apply to a bare Tag,
> and open question 2 is closed. Still *Open*: whether `+Wizard` gives a
> list with places, as the Director proposes, or stays a live group,
> with `list(Wizard)` as the step into a list (open question 8). The
> rows below that use places on other populations wait for that answer.

**Words used here.**
- **Sound**: every visible promise (Postcondition) of the Agent holds.
  **Broken** (defective): a member with a broken promise.
- **Population**: a live group of Agents. It answers `for`, `len`, `in`,
  `|`, `&`, `-`, `[:]` and `[n]`.
- **Root**: a whole that splits into parts: a Tag, `Wizard[:]`,
  `Wizard[...]`, or a Link such as `charlie.Knows`.
- **Part**: `+X`, the sound members of root X, or `~X`, the broken ones.
- **Projection**: one name read across a population, `(+Wizard).level`.
- **Filter**: a Projection after a comparison, `(+Wizard).level > 3`. It
  is a population.
- **Pick**: one Agent taken out of a population.
- **Home**: the one Tag a population was drawn from.
- **Absorbs**: doing it twice changes nothing. `~~X` is `~X`.
- **TagCategoryError**: STEP-28's failure for treating one kind of TOP
  thing as another. It is a `TypeError` too.

**Status marks**: **Decided** (the Director ruled; his words are at the
rule), **On main** (main's Specification already says it; no new
ruling), **Vetting** (written on S19, under review), **Recommended**
(this STEP proposes; he decides), **Open** (an open question),
**Python** (the language fixes it; no choice).

| Spelling | Meaning | Gives | When nobody is there | Status | Rule |
| --- | --- | --- | --- | --- | --- |
| **The Tag and its dot** | | | | | |
| `Wizard.motto`; `Wizard.motto = "wise"` | read or set the Tag's own Report | value; — | — | Decided | 1.1, 1.3 |
| `Wizard.level`, `Wizard.spells` (names its Agents have) | refused, naming `(+Wizard).level`; `hasattr` is False | AttributeError | — | Recommended (no projection: Decided) | 1.2 |
| `Wizard.hp = 10` (`hp` a Record) | refused, naming `(+Wizard).hp = 10` | TagCategoryError | — | Decided (message Recommended) | 1.3 |
| `+Wizard.level`; `+Wizard.rank`, `~Wizard.rank` (the Tag holds a number `rank`) | read as `+(Wizard.level)`, refused at the dot; silently `+` or `~` of the Tag's number | AttributeError; number | — | Python | 1.4 |
| **Populations and truth** | | | | | |
| bare `Wizard` in `for`, `len`, `if`, `in`, `\|`, `&`, `-` | the sound members, in join order | population | 0 rounds; `len` 0; False | Decided (`in`); On main (the rest) | 2.1 |
| `Wizard[:]` (`Wizard[::]` is the same key); `X[:]` on any other population | everyone in the Field; X itself | population | empty | Decided; Recommended | 2.2 |
| `ari in Wizard`; `ari in Wizard[:]`; `ari in ~Wizard` | a sound member? a member at all? a broken member? | bool | False | Decided | 2.1 |
| `if ari:`; `if Wizard:`, `if ~Wizard:` | do ari's promises hold? anyone sound? anyone broken? | bool | False | Decided (`if ari:`); On main (`if Wizard:`, `if ~Wizard:`) | 2.3 |
| `Wizard(purse)`, a host with its own `__bool__` | refused at tagging | TagCategoryError | — | Decided | 2.3 |
| `(+Enemy).hp = 10`; `weak.hp = 5`; `(~Enemy).hp = 4`; `Enemy[:].hp = 7` | write each sound Enemy; a Filter's members, read at the start; the broken; everyone | — | nothing written | Recommended | 2.4 |
| **The parts** | | | | | |
| `+Wizard`, `++Wizard`, `+Wizard[:]` | the sound part | population | empty | Recommended | 3.1, 3.2 |
| `~Wizard`, `~~Wizard`, `~~~Wizard`, `~Wizard[:]` | the broken part | population | empty | On main (`~Wizard`, §0.8); Recommended (`~~` absorbs, `~Wizard[:]`) | 3.1, 3.2 |
| `+~Wizard`, `~+Wizard` | refused: always empty | TagCategoryError | — | Recommended | 3.3 |
| `+X \| ~X`; `+X & ~X` | everyone; nobody | population | empty | Recommended | 3.3 |
| `-Wizard` | refused, naming `~Wizard`, `Wizard[...]` and `A - B` | TagCategoryError | — | Recommended | 3.4 |
| `Wizard[...]`, `Tag[...]`; `+Wizard[...]`, `~Wizard[...]` | Wizard's safehouse; the whole safehouse; its sound and broken kept Agents | population | empty | Decided; parts Recommended | 3.5 |
| **Combinations** | | | | | |
| `Wizard \| Fighter`, `Wizard & Sworn`, `Wizard - Sworn`; `~Wizard \| ~Fighter` | the sound members combined; broken in either | population | empty | On main (§2.5; STEP-13 at Vetting) | 4.1 |
| `~(Wizard \| Fighter)`, `+(Wizard[:] \| Fighter[:])` | refused: `+` and `~` split roots; names `~Wizard \| ~Fighter` | TagCategoryError | — | Recommended | 4.2 |
| `Rare \| Wizard`, `Rare[:] & Wizard` | refused: Tags with Agents | TagCategoryError | — | Decided | 4.3 |
| **Projections, Filters, masks** | | | | | |
| `(+Wizard).level`, `Wizard[:].level`, `(~Wizard).level` | each member's value | Projection | walks nothing | Recommended | 5.1 |
| `sum((+Wizard).level)` | adds the values there are | number | 0 | Decided | 5.1 |
| `(+Wizard).level > 3`, and `==`, `!=`, `<`, `<=`, `>=` | the sound Wizards above level 3, live | Filter | empty | Recommended | 5.2 |
| `veterans & Sworn`; `+Wizard - veterans` | combine; "not" | population | empty | Recommended | 5.2, 5.5 |
| `P == None`, `P != None`; `P == True` | no value; a value; Python's `==` (`level == True` keeps level 1) | Filter | empty | Decided; `== True` Recommended | 5.3 |
| `len(f) > 0`; `bool(f)`, `if f:`, `2 < P < 5` | anyone in the Filter?; refused | bool; TagCategoryError | False; — | Decided | 5.4 |
| `~f`, `+f`; `Wizard[f]`, `Wizard[:f:]`; `P[True]`, `P[0]` | refused: "not" is `root - f`; the Filter is the population; compare, or pick then read | TagCategoryError | — | Recommended | 5.5, 5.6 |
| `[w for w in Wizard if w.level > w.hp]` | Python's mask, for what a Filter cannot ask | list | `[]` | Python | 5.7 |
| **Picks** | | | | | |
| `Wizard[0]`, `Wizard[n]`, `Wizard[-1]` | the oldest sound one; place n now; the newest | Agent | IndexError naming the count now | Recommended | 6.1 |
| `Wizard[:][0]`, `(~Wizard)[0]`, `veterans[0]` | the oldest of everyone; one broken Wizard; one veteran | Agent | IndexError | Recommended | 6.2 |
| `Wizard[True]`, `Wizard[False]` | refused, naming `+X`, `~X` and `X[0]` | TagCategoryError | — | Recommended | 6.3 |
| `next(iter(X), None)` | "Any. or None." | Agent or None | None; test `is not None` | Recommended | 6.4 |
| `[w] = X`; `random.choice(X)` | the only one; one at random | Agent | ValueError; IndexError | Python | 6.5 |
| `Wizard[0].level`; `~Wizard[0]` | pick, then read; `~(Wizard[0])`, so write `(~Wizard)[0]` | value; TypeError | IndexError at the pick | Recommended; Python | 6.6 |
| `Wizard[ari]`; `charlie.Knows[ruth]` | the view; the Pair | view; Pair | TagResolutionError | On main (§1.7); Pair Recommended | 6.7 |
| `Wizard[()]`, `Wizard["level"]`, `Wizard[1:3]` | refused: never an Agent, never a place | TagCategoryError | — | Recommended | 6.7 |
| **Walking** | | | | | |
| `for e in Enemy:`, when an earlier turn Rips a later member | that member is skipped | — | 0 rounds | Decided | 7.1 |
| `while Enemy:` | asks `bool(Enemy)` before each round; binds no name | — | 0 rounds | Python | 7.2 |
| `for e in rounds(Enemy):` | round robin, lap after lap | iterator | ends at once | Recommended (Guide) | 7.3 |
| **Deleting** | | | | | |
| `del Wizard[ari]`; `del Wizard[:]` | Rip; Field Rip | — | TagResolutionError; nothing | On main (§0.7); Recommended (STEP-24) | 8.1 |
| `del (~Wizard)[:]`, `del weak[:]` | Rip every broken Wizard; Rip a filtered group, read once | — | nothing | Decided | 8.1 |
| `del (Wizard - Sworn)[:]`; `del (Wizard \| Fighter)[:]`, `del (Wizard & Sworn)[:]` | Rip from Wizard; refused: two homes | —; TagCategoryError | nothing | Recommended | 8.2 |
| `del Wizard[...]`, `del Tag[...]`; `del Wizard[...][:]` | triage; refused for now | —; TagCategoryError | nothing | Vetting (S19); Open | 8.3 |
| `del Wizard[0]` | refused: pick, then Rip | TagCategoryError | — | Recommended | 8.4 |
| **Links** | | | | | |
| `charlie.Knows`, `+charlie.Knows`; `~charlie.Knows`; `charlie.Knows[:]` | sound Contacts (Contact and Pair sound); a broken Contact or Pair; all | population | empty | Recommended | 9.1 |
| `charlie.Knows.since`; `(+charlie.Knows).since`, `(+charlie.Knows).since = 2011` | refused at the dot; read or write the sound Pairs | AttributeError; Projection | empty | Recommended | 9.2 |
| a name both the Pair and the Contact hold | refused at the walk | TagCategoryError | — | Recommended | 9.3 |
| `Social.Knows`; `(+Social).Knows[:] == ruth` | always the Relation; who knows Ruth? | Relation; Filter | empty | Recommended | 9.4 |
| `charlie.Knows[0]`; `del (~charlie.Knows)[:]` | the first sound Contact; unlink the broken ones | Agent; — | IndexError; nothing | Recommended | 9.1 |

The Guide names the group on its own line, then acts on it, so round
brackets never nest:

```python
veterans = (+Wizard).level > 3          # a Filter: the sound Wizards above level 3, live
veterans[0].Teach()                     # "the first": the one who joined first
(+Enemy).hp = 10                        # write each sound Enemy
del (~Wizard)[:]                        # Rip every broken Wizard
```

## Motivation

The Director, on 2026-10-09: "I just thought... Wizard[0] is, naturally
speaking, the first ever WIzard, not any wizard. Numbers have order. But
numbers are not the only valid selector possible. Wizard[True] could mean
the ANY wizard that is valid. Just give me a true one.
Wizard[True].level > 3 would then give me a wizard that is a level
over 3. Any. or None. Alernatively myTag[True] and myTag[False] could
be the populations of valid and not valid myTags and a myTag[\<mask>]
could apply conditional filters. What do you think? We need to unify
all the design of sets and filters and such, as it is getting messy."

The spellings grew in six STEPs on three branches; the catalog
(`steps/CATALOG-tag-algebra.md`) lists them. Three gaps remain:
- **No object means "the sound members" and takes a dot.** The Tag no
  longer can (rule 1.1). STEP-25 writes `(Enemy[:] & Enemy)`, a shape he
  refused: "I refuse that monstrosity with redundant information"
  (STEP-23, open question 2).
- **Nothing picks one member.** `Wizard[0]` reads `0` as an Agent and
  fails (`TopKit/tags.py:212-226`).
- **`~` flips when doubled.** `~~Wizard` is the sound members again
  (`TopKit/fields.py:385-393`). He wrote: "~~Wizard should be ...
  actually puzzled here but I'll tell you what I think: ~means bad. If
  you say "bad bad wizard" you don't mean good, so the "bad", the ~ is
  absorbent and "~~= ~" so any number of ~ should mean "broken
  Wizards". Makes sense?"

## Specification

§ cites the Specification; "rule N.M" is this STEP's. Checked on Python
3.13.16 and this branch's kit, TopKit 0.2.0a4 (main's). "S19" is the
branch `origin/Julio_Cl/step-19-sound-in`; "PR #28" is
`origin/julio_cl/step-25-commands-to-a-population`.

### 1. The Tag and its dot

1. **The dot on a Tag reads the Tag.** *Decided.* `Wizard.x` is the
   Tag's own value: a Report, an Operation, what a Pin lands, a Link's
   Relation, or a value set on it (§0.8 gives the dotted names to the
   program). The Director: "Wizard.level is a report", and
   "Wizard[].level feels more like sound members".
2. **A name the Tag's Agents have is refused on the Tag.** *Decided that
   the dot never projects; the refusal is Recommended.* `Wizard.level`
   and `Wizard.spells` raise `AttributeError`, so `hasattr` is False. The
   message names `(+Wizard).level` and `Wizard[:].level`.
3. **A write on a Tag.** *Decided; the message is Recommended.* A name
   the Tag does not give its
   Agents becomes a Report: "if it looks like a report, then it is"
   (2026-10-08). A name it gives them is a `TagCategoryError` (STEP-28,
   rule 3) whose message names `(+Wizard).hp = 10`.
4. **An operator before a dot goes in round brackets.** *Python.* The dot
   binds tighter than `+` and `~`. So `+Wizard.level` fails loudly at the
   dot (rule 1.2), and `+Wizard.hp = 10` does not compile. One case is
   silent: when the Tag holds a number `rank`, `+Wizard.rank` is that
   number, and `~Wizard.rank` is `~` of it. The Guide teaches the habit.

### 2. Populations and roots

1. **A bare Tag means its sound members** in `for`, `len`, `if`, `in`,
   `|`, `&` and `-`, in join order. *Decided for `in`; On main for the
   rest* (§0.8, §2.5). For `in`:
   "ari in Wizard should be the sound members. Expected baseline. ari in
   Wizard[:] should be all members. ari in ~Wizard should be the
   defective members."
2. **`[:]` is everyone.** *On main for a Tag (§0.8); Recommended
   elsewhere.* On any other population, `X[:]` is X itself, so `del X[:]`
   can name any population (section 8). `Wizard[::]` passes the same key,
   `slice(None, None, None)`.
3. **Truth.** *Decided.* "if ari: should be ari is sound (primises
   hold)". `if Wizard:` asks "anyone sound?", `if ~Wizard:` "anyone
   broken?". A host class with its own `__bool__` is refused at tagging
   (STEP-28 rule 3): "Bool-like behaviour conflicts with contracts.
   should be refused." A host with only `__len__` is *Open*.
4. **A population takes a write.** *Recommended.* `(+Enemy).hp = 10`
   writes each sound Enemy, all or nothing, by STEP-25's rules. A Filter
   is read once, at the start.

### 3. The parts: sound, broken, everyone, safehouse

1. **`+X` is the sound part of a root, and `~X` its broken part.**
   *Recommended for `+`; `~` is On main (§0.8).* Roots are a Tag, its
   Field `Wizard[:]`, its safehouse `Wizard[...]`, and a Link. Under `+` or `~`, a bare Tag stands for its whole
   Field. So `+Wizard` and `+Wizard[:]` hold what bare `Wizard` walks,
   and `~Wizard[:]` is `~Wizard`.
2. **Both absorb.** *Decided for `~`; Recommended for `+`.* The
   Director, 2026-10-09: "Implement the "bad bad = bad" meaning of ~.
   ~~~~~~~~~~~~~Wizard is still ~Wizards". `~~X` is `~X`: "any number of ~ should mean "broken Wizards"".
   `++X` is `+X`.
3. **Opposite signs are refused; the laws.** *Recommended.* `+~X` and
   `~+X` are always empty, so each is a `TagCategoryError` naming `+X` or
   `~X`. `+X | ~X` holds the members of `X[:]`; `+X & ~X` is empty.
4. **`-X` is refused.** *Recommended.* The message names `~X` (broken),
   `X[...]` (the safehouse) and `A - B`. "Not" is the binary `-`, as
   STEP-23 rule 4.5 says.
5. **The safehouse.** *Decided.* "Wizard[...] should be the Wizard
   safehouse", and "Tag[...] is the total safehose" (STEP-18 amendment E,
   S19). Only a Tag takes the key `[...]` (*Recommended*). Its parts,
   `+Wizard[...]` and `~Wizard[...]`, are *Recommended*.

### 4. Combinations and category errors

1. **`|`, `&` and `-` combine populations of Agents** (either, both, the
   left without the right), left first, in join order. *On main* (§2.5;
   STEP-13 at Vetting).
2. **`+` and `~` split roots, not combinations.** *Recommended.* On a
   combination both are refused, and the message names one part per Tag,
   `~Wizard | ~Fighter`. STEP-13 item 4's refusal of `~` stands; its
   reason, "no universe", becomes this rule.
3. **Category errors.** *Decided where marked.* Every refusal here is a
   `TagCategoryError` (STEP-28), except the `AttributeError` of the dot
   (rules 1.2, 9.2), which keeps `hasattr` honest. A Pin's population
   with a Tag's is refused (*Decided*): "Rare | Wizard should raise a
   category error. Pins are pinable, but the return population of pins
   are tags, but tags' populations are agents." So is a population used
   as a type, `isinstance(x, Wizard | Fighter)` (STEP-13 item 5).

### 5. Filters and masks

1. **A Projection reads one name across a population.** *Recommended for
   the roots; the skip is Decided.* A walk skips members with no value:
   "sum(Wizard[].level) skipping nulls is sound." STEP-23 rules 1.7 and
   1.9 stand. Rule 1.4's refusal of writes gives way to STEP-25 (rule 2.4
   here), and rules 1.5, 1.6 and 1.8 change as "What this replaces"
   says.
2. **A comparison on a Projection is the mask. Nothing else is.**
   *Recommended* (STEP-23 rule 2.1). `(+Wizard).level > 3` is a Filter: a
   live population that combines, projects and picks like any other.
3. **No value.** *Decided* (2026-10-08): "== None is the way to check for
   non-defined gains (records, contracts, actions...) and != None so it
   simply exists". `P == True` is Python's `==` (STEP-23 rule 2.2), so
   `level == True` keeps level-1 members. A stricter form is *Open*.
4. **A Filter refuses `bool()`.** *Decided* (2026-10-08): "we'll refuse
   to protect that". "Anyone?" is `len(f) > 0`, for now.
5. **"Not" is `root - f`.** *Recommended.* `~f` and `+f` are refused; the
   message says "~ means 'broken' in TOP, not 'not'". The broken members
   above level 3 are `(~Wizard).level > 3`.
6. **No masks as keys, and no keys on a Projection.** *Recommended.*
   `Wizard[f]` is refused, and so is `Wizard[:f:]`: Python passes
   `slice(None, f, None)`, the key of `Wizard[:f]`. `P[True]`, `P[False]`
   and `P[0]` are refused: compare (`P == True`), or pick then read.
7. **Python's own mask.** *Python.* For what a Filter cannot ask, such as
   two names of one member: `[w for w in Wizard if w.level > w.hp]`, a
   frozen list.

### 6. Picks

> **Superseded in part on 2026-10-09.** A plain Tag has no places. The
> Director: "So I would not implement [0] and[-1] then because that would demand any number to be an input there." And: "I would then make it so Wizard, the plain tag, doesn't accept the [] call with numbers (the tag is itself not ordered, but +Wizard would, as it returns a list. I know this is weird, but it forces a separation of masks+lists vs tags"
> So `Wizard[0]`, `Wizard[-1]` and every number key on a bare Tag are
> refused (*Decided*). Rules 6.1 and 6.2 no longer apply to a bare Tag,
> and open question 2 is closed. Still *Open*: whether `+Wizard` gives a
> list with places, as the Director proposes, or stays a live group,
> with `list(Wizard)` as the step into a list (open question 8). The
> rows below that use places on other populations wait for that answer.

1. **`X[n]` is the Agent at place n now, in join order.** *Recommended.*
   "Numbers have order." On a Tag, places count the sound members. `0` is
   the oldest, `-1` the newest. A miss is an `IndexError` naming the count
   now. A population is live, so a place gives an Agent, never a seat.
2. **"The first", on every population.** *Recommended.* `Wizard[0]` is the
   oldest sound Wizard; `Wizard[:][0]` the oldest of everyone;
   `(~Wizard)[0]` one broken Wizard, for a repair line; `veterans[0]` "a
   wizard that is a level over 3". Which is "the first ever WIzard" is
   *Open*.
3. **A bool key is refused.** *Recommended.* Python treats `True` as `1`
   (`True == 1`, and `isinstance(True, int)`). So the kit tests
   `type(k) is bool` before the int test, and never calls `__index__`.
4. **"Any. or None."** *Recommended.* `next(iter(X), None)` gives `X[0]`,
   or `None`. It is the only pick that returns `None`. Test it with
   `is not None`, never `if w:`: a broken Agent is False too.
5. **Python's own picks.** *Python.* "The only one" is `[w] = X`, a
   `ValueError` for none or several. One at random is `random.choice(X)`.
   The slip to teach: without brackets, `w = X` binds the whole
   population. Then `w.hp = 10` writes every member of a population (rule
   2.4), and on a Tag it is a write on the Tag itself (rule 1.3).
6. **Pick, then read.** *Recommended.* `Wizard[0].level`. Python reads
   `~Wizard[0]` as `~(Wizard[0])`, a `TypeError`; write `(~Wizard)[0]`.
7. **Other keys.** *On main for the view (§1.7); Recommended for the
   rest.* An Agent key is the view; on a Link, the Pair (STEP-22 rule
   7.1). A key that is never an Agent or a place, such as `()`, a string
   or a slice with bounds, is refused.

### 7. Walking

1. **`for` walks in join order.** *Decided for the skip; the rest
   Recommended* (STEP-25 rule 6.5). At its turn, a member is visited if
   it is a member now. One that an earlier turn Ripped is skipped: "it
   makes sense, to skip the left out member". One Ripped and tagged
   again is visited. The Director, 2026-10-09: "a ripped agent should not
   be a member. that's an oximoron. If the agent is in, it was tagged, if
   the agent was ripped it's out so it does not make it to the list, and
   if an agent is tagged again, it is in the list so you shouldn't skip
   it." An Agent that joins during the walk waits for the next walk.
2. **`while X:` is Python's.** *Python.* It asks `bool(X)` before each
   round and binds no name. The Director: "while Enemy should be a loop.
   your notes indicate a stop when finds a member. it should loop through
   each sound Enemy, changing to the next Enemy in each iteration, and
   circle back to the first after the last one." Python cannot give
   `while` that meaning. The "stop" is the yes-or-no check
   (`TopKit/fields.py:375`), not the loop.
3. **The round robin is a `for` over a small generator.** *Recommended, as
   a Guide recipe; a kit name is Open.*

   ```python
   def rounds(population):
       """Each member in turn, lap after lap, until nobody is left."""
       while len(population) > 0:          # len, not bool: a Filter refuses bool()
           for member in population:       # a fresh walk each lap: re-reads who is there
               yield member


   for enemy in rounds(Enemy):
       enemy.Attack(hero)
       if hero.hp <= 0:
           break
   ```

   A newcomer joins on the next lap; a member Ripped or broken is
   skipped; it ends when nobody is left. It works on a Filter too.

### 8. Deletion over populations

1. **`del X[:]` Rips every member of X from X's home.** *Decided* for
   `del (~Wizard)[:]` and filtered groups: "del (~Wizard)[:] is good to
   delete all broken wizards. Also filtered groups... I like it a lot!
   very useful." The population is read once, at the start; then
   STEP-24's Field Rip runs (rules 1.3 to 1.5).
2. **The home.** *Recommended.* A Tag is its own home. `+`, `~`, `[:]`
   and a Filter keep the home. In `A - B` the home is A's; the right side
   only removes members. `A | B` and `A & B` have a home only when both
   sides share one; otherwise `del` is refused, naming one line per Tag.
3. **The safehouse.** *Vetting on S19:* `del Wizard[...]` and
   `del Tag[...]` are triage (STEP-18 amendment F, where the Director
   chose "End it, then let it go"). *Open:* `del Wizard[...][:]` is
   refused until STEP-24 open question 1 settles whether kept Agents are
   members.
4. **No Rip by place.** *Recommended.* `del Wizard[0]` is refused: an act
   names its target. Write `w = Wizard[0]`, then `del Wizard[w]`.

### 9. Links

1. **A Link is a root.** *Recommended.* `charlie.Knows` and
   `+charlie.Knows` are the sound Contacts: Contact and Pair both sound
   (STEP-22 rule 7.3). `~charlie.Knows` holds a Contact whose contract or
   Pair is broken; `charlie.Knows[:]` every Contact. Places and `del X[:]`
   work as anywhere: `charlie.Knows[0]`, `del (~charlie.Knows)[:]`.
2. **The dot on a Link reads the Link.** *Recommended.*
   `charlie.Knows.since` is an `AttributeError` naming
   `(+charlie.Knows).since`, which reads the sound Pairs;
   `(+charlie.Knows).since = 2011` writes them (STEP-25 section 5).
3. **A name both the Pair and the Contact hold is refused at the walk.**
   *Recommended.* The answer never changes in silence (STEP-23 open
   question 1).
4. **`Social.Knows` is always the Relation.** *Recommended.* Who knows
   Ruth is `(+Social).Knows[:] == ruth`. A combination of Links sees no
   Link (STEP-23 rule 1.5).

## What this replaces

Lines are on S19 and PR #28 where named, and on this branch otherwise.
Files are under `steps/spec/` unless named.

| Where | What changes |
| --- | --- |
| STEP-13 (S19) `STEP-SPEC-13-field-algebra.md:35-38` (item 1) | The populations gain `+Tag` and the parts of every root. |
| STEP-13 (S19) `:50-52` (item 4), `:138`; `:79-85` (item 6) | `~` on a combination stays refused, for rule 4.2's reason; item 6 is a `TagCategoryError` (Decided). |
| STEP-19 (S19) `STEP-SPEC-19-in-answers-for-sound-members.md:67-78`; `:70-71`, `:199-200`, `:136-137`, `:287-291` | Items 1 and 2 stand (Decided). "unless the host ... gives the Agent its own `__bool__`" goes, and so does item 7's text on it; Decision question 3 is answered. |
| STEP-19 (S19) `:226` | The rejected `agent in +Wizard` now works; the Guide does not teach it. |
| STEP-18 (S19) `STEP-SPEC-18-deletion-in-layers.md:433` | Stays true: the safehouse is `Tag[...]`. `+Tag` is the sound part; `-Tag` is refused. |
| `spec/SPECIFICATION.md:1062` (S19 `:1110`) | "no universe" goes; rule 4.2 replaces it. |
| `spec/SPECIFICATION.md:264`, `:1047`, `:1051-1053`, `:1086-1088` | `in` is sound membership (as on S19); a host's own `__bool__` is refused. |
| STEP-22 `STEP-SPEC-22-links.md:485-488` (rule 6.5); `:614-627` | `(+Social).Knows[:] == ruth`, `(+Social).Knows == link`; "With STEP-SPEC-23" goes. |
| STEP-23 `STEP-SPEC-23-field-filters.md:16-47`; `:125-169` (rules 1.1 to 1.3) | Every root becomes `(+Wizard)`, `(+charlie.Knows)` or `(+Social)`. Rule 1.1 becomes rules 1.1 and 1.2 here; rule 1.2 adds the parts; rule 1.3 goes. |
| STEP-23 `:175-201`, `:239-247` (rules 1.5, 1.6, 1.8) | `(+charlie.Knows).since`, `(+Rare).rarity`; a shared name is refused; `P[n]`, `P[True]` refused. |
| STEP-23 `:170-174` (rule 1.4) | A population takes a write (rule 2.4, with STEP-25). |
| STEP-28 `STEP-SPEC-28-category-error.md` (rule 2) | The message for `Wizard.hp = 10` names `(+Wizard).hp = 10` beside the loop. |
| STEP-23 `:291-297`, `:327-375`; `:429-433`, `:456`, `:458`, `:466-510` | `(+Enemy).Take_Damage(5)`; add `f[0]`, `next(iter(f), None)`, `[w] = f`; `Wizard.hp = 10` names `(+Wizard).hp = 10`. The `hasattr` item goes; `(+Wizard).level` adopted; masks stay set aside (rule 5.2); open questions 1 and 2 answered. |
| STEP-24 `STEP-SPEC-24-field-rip.md:123-139` (rule 1.7), `:381-382` | `weak = (+Wizard).level < 3`, then `del weak[:]`; the home; `del Wizard[...][:]` refused. |
| STEP-25 (PR #28) `STEP-SPEC-25-commands-to-a-population.md:39`, `:148-157` | `(Enemy[:] & Enemy)` becomes `(+Enemy)`. |
| STEP-25 (PR #28) `:312-346` (rule 4.2); `:370-384`, `:403-405` (rules 5.1, 5.4) | A `TagCategoryError` naming `(+Enemy).hp = 10`; the sound Pairs' root is `(+charlie.Knows)`. |
| STEP-25 (PR #28) `:433-469` (rules 6.3, 6.4) | The admitted trap goes: `Enemy.Take_Damage(5)` is refused at the dot. |
| STEP-25 (PR #28) `:470-486`, `:639-641`, `:661-666` | Rule 6.5's skip is Decided; question 1's second part dissolves; question 4 closes with `+Enemy`. |

**The catalog** (`steps/CATALOG-tag-algebra.md`) already shows this
STEP's rows beside today's, each marked Brief. If this STEP is adopted,
those rows take the status the Director sets.

## Rationale

**Why `+`.** He offered it: "+Wizard, -Wizard should be... A short
spelling for the sound members, or for the safehouse. That is sound for
filters." Beside "~means bad", `+` reads "good". In Python's
`collections.Counter`, `+c` keeps the positive part, and `+(+c) == +c`.
`+X` reads soundness directly, so it does not wait on STEP-28 open
question 2. Its cost is round brackets before a dot (rule 1.4); the
Guide's style removes the nesting, and every slip but one is loud.

**Why not `[True]`.** He read it two ways: a pick ("Just give me a true
one"; "should return any one sound wizard?") and a population
("myTag[True] and myTag[False] could be the populations"). Python reads
`seq[True]` as `seq[1]` (`['a', 'b', 'c'][True]` is `'b'`), so with
places `Wizard[True].hp = 1` and `Wizard[1].hp = 1` would both run, on
different Agents. A refused key can gain a meaning later.

**Why `~` absorbs.** His proposal, pending his answer (open question
7). TOP's `~` was never "not": the
Specification gives a union "no universe" (`spec/SPECIFICATION.md:1062`),
and the flip is the kit's alone. With two parts the laws are short:
`+X | ~X` is everyone, `+X & ~X` nobody, each sign absorbs.

**Why no `+` or `~` on a combination.** Otherwise one `[:]` changes the
answer in silence: in the design panel's bracket toy,
`~(Wizard[:] | Fighter)` dropped a broken Fighter that
`~(Wizard[:] | Fighter[:])` kept. One part per Tag has no switch.

**Why places.** "Numbers have order", in join order, as every walk. No
Agent can be an `int` (STEP-28 rule 3), so a place never meets a view.

## Backwards compatibility

Against this branch's kit (main's, TopKit 0.2.0a4):
1. `~~Wizard` was the sound members; it is the broken ones.
2. `ari in Wizard` was membership; it is sound membership (as on S19).
3. A host with its own `__bool__` was tagged, and its truth answered for
   the Agent (`TopKit/access.py:107`); it is refused.
4. `Rare | Wizard` mixed Tags and Agents; it is refused.
5. `Wizard.spells` (a declared Record) gave the raw function; it is an
   `AttributeError`, and `hasattr` turns False.
6. `+Wizard`, `~Wizard[:]` and `Wizard[:][0]` were `TypeError`s; `Wizard[0]`
   and `Wizard[...]` were `TagResolutionError`s. They are now the parts,
   places and the safehouse. `-Wizard`, `~(Wizard | Fighter)` and
   `Wizard[True]` are refused as a `TagCategoryError`, a `TypeError`.
7. A `for` walk visited a member an earlier turn Ripped; it skips it.
8. `del Wizard[:]` and `del (~Wizard)[:]` were errors; they Rip.

To migrate: write `ari in Wizard[:]` for plain membership, keep a host's
truth in a Record, and write `+Wizard` before a dot.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| `Wizard[]`; `Wizard[*]` | Not Python: SyntaxError ("invalid syntax"; "Invalid star expression"). Their jobs are `+Wizard` and `Wizard[0]`. |
| `Wizard[::]` as a new spelling | Not free: the same key as `Wizard[:]`. |
| `[Wizard]`, `[~Wizard]`, `[Wizard[:]]` for "any one" | A plain Python list holding the Tag; no hook can make it a pick. |
| `Wizard[Sound]` | Rejected by the Director: "Wizard[Sound] looks horrible. It takes over programmer's choices, not language options. Skip." |
| `Wizard[()]` | One shape from `Wizard[0]`; both writes would run silently. |
| `Wizard[True]`, `Wizard[False]` as the parts (the bracket and minimal designs), or as a pick | `True` is `1` to Python, and the author read it two ways. As a pick, `Wizard[True].level > 3` is a bool about one Agent, not a search. |
| `myTag[<mask>]`, `Wizard[:<mask>:]` | The Filter already is the masked population; `[:mask:]` is the slice `[:mask]`. |
| A `with` mask, `w for Wizard with w.level > 3` | Not Python. Python's mask is `if` in a comprehension. |
| `-Wizard` for the safehouse | The safehouse is `Wizard[...]` (decided); `-` stays the binary "not". |
| `~~X` as the sound members | Against his proposal, "~~= ~" (open question 7). |
| `~` on a combination, with a universe | A hidden switch (Rationale). |
| No places at all (the minimal design) | Against "Numbers have order". |
| `X[Only]`, `X[Anyone]`, `P[True]` | New names and keys; `[w] = X`, `next(iter(X), None)` and `P == True` say it. |
| `Wizard["level"]`, `Each(Wizard).level`, `Where(Wizard, ...)` | A key naming an attribute; functions where TOP uses the language. |
| `Wizard.level` as a Projection; `(Wizard[:] & Wizard).colour` | Rejected by the Director: "Wizard.level is a report"; "I refuse that monstrosity with redundant information". |
| `while Enemy:` as a round robin; `itertools.cycle(Enemy)` | Python fixes `while`; `cycle` replays its first lap. |

## Open questions for the Director

1. **`rounds`: a Guide recipe or a kit name?** Recommended: the Guide;
   five lines of plain Python.
2. **"the first ever WIzard": `Wizard[0]` (the oldest sound one) or
   `Wizard[:][0]` (the oldest of everyone)?** Closed on 2026-10-09: a
   plain Tag has no places (the note at section 6).
3. **`del Wizard[...][:]`** stays refused until STEP-24 open question 1
   settles whether kept Agents are still members.
4. **Should `P == True` refuse a value that is not a bool?** Recommended:
   not now; the Guide names the `level == True` trap.
5. **A host with `__len__`** (STEP-28 open question 2). Recommended: your
   "(Or at least underlayed by the contracts)": truth is the contract.
6. **"Anyone?"** stays `len(f) > 0` until you come back to it.
7. **Does `~` absorb?** (rule 3.2) **Decided by the Director on 2026-10-09:** yes, "~~~~~~~~~~~~~Wizard
   is still ~Wizards".
8. **Is `+Wizard` a list?** **Decided by the Director on 2026-10-09:** (b). "+Wizard stays a live
   group for masks and such. not fixing them. I settled on an easy call
   to list is enough for what I was thinking earlier." The Guide teaches
   `list(...)` as the step into a list. Still open: whether `X[True]`
   picks one member ("w = (+Wizard)[True] one valid wizard, any one"),
   and whether a Filter has places (`veterans[0]`).

   The question as it was asked. The Director proposed it on 2026-10-09: the
   bare Tag refuses number keys, "but +Wizard would, as it returns a
   list". Two answers:
   - **(a) `+Wizard` is a list:** the sound members, copied at that
     moment, with places. `(+Wizard)[0]` works.
   - **(b) `+Wizard` stays a live group, and lists are Python's:**
     `list(Wizard)[0]`, or `[*Wizard][0]` without a call. `+` keeps one
     job, "the sound part", and stays the partner of `~`.

   Recommended: (b). Under (a), `+` would do two jobs, choose the sound
   members and freeze them, and `+X` and `~X` would stop being a pair.
   Masks show the risk most clearly: on a plain Python list, `del
   weak[:]` only empties the list and Rips nobody (checked), so a mask
   that gave a plain list would silently undo the decided rule 8.1.

## Acceptance requirements

- `tests/test_topkit.py`: a `PopulationAlgebraTests` class covering every
  row of the Summary's table on a full and an empty cast, and: the laws
  on each kind of root; places (live, `-1`, a bool key refused, an object
  with `__index__` still read as an Agent); each refusal changes nothing;
  `del X[:]` read once; the walk's skip; the Guide's `rounds`.
- TopKit: MetaTag (`TopKit/tags.py:51`) gains `__pos__`, a refusing
  `__neg__`, and a dot that refuses Agent names; Records and Actions are
  plain class functions today, so a `__getattr__` alone cannot. At
  `TopKit/tags.py:161` and `TopKit/fields.py:385`, `~` absorbs.
  `TopKit/tags.py:212` gains the bool refusal, `int` places and `...`.
  Every population gains `[:]`, `[n]` and `del X[:]`.
- `tests/oracle_topkit.py`: parts, places, `del X[:]`. The Guide: its
  "name the group, then act" style, rule 1.4's habit, and `rounds`.

Built on PR #26 on 2026-10-09: rule 7.1, the walk's skip, on every walk
the kit offers (a Tag, `Wizard[:]`, `~Wizard`, a Pin, a combination),
with `WalkTests`. The Recommended half of 7.1 is not built as a general
rule: an Agent that joins a Field during its walk waits for the next one,
as before, but `&` and `-` still ask their right side at each turn, so
one that joins `Wizard & Fighter` through Fighter is met in the same
walk. The refusals of rules 2.3 (a host with its own `__bool__`) and 4.3
(`Rare | Wizard`) were built with STEP-SPEC-28.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Decided by the Director on 2026-10-08 and 2026-10-09, ahead of this
> STEP:* every rule marked Decided, with his words at the rule (rules
> 1.1, 1.3, 2.1, 2.3, 3.5, 4.3, 5.1, 5.3, 5.4, 7.1, 8.1),
> and the rejection of `Wizard[Sound]` (Alternatives). The Status stays
> Brief until he has read this text and answered the open questions.
