# STEP-SPEC-36: Tools

- **STEP:** SPEC-36
- **Desk:** spec
- **Title:** Tools: a Record whose value is an Agent
- **Author:** Julio Toboso (@JulTob); drafted with Claude Code from the
  Director's brief of 2026-10-12
- **Status:** Vetting
- **Created:** 2026-10-12
- **Refs:** issue #74 (dunder-named conditions), PR #58 (Tags recognised
  by metaclass), STEP-SPEC-22 (Links, Brief), STEP-SPEC-33 (Presence),
  STEP-SPEC-34 (Constant), STEP-SPEC-29 (Brief; the meaning of `in`),
  issue #30 and STEP-SPEC-39 (Tagging Admission, Cleared, PR #78: the
  sequence this STEP's failure outcomes follow once it lands)

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A **Tool** is an object an Agent *has*: a Record whose value is an Agent
in its own right, with its own Tags, Field, contract, keywords and
secrets. The vocabulary is the third verb of a triad the Specification
already uses two of: a Tag is what you **are** (*ser*, §0.2), a Record is
what you are **currently** (*estar*, §1.3), a Tool is what you **have**
(*tener*).

```python
class Fighter(Tag):

    @Tool(Weapon)                       # a Record whose slot holds a Weapon
    def weapon(agent):
        sword = Sword(f"{agent.name}'s sword")
        Weapon(sword)                   # the forge Tags it, in plain sight
        return sword


Fighter(charlie)
charlie.weapon.Swing()                  # a use of the tool: the sword's own Action
Cursed(charlie.weapon)                  # the curse is the sword's, never Charlie's
```

Everything a Tool *is* already follows from laws on `main`: identity
(§0.1), Records (§1.3), the composition door (§1.5) and contract truth
(§2.5). A hand-written Record whose builder Tags its value gives the whole
behaviour today, and the wiki page `1.4 TopKit: Tools` teaches that
pattern with blocks that run on `main`.

This STEP proposes **one kit addition**, the mark `@Tool(T, ...)` on a
Record builder, with **three laws**, and nothing else new:

1. **The slot has a kind, checked at admission.** A Tool slot admits only
   an object that is *now* a member of every Tag named, sound or
   defective, and is not the bearer. The kit checks this when the slot is
   gained (step 2 of §0.6) and at every write to the slot. A refused write
   changes nothing; a refused gaining is that step's failure under §0.6.
   After admission, presence, membership and soundness stay three
   separate questions.
2. **The slot is never empty, unless its kind says so.** `None` is
   refused, except where the declaration writes it: `@Tool(Weapon | None)`
   admits the empty hand explicitly. `del agent.weapon` is always the
   drop. With the default, `"weapon" @ agent` answers "armed?".
3. **The slot never Tags.** The kit applies no Tag to what the builder
   returns or to what is assigned. The forge Tags the object in plain
   sight, and that tagging keeps its own call boundary.

Nothing lands on the bearer. The barrier, the two doors, one direction,
truth, presence, Rip and deletion are all restated from the Specification,
with their sections.

## Motivation

Domains hold things: a character has a weapon, a drone has a battery, an
account has a key, a ship has a cargo. The thing has a being of its own.
A sword can be *Cursed* without its bearer being cursed; a battery can be
*Depleted* while the drone is sound; the thing can change hands, and its
Tags must travel with it, because Tags live on the object (§0.1).

### What works today

On `main` at `082092e` (2026-10-12), a Record whose builder returns a
Tagged object already gives, verified:

- the held object is an Agent of `Weapon`; the bearer is not;
- the held object acts on its own, with its own Overlay: `Cursed` over
  `Weapon.Swing` changes the sword's `Swing`, not the bearer's anything;
- membership, keywords (`Keyword(charlie, "Cursed")` is `False`),
  contract and truth stay on the sword;
- the sword's secrets fail closed from the bearer's Actions (two doors);
- a bearer's own Post can require the slot to hold a Weapon, and judge
  its soundness with `Contract.Holds(agent.weapon)`;
- hand-over is assignment and the Tags travel with the object;
- Rip of the bearer leaves the slot, sticky, as any Record (§0.7);
- a failing tagging inside the builder refuses Parts and rolls the
  bearer's call back under the failure's own name
  (`except Precondition.Blessed_Steel:` works at `Fighter(charlie)`).

### Where the pattern lies

Four things a reader of `Fighter` will assume and the kit does not keep.
Each was reproduced on `main`:

| # | Found | Why it matters |
| --- | --- | --- |
| 1 | **A stick is seated in silence.** `charlie.weapon = "a stick"` is accepted; the bearer turns defective only when a Post is next read, at a boundary or at `bool(charlie)`. | §2.4 is right that conditions never check themselves during play. But a declaration that *says* what the slot holds should refuse what it cannot hold, at the write, with nothing changed: the move §2.5 made for condition names and §1.8 for the `in` seat. |
| 2 | **`None` is a held nothing.** STEP-SPEC-33 counts `None` as present, so `"weapon" @ charlie` is `True` with nothing in hand, and "armed?" needs two questions. | §2.8 asks to keep "is it there?" apart from "what is its value?". A slot that is never `None` keeps presence meaningful; an author who wants an empty hand says so in the kind, `Weapon | None`, instead of every reader assuming it. |
| 3 | **The bearer can be its own tool.** `charlie.weapon = charlie` is accepted. | The barrier is void by identity; the two contracts fold onto one object. *Tener* and *ser* are different verbs. |
| 4 | **The forge's tagging outlives the bearer's failure.** A tool Tagged inside a builder stays Tagged when a later gaining of the same call fails. On `main` today the whole call rolls back, so a sword forged in the builder is held by nothing and collected (§0.3). Under the approved sequence (issue #30, STEP-SPEC-39, PR #78) the bearer keeps the sword as an acquired Gain and stands outside the Tag's Field, a Rogue. | In either sequence a pre-existing object handed in keeps the Tag the forge applied, and Rip is not restoration (§0.7). The STEP says so where readers look instead of promising an undo. |

Findings 1 to 3 are what law 1 and law 2 refuse. Finding 4 is **not**
closed by this STEP: the honest answer is that the tool's tagging is a
nested call with its own §0.6 boundary (law 3), and the STEP says so
where readers look. Open question 2 puts the alternative, an undo, to the
Director. The failure outcomes in this STEP are restated from §0.6 and
follow it: on `main` today that is the whole-call rollback; once PR #78
lands it is STEP-SPEC-39's sequence, Gate, Gainings, Imprints,
FieldAdding, Posts, in which a failure before FieldAdding keeps the Gains
already acquired and leaves the Agent outside the Tag's Field.

### Issue #74, and where a part's truth lives

Issue #74 asks whether a condition may take a dunder name such as
`__bool__`. The Director's position is to refuse it, and to put boolean
information in conditions, Records, Actions, "or even record-objects that
have their own bool method". A Tool is that record-object. The sword's
truth is the sword's own contract: `if charlie.weapon:` asks whether the
sword's promises hold (§2.5). It never becomes a dunder on Charlie, and a
bearer that needs a sound tool says so in an ordinary, named Post.

## Specification

In this STEP, § cites the Specification. The STEP's own parts are cited
as "law N" or "rule N.M".

### 1. Vocabulary

Rows for §0.2:

| Term | Meaning |
| --- | --- |
| **Tool** | An object an Agent has, held under a name, that is an Agent of the Tags its declaration names. Something you *have* (*tener*), beside a Tag (*ser*) and a Record (*estar*). |
| **Bearer** | The Agent that holds a Tool: the receiver of the Tool's Record. Charlie is the bearer of `charlie.weapon`. "Owner" stays a domain word, as it does for Links. |
| **Kind** (of a Tool slot) | The Tag or Tags a slot requires of what it holds, named in the declaration: `@Tool(Weapon)`. |
| **Use** (of a Tool) | An Action of the Tool, called through the slot: `charlie.weapon.Swing()`. The receiver is the Tool. |

The slot itself is §1.1's word: the `(Agent, name)` slot that holds the
Tool. This STEP does not add a third meaning to "seat", which the
Specification uses for parameter positions and for `in`.

A row for §0.8:

| Act | Python spelling |
| --- | --- |
| what the Agent has | `@Tool(Weapon)` on a builder; use it through the slot, `charlie.weapon.Swing()`; hand it over by assignment; drop it with `del charlie.weapon` |

### 2. The mark

1. `@Tool(T1, ..., Tn)` marks a Record builder and names what its slot
   holds: one or more Tags, in no particular order; the slot holds a
   member of **all** of them. It stacks with `@Constant`, `@Secret` and
   `@Public` in either order, as the modifiers of §1.5 and STEP-SPEC-34
   do.
   - **An emptiable slot is written `@Tool(Weapon | None)`.** `Weapon |
     None` is the language's own class union (§2.5: "A Tag with anything
     that is not a population keeps the language's own class union"), so
     the kind is spelled as Python spells an optional type, and the kit
     reads the Tags and the `None` from it. Explicit `None` beats an
     implied one.
   - **A population is not a kind.** `Weapon | Blessed` is the Field
     algebra's "sound in either" (§2.5), `~Weapon` and `Weapon[:]` are
     populations too; any of them as an argument is a Declaration Failure
     whose message shows the spelling meant: `@Tool(Weapon, Blessed)` for
     both, `@Tool(Weapon | None)` for an empty hand.
2. `@Tool(...)` alone declares the Record. STEP-SPEC-34 rule 1 keeps an
   unqualified method an Action under `@Constant` because Constant can
   mark five kinds, so the kind must be said; a Tool can be one kind
   only, so writing `@Record` as well says nothing new. It is accepted as
   a restatement, as `@Public @Record` is (§1.5). `@Tool` over an Action,
   Report, Operation, condition, Imprint, Rip or Delete is a Declaration
   Failure at class use: a Tool is something the Agent *has*; those are
   things it does, shares or promises.
3. Each `Ti` is a Tag **recognised by its metaclass**, the way PR #58
   recognises a Tag in the Field algebra (`isinstance(Ti, MetaTag)`, the
   root `Tag` excluded; on today's `main`, `geometry._is_tag`). A plain
   class, an instance, the root `Tag`, a Pin (§1.9: a Pin's Agents are
   Tags, and "Fields never mix Agents and Tags") or, when Links exist, a
   Relation or a held Link, is a Declaration Failure at class use.
4. `@Tool` inside a `@Pin` is a Declaration Failure: a Pin's Record lands
   as a Report of the pinned Tag (§1.9), one value on the Tag, which is
   Tag-scope having and its own topic (open question 6).
5. The builder is a Record builder in full (§1.3): the three seats, the
   bearer, the stored value and the inputs by name after `*`; piling up
   through the stored seat; a replacement of an independent Tag's Record
   diagnosed; and every collision rule of §1.1, §2.5 and Ring 4. Nothing
   in the builder's own contract changes.

### 3. The three laws

**Law 1. The slot has a kind, checked at admission.** A Tool slot admits
only an object that is *now* a member of every Tag of its kind and is not
the bearer. Admission is asked twice: when the slot is gained, and at
every write. After admission, three questions stay separate: presence
(`"weapon" @ agent`), current membership (`agent.weapon in Weapon[:]`)
and soundness (`Contract.Holds(agent.weapon)`).

- *Member* means membership at all: `value in T[:]`, sound or defective.
  The guard asks membership, never soundness; a cursed or broken sword
  may be seated, and the bearer's own Post judges it. The check is spelled
  against `T[:]` because STEP-SPEC-29 (Brief) proposes that `value in T`
  mean sound membership; this law must not change meaning if that lands.
- Membership is closed upward (§0.3), so an Agent of a Shape of `T` passes
  the guard for `T`.
- The check runs **at the slot's gaining** (step 2 of §0.6), on what the
  builder returns. A refusal is a Composition Failure of that step and the
  slot is not written. What that means for the rest of the call is §0.6's
  rule, not this STEP's: on `main` today the whole call rolls back; under
  STEP-SPEC-39 (Cleared, PR #78) the bearer keeps the Gains it already
  acquired and does not enter the Tag's Field.
- The check runs **at every write** to the slot, `object.__setattr__`
  included, the path STEP-SPEC-34 already intercepts: a refusal is a
  Composition Failure and the slot is unchanged.
- Admission is a **gate**: asked at the write, never re-asked (§2.2). A
  seated tool that later leaves its Tag (`del Weapon[sword]`) stays
  seated, a Rogue in hand: presence stays `True`, `charlie.weapon in
  Weapon[:]` turns `False`, and the bearer's Post notices at its next
  boundary or read (§2.4). Such a Rogue is refused if moved to another
  slot.
- The bearer itself is refused at Parts and at the write. A Tool is
  something the Agent has, never the Agent; to make Charlie a Weapon, Tag
  him: `Weapon(charlie)`. This departs from STEP-SPEC-22, which leaves a
  self-link to the author's Pre (rule 8.5), because a Link is a relation
  and knowing oneself is a sentence, while a self-tool voids the barrier
  by identity.

**Law 2. The slot is never empty, unless its kind says so.** With a kind
of Tags alone, a builder that returns `None`, or an assignment of `None`,
is a Composition Failure (Parts refused and the call rolled back; or
nothing changed), and `"weapon" @ agent` answers "armed?" with one
question (STEP-SPEC-33). With a kind written `Weapon | None`, `None` is
admitted at Parts and at the write: the empty hand is declared, so a
reader of `Fighter` knows the slot may be empty and writes
`agent.weapon is not None` where it matters; presence then says only
that the slot exists. In both cases the drop is `del agent.weapon`, the
language's own deletion of a Record (§1.3), and `@Delete` at the name
frees the slot (§1.6) and so drops the tool. Both are refused on a
Constant slot (§1.5).

**Law 3. The slot never Tags.** The kit applies no Tag to what the
builder returns and none to what is assigned. The forge Tags the object
in plain sight, `Weapon(sword)`, or receives one already Tagged. A
tagging the builder performs is an ordinary call on another Target with
its own §0.6 boundary, and what its failure means for the bearer is the
bearer's own §0.6 rule for a failure inside a Record builder:

- the tool's gate or Parts failure leaves the tool untouched and
  propagates under its own name (`except Precondition.Is_Holy:` works at
  `Fighter(charlie)`, as today); for the bearer it is a failure of the
  slot's gaining;
- the tool's Write or Quality failure leaves the tool Tagged, and
  defective if a promise broke (§0.6: "the Tags stay"); for the bearer,
  the same;
- when a later gaining of the bearer's call fails, the forged tool keeps
  its Tags. On `main` today the whole call rolls back, so a sword forged
  in the builder is held by nothing and is collected, "vanishing from
  every Field" (§0.3). Under STEP-SPEC-39 (Cleared, PR #78) the bearer
  keeps the sword as an acquired Gain and stands outside the Tag's Field.
  A pre-existing object handed in keeps the Tag the forge applied in
  either sequence. Rip is not restoration (§0.7, Contributions are
  sticky), so this STEP offers no cleanup recipe inside the forge: a
  forge's `except` cannot see a later gaining's failure, and a Rip of a
  Tag the object never joined would raise a Resolution Failure that masks
  the named refusal. A caller that must not leave such a Tag behind
  compensates on its own side, tracking what the call gained, and keeps
  the primary failure primary:

  ```python
  was_a_weapon = sword in Weapon[:]
  try:
      Fighter(charlie, weapon=sword)
  except TagError:
      if not was_a_weapon and sword in Weapon[:]:
          del Weapon[sword]           # the forge's act, undone by the same kind of act
      raise
  ```

### 4. Restated, with their sections

None of the following is new law. Each is what the Specification already
says, applied to a Record whose value is an Agent.

4.1 **The barrier.** A Tool is a Target of its own. Nothing it is reaches
its bearer: not membership (§0.3, "Fields are indexed by identity";
`charlie in Weapon` is `False`), not keywords (§1.8: a word is on the
Agent that carries the Flag; the bearer-side question is
`Keyword(charlie, "Cursed")`, because `"Cursed" in charlie` reads the
host's own `in` and raises on a host with no Flag), not its contract or
truth (§2.5: each Agent is truthy exactly when its own visible
Postconditions hold), not its published members (§1.5: "members only"),
not its secrets.

4.2 **Two doors, as §1.5 already opens them.** Inside composition means
"while an Action, Imprint, Record builder, condition, or Rip protocol
bound to **this** Agent is running" (§1.5). A door belongs to one Agent
and stays open for as long as that Agent's own function runs. So reading
`agent.weapon.combination` from a bearer's Action fails closed, because
the sword's door is shut, while `agent.weapon.Open()` resolves it inside
the sword's own Action. In the other direction the same rule, and no
more: a tool's Action called from *outside* the bearer's functions cannot
read the bearer's secrets; a tool's Action the bearer calls from *inside*
its own Action, handing itself over (`agent.weapon.Swing(agent)`), runs
while the bearer's door is open and can read them through that
reference, as any callback can. Both verified on `main`. This STEP adds
no isolation between nested receivers; that would be a separate design
change to §1.5. The forge, a Record builder bound to the bearer, runs
inside the bearer's door and outside the tool's. A `@Secret` Tool slot is
the bearer's secret: the name resolves inside the bearer's functions
only; the tool object is an ordinary Agent to anyone holding a reference
to it. Links differ on purpose: their functions open the Link's Agent's
door and the Pair's (STEP-SPEC-22 rule 3.6); a Tool has no Pair.

4.3 **One direction, written back on purpose.** The kit writes nothing of
the bearer on the tool and keeps no reference, weak or strong, from a
tool to any bearer; a tool never keeps its bearer alive. The tool's
functions receive the tool in their one seat, `def Swing(tool)`; a use
that needs the bearer takes it as an argument, `agent.weapon.Swing(agent)`.
No spelling walks from a tool to the slots that hold it; the search is
from the bearers' Tag, which the searcher must name:
`[f for f in Fighter[:] if "weapon" @ f and f.weapon is sword]`. A tool
that knows its bearer is the author's visible line (an attribute set in
the forge, an Imprint, or a Link), as STEP-SPEC-22 rule 6.4 writes two
ways down; the author then owns the cycle it makes.

4.4 **Truth and presence.** `bool(charlie.weapon)` is the sword's own
contract once a Postcondition is visible on it (§2.5), unless the host
defines its own `__bool__`: on `main` today the kit never replaces a
host's `__bool__`, so it stays authoritative even while a Post fails
(verified: `bool(agent)` `True` with `Contract.Holds(agent)` `False`);
#71 and #72 settle that rule. So the spelled-out form to teach inside a
Post is `Contract.Holds(agent.weapon)`, which asks the contract whatever
the host says. Conditions on
the tool are written with `return`, not `assert`, so they still hold
under `python -O` (§2.1 and the Guide's note on optimized Python).
`"weapon" @ charlie` is presence and never evaluates the tool's contract
(STEP-SPEC-33). `for w in Weapon` walks swords, never bearers. A bearer
that needs a sound tool says so in a named Post, read at its own
boundaries and on `bool(charlie)`, never continuously (§2.4):

```python
@Post
def Armed(agent):
    if agent not in Fighter:            # the promise ends with the Tag (§0.7, STEP-SPEC-12)
        return True
    return ("weapon" @ agent
            and agent.weapon in Weapon[:]
            and Contract.Holds(agent.weapon))
```

4.5 **Lifecycle.** Rip of the bearer's Tag leaves the slot and its tool
with the Rogue (§0.7, "Contributions are sticky"); its conditions are
sticky too (STEP-SPEC-12), so a Post about the tool carries a membership
guard or is ended in the Tag's `@Rip` with `Contract.Delete`. A Tag that
must disarm on leaving says so in its `@Rip`: `del agent.weapon`. Rip of
the tool's own Tag never reaches the slot (§0.7, "Rip never cascades").
Deletion of the bearer runs the bearer's teardowns and `__del__` Layers
(§3.2); the slot ends with the bearer's namespace; nothing is Ripped from
the tool, which lives on wherever else it is held. **A slot holds its tool
strongly, as a Record holds its value, which a Field never does (§0.3).**
This is the line that separates a Tool from a Link, whose Agent's deletion
ends it (STEP-SPEC-22 rule 8.3): a Link belongs to its Agent; a Tool
outlives its bearer, as Excalibur outlives Arthur. Reapplying the
bearer's Tag after Rip rebuilds an ordinary slot (the stored seat receives
the sticky tool, so `return forge(agent) if stored is None else stored`
keeps it; never `stored or forge(agent)`, because a defective tool is
falsy and `or` would forge its replacement) and keeps a Constant one
without running its builder (STEP-SPEC-34 rule 7).

4.6 **Overlay on a Tool slot.** The latest applied Layer is the visible
declaration for the name (§1.2). A Shape that redeclares the name as a
Tool receives the held tool in its stored seat and guards with **its own
kind list**; the wiki teaches "say everything the slot holds", because
`@Tool(Blessed)` alone would admit a Blessed non-Weapon. **A Tool slot
stays a Tool slot**: a plain Record or an Action at that name, from a
Shape or an independent Tag, is a Composition Failure that names the
slot and the two ways out, "redeclare it with `@Tool(...)`, or free it
with `@Delete`". This is the one amendment to §1.1 this STEP makes, for
Tool slots only (open question 12, implemented as recommended): a thing
one has needs one identity, and the guard must never go away in silence.
The refusal comes before any Overwrite Warning, so no warning describes
a replacement that did not happen. `@Delete` frees the slot for any
later declaration; a Tool over a plain Record takes the slot and guards
it from then on. `@Underlay` has no meaning on a Record; a Tool extends
through the stored seat. A Constant slot refuses all of it (§1.5).

4.7 **Constant, Secret, Public.** `@Constant @Tool(Weapon)` is a
**bonded** tool: the binding cannot be replaced or deleted, so it is never
handed over or dropped, and it survives Rip; the tool's value and the
tool's own Tags may still change (STEP-SPEC-34 rules 2, 5 and 7). `@Secret`
hides the slot outside the bearer's door. `@Public` restates the default.

4.8 **Hand-over, aliasing, copying.** `bob.weapon = charlie.weapon;
del charlie.weapon` is a hand-over: two visible lines, no move primitive.
Two slots may hold one tool; the kit tracks no bearers, and exclusivity,
when the domain wants it, is a Post on the bearer or a Pre on the tool's
Tag. `copy.copy(charlie.weapon)` is refused (Ring 4); duplicating a tool
is domain work: build a new Target and apply `Tags(sword)` again. The
Agent-bound view `Fighter[charlie].weapon` holds the reference captured at
that Tag's Commit (§1.7); a later hand-over changes the live slot and not
the view, as for any Record value.

4.9 **Shared tools, inventories, searches.** One tool for the whole Field
is a Report whose builder Tags its value (§1.4, "Shared values belong in a
Report"); it works today, unkinded, and a kinded Report is open question
6. Many tools held with a gate and a drop protocol are a Link whose
Contacts are tools (STEP-SPEC-22), with the caveat that a Field never
keeps an Agent alive (§0.3), so an inventory Link does not own its items.
Under STEP-SPEC-23, `Fighter[:].weapon` is a Projection of tools and
`Fighter[:].weapon == sword` finds bearers; Tools add no rule there, and
STEP-SPEC-22's open question 2 (is naming the declaring Tag explicit
enough?) should get one answer for both.

### 5. Refusals

| When | Kind | Message |
| --- | --- | --- |
| class use: `@Tool()` | Declaration Failure | `@Tool names what the held thing is: @Tool(Weapon)` |
| class use: `@Tool(Sword)`, not a Tag (a plain class, an instance, the root `Tag`) | Declaration Failure | `@Tool(Sword): Sword is not a Tag; a Tool slot holds an Agent of a Tag` |
| class use: `@Tool(None)` | Declaration Failure | `@Tool(None): None is not a Tag; a Tool slot holds an Agent of a Tag` |
| class use: `@Tool(Rare)`, a Pin | Declaration Failure | `@Tool(Rare): Rare is a Pin, whose Agents are Tags; a Tool slot holds an object (§1.9)` |
| class use: a population as kind, `@Tool(Weapon \| Blessed)`, `@Tool(~Weapon)`, `@Tool(Weapon[:])` | Declaration Failure | `@Tool: a population is not a kind (a Tag in an operator seat, as in Weapon \| Blessed, ~Weapon or Weapon[:]); write @Tool(Weapon, Blessed) for both, @Tool(Weapon \| None) for an empty hand` |
| class use: `@Tool` over an Action, Report, Operation, condition, Imprint, Rip or Delete | Declaration Failure | `Swing: @Tool declares what the Agent has, a Record; Swing is an Action`; with the marks in the other order, `Fighter.Swing: @Tool declares what the Agent has, a Record; Swing is not one here` |
| class use: `@Tool` on a value, a classmethod or a staticmethod | Declaration Failure | `@Tool declares what the Agent has, a Record: it marks a builder, def weapon(agent)` |
| class use: `@Tool` inside a `@Pin`, or in a Shape of one | Declaration Failure | `Armory.standard: a Pin's Records land as Reports of the pinned Tag; a shared tool is a Report (§1.9)` |
| Parts: builder returned a non-member | Composition Failure, call rolled back | `Fighter.weapon holds a Tool of Weapon; 'a stick' (str) is not a Weapon now. Tag it in the builder, Weapon(...)` |
| Parts: builder returned `None`, kind without `\| None` | Composition Failure, call rolled back | `Fighter.weapon returned None; its slot is never empty: return a Target, drop with del agent.weapon, or declare the empty hand, @Tool(Weapon \| None)` |
| Parts: builder returned the bearer | Composition Failure, call rolled back | `Fighter.weapon: a Tool is something the Agent has, never the Agent; to make it a Weapon, Tag it: Weapon(agent)` |
| Parts: the tool's own tagging failed | the tool's own failure, unchanged | as today: `Precondition.Is_Holy`, `Postcondition.Has_An_Edge`, the tool's Composition Failure |
| write: a non-member | Composition Failure, nothing changed | `Fighter.weapon holds a Tool of Weapon; 'a stick' (str) is not a Weapon now. Tag it first, Weapon(...), or hand over a Weapon` |
| write: a Rogue of the kind | Composition Failure, nothing changed | `Fighter.weapon holds a Tool of Weapon; this Sword left Weapon` |
| write: `None`, kind without `\| None` | Composition Failure, nothing changed | `Fighter.weapon is never empty; drop it with del character.weapon, or declare the empty hand, @Tool(Weapon \| None)` |
| write: the bearer | Composition Failure, nothing changed | `Fighter.weapon: a Tool is something the Agent has, never the Agent; to make it a Weapon, Tag it: Weapon(agent)` |
| write or delete on a Constant slot | Composition Failure | STEP-SPEC-34's existing message |
| step 1: a plain Record or an Action over a Tool slot, from a Shape or an independent Tag (rule 4.6) | Composition Failure, call rolled back | `Smith.weapon: Fighter.weapon is a Tool of Weapon; a Tool slot stays a Tool slot, and an Action cannot take it. Redeclare it with @Tool(...), or free it with @Delete` |
| step 1: a Tool name over a condition's name, a host property or slot, or an independent Tag's Action | Composition Failure, nothing changed | the existing Record refusals of §1.1, §2.5 and Ring 4 |

Not refused, on purpose: two slots holding one tool; a tool that bears
tools (`charlie.weapon.gem in Gem`); a defective or cursed tool seated; a
seated tool Ripped from its Tag (the bearer's Post notices); a Tool whose
Tag is a Shape of the declared one; `None` in a slot whose kind says
`| None`.

### 6. What this STEP refuses to decide

Each is one more law and its own topic: Tag-scope tools (a kinded Report,
a Pin's Tool); Pair-scope tools inside a Relation; exclusivity; a move
primitive; a query from a tool to its bearers; listing Tool slots in
`Outline`; forwarding the bearer's inputs to the tool's tagging.

## Rationale

**A modifier, not a new kind.** STEP-SPEC-34 chose a modifier for
Constant because it "names a semantic property of the Contribution rather
than a new Contribution kind". A Tool is a Record with a kind; the slot
keeps every Record act, `=`, `del`, the stored seat, Constant, Secret.
Nothing in §1.1 or §1.3 is amended. A Tool therefore costs one mark, one
check on the write path the kit already intercepts for Constant, one
check at Parts, two Declaration checks, and no new failure kind.

**The slot never Tags.** The alternative, the kit applying the named Tags
to what the builder returns, reads well but hides a tagging behind a
Record, needs an input-forwarding rule, and raises the undo question
below. "No magic": the forge writes `Weapon(sword)` and a reader sees it.

**No cross-Agent undo.** The orphan (finding 4) could be closed by the kit
restoring the tool's state when the bearer's call rolls back. That is a
new kernel promise: §0.6 restores the Target of the call, and the kit's
call boundary is independent of nested tagging by design. It would be
incomplete, because a forge that Tags with inputs is outside it, and it is
the kind of clever mechanism that is not maintainable. The honest law is
law 3, written where readers look, and open question 2 keeps the door
open for the Director. STEP-SPEC-39 narrows the question further: a
tool forged in the builder is a Gain the bearer keeps, so only a
pre-existing object handed in is affected.

**Explicit `None`, never an implied one.** STEP-SPEC-33 counts `None` as
present, and §2.8 asks to keep "is it there?" apart from "what is its
value?". So the default slot is never `None`: `"weapon" @ charlie` is the
one question "armed?", and `if charlie.weapon:` is one question too, the
sword's truth. An author who wants an empty hand has control over it,
and says so where every reader sees it, in the kind: `@Tool(Weapon |
None)`. That spelling costs nothing new: it is Python's own optional
type, and §2.5 already makes `Weapon | None` a class union rather than a
population. What the STEP refuses is the *implied* possibility, a slot
that may or may not be empty with nothing in the declaration to say
which.

**Membership at all, spelled `T[:]`.** A kind is what the thing *is*, not
whether it keeps its promises. A broken sword is still a sword; the
bearer decides whether to hold one. Spelling the guard against `T[:]`
keeps it stable under STEP-SPEC-29.

**Refusing the self-tool.** A Tool exists to keep two Agents apart: two
Fields, two contracts, two doors. A self-tool folds them onto one object
and makes the barrier a lie by identity. Links allow a self-link because
"Charlie knows Charlie" is a sentence; "Charlie has Charlie" is not.

**A Tool is not a Link.** A Link is a Tag the Agent owns, a category of
others, walked with Ring 0 acts, read-only, ending with its Agent. A Tool
is one object the Agent has, used with the language's attribute acts,
assignable, droppable, held strongly, outliving its bearer. The reduction
"a Tool is a Link whose Field holds one Contact" was weighed: it buys
membership acts nobody wants on a sword and loses the dot. The two share
one vocabulary (one direction, the barrier, granting at Parts,
stickiness) and five stated differences (seats, reassignment, Pair,
doors, ending).

**Tools, Actions and the smith.** `@Tool` never marks an Action, and not
only because an Action is what the Agent *does* rather than *has*. Ring 2
opens with the law: conditions "never wrap an ordinary Action call". A
kind on an Action's return value would be exactly that wrap, a check run
on every call. So a smith is written as what it is, an ordinary Action
that produces a Tagged object, `sword = smith.Forge()`, and the slot that
receives it, `charlie.weapon = sword`, is where the kind is checked. The
two halves keep their meanings: the Action produces, the slot admits. The
danger the Director sensed is real and belongs to the program: every call
forges a new object, a new Agent in `Weapon`'s Field, with no slot to give
it one identity; those nobody holds vanish from the Field (§0.3), those a
list keeps accumulate. Open question 12 asks whether a Tool slot may be
turned into such a smith by a Shape.

**Ser, estar, tener.** The Specification chose two Spanish verbs to keep
Tag and Record apart. The third verb completes the picture a character
sheet needs: what the hero is, what the hero is currently, what the hero
carries. The thing carried has a being of its own, and the curse is the
sword's.

## Backwards compatibility

Opt-in. Unmarked Records keep every current behaviour, and the hand-made
pattern keeps working. A program that marks a slot `@Tool` accepts three
refusals it did not have: a non-member, `None`, and the bearer itself.
`Tool` becomes a public name in TopKit; a program that does
`from TopKit import *` and defines its own `Tool` must rename one of them.
The Specification already uses "tool" for a software tool (§1.9, "a tool
walks every Tag that is Deprecated"); that sentence is reworded when this
STEP is Deployed.

## Alternatives considered

- **A documented pattern and no kit code.** Every rule of this STEP except
  the three laws is a restatement, and the wiki page runs on `main`
  today. This is the Redact path: keep the page, drop the mark. It was set
  aside because findings 1 to 3 are silent acceptances, and the project's
  rule is that a seat never changes meaning in silence; closing them costs
  one small mechanism the kit already has.
- **A cross-Agent undo of the tool's tagging on rollback.** Set aside for
  the reasons in Rationale; kept as open question 2.
- **The kit applies the named Tags at Parts.** Set aside: hidden tagging,
  an inputs rule, and the undo question come with it.
- **A kinded slot species:** `None` always allowed as the empty slot,
  `del` refused, the `(Agent, name)` slot closed to other kinds, as
  STEP-SPEC-22 rules 4.3 and 4.4 do for Links. Set aside: it amends §1.1,
  §1.3 and §1.6 for one modifier, borrowing Link rules whose reason (a
  Link *is* a Tag and ends Contact by Contact) does not hold for a thing
  one has; and an always-possible `None` makes `if charlie.weapon:` two
  questions in one for every slot, where `@Tool(Weapon | None)` makes it
  so only where the author chose it.
- **A nested class as the Tool's declaration** (the Director's
  suggestion): `@Tool` over a class declared inside the Tag, read as "one
  object of this class per Agent, built at Parts, scoped to this Tag".
  It has a real symmetry with Links, where `@Link class Knows(Tag)` is
  "one Tag per Agent, built at Parts": a nested Tag class would be a Link,
  a nested plain class a Tool. It is set aside as the *law* and kept as
  open question 11, for two reasons. First, the kind of a Tool must be a
  Tag: in TOP what a thing *is* is its Tags, and they travel with the
  object across a hand-over; a class is the host's inherent structure
  (§0.1), and making the class the kind would make the slot a nominal
  type. Second, the kit would then construct and Tag the object itself,
  which reopens the inputs rule and the undo question that law 3 avoids.
  The nested class remains a good spelling for the *host* of a tool, as
  sugar over the Record builder, once the one mechanism is law.
- **A Link whose Field holds one Contact.** Set aside: see Rationale.
- **A Pre on a Record,** as the general gain a gated slot would inherit.
  Worth its own STEP; this one names its Tags in the declaration, so the
  guard is the declaration's own content, as a Flag's words are.
- **Tag-scope tools** (a kinded Report, a Pin's Tool), **exclusivity**, a
  **move primitive**, **bearer queries**, **Outline display**: each one
  more law; refused here, listed in section 6.
- **A builder-less spelling,** `weapon = Tool(Weapon)`, for an empty slot
  to fill later. Set aside: one spelling, and a slot is never empty
  unless its kind says so.
- **`@Tool` on an Action,** a kind on the return value, so a smith's
  `Forge` would be checked to produce a Weapon. Set aside: Ring 2 forbids
  wrapping an Action call with a check; the slot that receives the
  product is where the kind is asked (see Rationale).

## Open questions for the Director

1. **Worth its code?** If the three refusals are not worth about one
   hundred and fifty lines plus tests, the pattern stands as written on
   the wiki page and the mark stays here as an alternative.
2. **The forge's tagging of a pre-existing object.** Under STEP-SPEC-39
   a tool forged in the builder is a Gain the bearer keeps, so the old
   "orphan" question narrows to one case: an object handed in keeps the
   Tag the forge applied when a later gaining fails. Law 3 as proposed
   (documented, with caller-side compensation), or a kit undo of the Tags
   the forge applied? Links rule 5.6 undoes a linking made in a
   rolled-back call; a linking is into the Agent's own Link, while
   `Weapon`'s Field belongs to no bearer, so the two need not answer
   alike, but the Director may want them to.
3. **The self-tool.** Refused by law as proposed, or left to the author's
   Post as Links leave `Not_Oneself` to a Pre?
4. **Words.** "Bearer" as the formal word, or "the Tool's Agent" as Links
   say? "Slot" for the place, as §1.1, or "seat"?
5. **A Shape that widens the kind** (`@Tool(Equipment)` over a Base's
   `@Tool(Weapon)`): a silent Overlay, or diagnosed like a weakened Post
   with the Contract Warning (§2.4)?
6. **Tag-scope tools:** a kinded Report, one object the whole Field has,
   and with it a Pin's Tool. A later STEP completing §1.4's grid, or never?
7. **Display.** Should `Outline(charlie)` list Tool slots with the tool's
   Tags (`weapon: Weapon, Cursed`)? Readable, not a law, and it crosses
   the barrier in display only.
8. **Searching from the declaring Tag.** `Fighter[:].weapon == sword`
   finds bearers for anyone who holds `Fighter`. This is STEP-SPEC-22's
   open question 2; one decision should cover both.
9. **`@Record` optional.** The first draft required `@Record` beside
   `@Tool`, after STEP-SPEC-34's convention. The Director read that as
   redundant on 2026-10-12, and rule 2.2 now makes `@Tool(Weapon)` alone
   the declaration, with `@Record` accepted as a restatement. Confirm.
10. **Issue #74.** This STEP depends on the recommended refusal of
    dunder-named conditions so that "a part's own truth is its contract"
    is the only road. Confirm the refusal and the STEP-SPEC-14 wording.
11. **A nested-class spelling.** The Director suggested that a Tool could
    decorate a class declared inside the Tag, limiting its scope to that
    Tag and building one record-like object per Agent at tagging. Should
    that be (a) the law instead of the Record builder, (b) sugar over the
    builder, `@Tool(Weapon) class sword: ...` meaning "build one `sword`
    per Agent at Parts, then the forge's rules apply", or (c) left out?
    This STEP proposes (b) as a later addition, once the one mechanism is
    law, and asks how such a class would state its Tags without the class
    itself becoming the kind.
12. **A Shape that computes a Tool slot with an Action.** §1.1 lets a
    Shape "compute a Base Record with an Action". On a Tool slot that
    makes a smith: every call forges a new sword, `charlie.weapon` is no
    longer one object but a bound Action, and the bearer's Post is the
    only thing that notices (verified on `main`, 2026-10-12: the Shape
    applies, the Agent is left applied and defective, two calls give two
    swords, and `Weapon`'s Field grows by one per call). Should a Tool
    slot be closed to that change of kind, as STEP-SPEC-22 rule 4.4
    closes a Link's slot, so that a Shape may redeclare it only as a Tool
    and rework the tool through the stored seat? This STEP recommends
    closing it: a thing one has needs one identity. It amends §1.1 for
    Tool slots only, and is the one place this STEP would touch §1.1.
    *Implemented as recommended in PR #143, and closed to a plain Record
    as well as to an Action, since either drops the guard in silence;
    rule 4.6 states it. The Director may reopen it.*

## Validation

Implemented in PR #143 (`TopKit/tools.py`, with the gate on the runtime
type beside the Constant gate; `tests/test_tools.py`, 56 tests). Each
item below names where it is shown; all pass on 2026-10-12 with the
full suite (`python3 -m unittest discover -s tests -t .`), the opt-in
budgets (`TOPKIT_PERF=1`) and the oracle at its audited size.

- the guard at Parts and at the write, including `object.__setattr__`,
  for a non-member, a Rogue of the kind, `None` and the bearer:
  `Admission_Tests`, `Emptiness_Tests`;
- a kind written `Weapon | None`: `None` admitted at Parts and at the
  write, presence still `True`, `del` still the drop
  (`Emptiness_Tests.test_the_declared_empty_hand_...`); a population
  (`Weapon | Blessed`, `Weapon & Blessed`, `~Weapon`, `Weapon[:]`)
  refused as a kind at class use, with the spelling meant
  (`Declaration_Tests.test_a_population_is_not_a_kind`);
- the failure outcomes under today's §0.6: a refused gaining rolls the
  whole call back, the bearer outside the Field and the host's own type
  restored (`test_a_builder_returning_a_non_member_refuses_the_gaining`).
  Under STEP-SPEC-39 (PR #78, not yet on `main`) the same refusal leaves
  the Gains already acquired and keeps the bearer out of the Field; the
  wiki's examples assert only what holds under both, and are to be
  re-run on that branch when it lands;
- a Shape's own kind list through the stored seat
  (`Overlay_Tests.test_a_shape_receives_the_tool_in_the_stored_seat_...`);
  the slot closed to a plain Record and to an Action, from a Shape and
  from an independent Tag, with no Overwrite Warning before the refusal,
  and `@Delete` freeing it (`Overlay_Tests`, rule 4.6 as amended);
- `@Constant`, `@Secret` and `@Tool` layered on one name, in every
  stacking order, `@Public` too (`Stacking_Tests`);
- Rip of the bearer (slot sticky and still guarded; a `@Rip` protocol
  may disarm), Rip of the tool's Tag (Rogue in hand, the bearer's Post
  notices, a fresh tagging repairs), reapplication after Rip for an
  ordinary slot (rebuilt), through the stored seat (kept) and for a
  Constant slot (kept, builder not run): `Lifecycle_Tests`;
- a tool whose own gate fails inside the forge: the failure keeps its
  name, the bearer is rolled back; a later gaining's failure leaves the
  forge's Tag on a handed-in object, which the caller undoes
  (`Forge_Tests`);
- two bearers of one tool, the tool's Tags travelling with it, a tool
  that bears a tool and guards its own slot (`Sharing_Tests`);
- the two doors: a bearer's Action reading the tool's secret fails
  closed, the tool's own Action reads it
  (`Sharing_Tests.test_a_bearers_action_reads_its_tools_secret_fails_closed`);
- a host's own `__setattr__` keeps its behaviour and admission runs
  before it; presence answers for the slot; a Tool slot does not
  multiply runtime types, since the gate reads the kind from the Agent's
  state (`Host_Tests`);
- the Record-write budget of `tests/test_performance.py`: the guard is a
  data descriptor on the runtime type for the Tool's name only, so an
  ordinary Record's write path is unchanged; the 13 budgets pass;
- the oracle: `Exercise_Tools` in `tests/oracle_topkit.py` checks the
  three laws on every seed's Agents against the model's membership;
  `PASS seeds=1701..1710 transitions=4000` under the suite, and the
  audited run passes;
- the wiki page's 16 blocks run as one program under
  `tests/test_documents.py`, the `@Tool` blocks included; the
  Specification's new §1.3 example runs in `tests/spec_examples.py`.

Known limit, shared with `@Constant`: a host whose instances cannot
change class in place (`__slots__` without a compatible layout) cannot be
actualized, and the kit says so with the existing Composition Failure.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
