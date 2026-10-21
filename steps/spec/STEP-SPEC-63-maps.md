# STEP-SPEC-63: Maps — Links between Tags

- **STEP:** SPEC-63
- **Desk:** spec
- **Title:** Maps: a Relation declared in a Pin connects Tags
- **Author:** Claude, recording the Director's 2026-10-20 and 2026-10-21 direction
- **Status:** Brief
- **Created:** 2026-10-20
- **Renumbered:** 2026-10-21, from SPEC-61. That number is held by the
  Deployed STEP-SPEC-61 (Condition Lifetimes), and SPEC-62 is held by the
  late-Pin boundary Brief.
- **Related issue:** [#347](https://github.com/JulTob/Tag_Oriented_Programming/issues/347)
  (Link independence, which laws 9–12 lift)
- **Related Briefs:** [STEP-SPEC-51](STEP-SPEC-51-independent-link-fields.md)
  and [STEP-SPEC-52](STEP-SPEC-52-ordered-link-underlays.md), the latter as
  corrected by [PR #406](https://github.com/JulTob/Tag_Oriented_Programming/pull/406)
- **Related runtime draft:** [Links core on main / PR #435](https://github.com/JulTob/Tag_Oriented_Programming/pull/435) (Draft)

> One STEP, one topic. This Brief says what a Relation declared in a Pin's
> body grants: a Map, a Link whose holder and Contacts are Tags. Whether a
> Pin may pin a Link is a separate topic, STEP-SPEC-64.

## Summary

A **Map** is a Link whose holder and Contacts are Tags. A Relation,
`@Link(agent, contact)` on a nested Tag class, declared in a **Pin's** body
is a Map template. Pinning a Tag grants that Tag its own actual Map. The
Map's Field holds Tags, and each of its Pairs connects the holding Tag to
one Contact Tag. The decorator is written the same way at both levels.
Where it is declared decides what it grants:

| Declared in | Granted to | Its Field holds | Name |
| --- | --- | --- | --- |
| an ordinary Tag | each tagged Agent | Agents | Link |
| a Pin | each pinned Tag | Tags | Map |

A Map reuses the Link machinery one level up. From Links it takes its
independence (STEP-SPEC-51), its ordered class-header Form (STEP-SPEC-52, as
corrected by PR #406) and its Pair receiver. A Map's Records and Actions
belong to the Pair, not to either Tag. From Pins (Specification §1.9) it takes
the rules that every name a Pin lands must obey.

The name **Map** is the Director's choice (2026-10-20). The Rationale says
why the Tag level gets a name of its own.

Links are not on `main`. PR #435 is a Draft port of their core, and Maps have
no runtime at all. This Brief claims no runtime change.

## Motivation

The Director asked (2026-10-20): *"Should we implement Tag-level-links? Just
like record-tags are links these could be report-links."* Two reasons to say
yes:

1. **The schema already implies it.** A Link is a Tag of its Agent
   (STEP-SPEC-51, Motivation). A Pin is the same structure one level up: its
   Agents are Tags (Specification §1.9; wiki 2.1 §3, "levels repeat, never
   mix"). A Relation declared in a Pin therefore has an obvious meaning, a
   Link whose holder and Contacts are Tags. Today it has no meaning. The
   Links draft refuses it until "Links between Tags" get "their own receiver
   rule" (STEP-SPEC-22 rule 2.8), and the Draft port in PR #435 implements
   that refusal. This STEP supplies the rule by reuse. Because a Map is a Tag
   of the pinned Tag, the independence of Tags applies to it for the same
   reason it applies to a Link.
2. **It closes a real gap.** Today the only declared structure between two
   particular Tags is the Base/Shape order: the Geometry, a partial order
   that means inheritance (Specification §0.4; wiki 2.1 §2.1). A Pin
   classifies Tags, one Pin over a Field of Tags. It does not say that one
   particular Tag stands in a named relation to another particular Tag, with
   facts of its own about that pair (`Sword —forged_by→ Smith`,
   `since=1204`). Maps add those named, directed arrows **beside** the
   Geometry, not inside it. `Form`, `f"{T:form}"` and the partial order do
   not change, and no Map is a Base or a Shape of anything.

## Specification

Every law below is proposed. Neither Links nor Maps exist on `main`, so
"is refused" and "runs" describe the intended language. A bare section sign
(§) refers to the Specification. Laws of other STEPs are always named with
their STEP.

Each law states its source. Where the source is a law of another STEP, the
Maps law is a lift of it. A lift is not a verbatim copy: the table says what
each lift changes.

| Maps law | Source | What the lift changes |
| --- | --- | --- |
| 1 | New. Replaces STEP-SPEC-22 rule 2.8's refusal of `@Link` inside a `@Pin` | — |
| 2 | STEP-SPEC-52 law 1 | The seats hold Tags |
| 3 | §1.9, the receiver rule (STEP-SPEC-9 §3) | Applies the existing `tag` parameter convention to Map members |
| 4 | STEP-SPEC-51 law 3, and the Pair scope of STEP-SPEC-22 rule 2.3 | The Pair connects two Tags |
| 5 | STEP-SPEC-51 law 1 | A Tag holds the actual Map |
| 6 | §1.9, "Who may be a Target" | A Map's Contacts are the Tags a Pin's Targets are |
| 7 | New. Amends one sentence of §1.9 | — |
| 8 | §1.9, collision control and Constant protection; §1.2 and §1.3, the Overlay | Adds a refusal over the Tag's own Operation or Report, and refuses `@Public` and `@Secret` |
| 9–12 | STEP-SPEC-51 laws 2–5 | Agent → pinned Tag; declaring Tag → declaring Pin |
| 13 | STEP-SPEC-52 law 2, and Resolution and lifetime ¶2 | — |
| 14 | STEP-SPEC-52 law 3 | Only a Pin can be a plain entry; an ordinary Tag is refused |
| 15 | STEP-SPEC-52 law 4 | — |
| 16 | STEP-SPEC-52 law 5 | Adds: a Contact without that Map fails the turn |
| 17 | STEP-SPEC-52 law 6 | — |
| 18 | STEP-SPEC-52 law 7 | Closes the list of entries; refuses an Agent's Link |
| 19 | STEP-SPEC-52 law 8 | States that the selected Map does not run after a failure |
| 20 | STEP-SPEC-52 law 9, and its Summary's list of what each turn keeps | — |
| 21 | STEP-SPEC-52 law 10, and its seat-restoration requirement | — |
| 22 | STEP-SPEC-52 law 11, and its `agent is contact` requirement | — |
| 23 | STEP-SPEC-52 Resolution and lifetime ¶1 and ¶3 | States that the soft coordinate follows the Overlay |
| 24 | STEP-SPEC-52 Resolution and lifetime ¶4 | — |
| Python profile boundary | STEP-SPEC-52 Python profile boundary | Adds: the Map-template checks run at class use |

STEP-SPEC-52 is cited as corrected by PR #406. Its "Resolution and lifetime"
paragraphs are numbered in that text's order.

### 1. Declaration, seats and receivers

1. **A Relation declared in a Pin is a Map template.** `@Link(agent, contact)`
   on a nested `class Knows(Tag)` inside a Pin's body declares a Relation, in
   the same way as inside an ordinary Tag (STEP-SPEC-51 law 1). Where it is
   declared decides what it grants. A Relation in an ordinary Tag grants each
   tagged Agent an actual Link. A Relation in a Pin grants each pinned Tag an
   actual Map. This replaces the Links draft's refusal of `@Link` inside a
   `@Pin` (STEP-SPEC-22 rule 2.8). A Relation that is itself a Pin is still
   refused.
2. **Every Map names its seats, with the Link's words.** A Relation in a Pin
   is declared `@Link(agent, contact)`, with the same seat words as in an
   ordinary Tag. In a Map, `agent` is the pinned Tag whose actual Map receives
   the call, and `contact` is the other Tag in that call. §1.9 already calls
   the pinned Tag the Pin's Agent "in every sense of Ring 0". There is no
   Tag-level seat word. In a Pin, bare `@Link`, or `@Link` with any other seat
   words, is refused with a Declaration Failure, as STEP-SPEC-52 law 1
   proposes for bare `@Link` in an ordinary Tag. The seat words stay in scope
   inside the Relation's protocols, so a zero-parameter Imprint can use
   `agent` and `contact` as the current Map's two Tags.
3. **The first parameter is written `tag`.** A function the Relation declares
   for the Pair receives the two seats in order, the holding Tag first and the
   Contact second: `def since(tag, contact, *, since=None)`. The name `tag`
   follows §1.9's convention for the first parameter of a Pin's Agent-scope
   member (STEP-SPEC-9 §3), so that the receiver reads right. It is
   discipline, not a check. As §1.2 says of every Action, the first parameter
   is the receiver under any name. Only this parameter is renamed. The
   decorator's seat word stays `agent`.
4. **A Map's Records and Actions are contributions of the Pair.** An actual
   Map holds one Pair per Contact. The Pair receives the Relation's Actions,
   Records and conditions, as a Link's Pair does. `Wizard.Knows[Elf].since`
   is a Record of the Pair of `Wizard.Knows` and `Elf`. It is not a Report: it
   does not land on `Wizard`, on `Elf`, or on either Tag's Agents. Reports and
   Operations that the Relation declares belong to the actual Map itself, one
   per holding Tag, as a Link's do. **Maps therefore add a receiver that
   §1.1's two-scope table does not cover: the Pair.** They inherit it from
   Links (STEP-SPEC-51 law 3; STEP-SPEC-22 rule 2.3 states the Pair scope).
   They do not take it from §1.9's Pin receiver rule. That rule still governs
   the Pin's own Records and Actions, which land on the pinned Tag as Reports
   and Operations, unchanged.
5. **A template owns nothing.** A bare Relation name is a blueprint with no
   Field and no Contacts. For a pinned Tag `Wizard`, `Wizard.Knows` is an
   actual Map: a Tag held by `Wizard`, with its own Field.

### 2. The levels never mix

6. **A Map's Contacts are Tags.** An actual Map applies to Tags only, as a
   Pin does. Its Field holds Tags. An object offered as a Contact is refused
   with a Composition Failure, as §1.9 refuses an object for a Pin. A Link's
   Field holds Agents and refuses a Tag, as §1.9 refuses an ordinary Tag on a
   class. A Pin is a Tag (STEP-SPEC-9 §2, rule 3), so a Pin may be a Contact.
   Nothing a Map holds is projected onto either Tag's Agents. This STEP admits
   no Contact kind beyond the Tags that §1.9 admits as Pin Targets.
   STEP-SPEC-64 separately asks whether an actual Link, itself a Tag the kit
   builds, may be pinned. This STEP decides that question neither for Pins nor
   for Maps. **Left open:** whether an actual Map may itself be a Map's
   Contact, or be pinned. Both follow from STEP-SPEC-64's answer for an
   actual Link, and this STEP proposes neither.
7. **An actual Map is not a Pin.** It is a Tag the kit builds from a
   Relation, as an actual Link is, and its Contacts are at its holder's level.
   It cannot be a Pin, because a Pin lands its Records on its Target as
   Reports (§1.9), while a Map's Records land on the Pair (law 4). The
   Relation is not a Pin either (law 1). §1.9's sentence "An ordinary Tag
   applies to objects only" therefore gains one named exception: an actual
   Map applies to Tags only. Each Field still holds one level, so "Fields
   never mix Agents and Tags" holds without amendment.
8. **A Map name is a name the Pin lands.** The actual Map is reached on the
   pinned Tag by its name, `Wizard.Knows`, so §1.9's rules for the names a Pin
   lands apply to it:
   - **Collision control.** A Map is refused at the gate if it is named like
     any of these: something the pinned Tag declares in Agent scope or as a
     protocol, itself or in a Base; or a name every Tag answers through its
     metaclass. A Map named like the Tag's own Operation or Report is refused
     too. A Map has no Underlay seat, so it cannot be a patch.
   - **Constant protection.** A Map cannot replace or hide a Constant
     Contribution of the Tag or of one of its Bases.
   - **Overlay.** A same-name Map landed by another Pin follows the Overlay
     laws of §1.2 and §1.3, as §1.9 says of every name another Pin landed.
     Within one Pin's Form, the later layer's Map becomes visible without a
     word. A same-name Map from an independent Pin becomes visible and is
     diagnosed with an Overwrite Warning, as an independent replaced Action
     is.
   - **Publication.** In this STEP, `@Public` and `@Secret` on a Map's
     members are Declaration Failures. Where a Pair member published onto a
     Contact Tag would live, and who could see it, is a separate topic.
   - **Cross-kind collision.** A Map and a Report or Operation of the same
     name, landed on one Tag by independent Pins, is a cross-kind collision:
     a Composition Failure (§1.1), as for any two kinds at one name.
   - **Sticky.** A Map is sticky like every name a Pin lands (§0.7, §1.9).
     Ripping the granting Pin from `Wizard` leaves `Wizard.Knows`, its Field
     and its Pairs with `Wizard`, as STEP-SPEC-22 rule 4.5 says of a Link
     when its granting Tag is Ripped.
   - **The other decorators.** Apart from `@Public` and `@Secret`, a Map
     Relation takes the decorators STEP-SPEC-22 rule 2.3 lists for a
     Relation, with the Pair as the receiver: `@Flag` answers its words on
     the Pair, never on a Contact Tag. Because no Map member is published
     onto a Contact Tag, an `@Underlay` never patches a member of a Contact
     Tag. This is a proposal; the Director may instead refuse `@Flag`,
     `@Delete` and `@Underlay` in a Map Relation until a later STEP.

### 3. Independence, lifted from STEP-SPEC-51

Laws 9–12 lift STEP-SPEC-51 laws 2–5. Its law 1 is law 5 above. The lift
makes two substitutions: the Agent becomes the pinned Tag, and the declaring
Tag becomes the declaring Pin. Pins over one Tag are ordered as Tags over one
Agent are: by application, and within one Pin's Form deepest first (§0.4).
The examples refer to the first program in the Example section. There,
`Spy` is a Shape of the Pin `Social`, and both declare a Relation named
`Knows`.

9. **One Field per actual Map.** Applying a declaring Pin grants the pinned
   Tag that Pin's own actual Maps. A later Pin's same-name Map is another
   actual Map. The Tag's ordinary Overlay shows the latest `Wizard.Knows`
   (law 8). `Social[Wizard].Knows` selects the Map of the Social layer.
   Reading either Map does not add a Contact.
10. **One Pair per Map and Contact.** If the same Contact Tag is admitted
    into two actual Maps of one Tag, each Map holds a different Pair. Their
    Actions, Records, Posts and saved Rip work stay independent. Tagging a
    Contact in one Map does not automatically admit it to the other. That
    admission requires an explicit Map call, or an ordered underlay declared
    by a later Map (laws 13–24).
11. **One Map turn.** Calling `Wizard.Knows(Elf)` runs the selected Map's
    Gate, training, Field admission and Posts under the ordinary Tag rules
    that apply when Maps are deployed. Another Map's Contact Tagging, if a
    declared ordered underlay or a protocol expressly requests it, stays its
    own turn and its own Field admission. A shared declaration name, or the
    declaring Pin's Form, does not by itself apply the other Map.
    `Social[Wizard].Knows(Elf)` selects the Social layer's Map explicitly.
12. **Independent Rip and live Pair views.** Ripping one actual Map's Contact
    or whole Field acts on that Map's own membership, Pair and saved teardown.
    It does not remove the Contact from another Map. Given `m = Wizard.Knows`,
    a saved `view = m[Elf]` is a lazy shortcut to that **same actual Map** and
    Contact. Each later use resolves what a fresh `m[Elf]` would resolve at
    that moment, including the Map's ordinary access rule. After Rip and
    reTag, it reaches the newly current Pair. It never follows the Tag's name
    Overlay to a different same-name Map.

### 4. The ordered header Form, lifted from STEP-SPEC-52

Laws 13–24 lift STEP-SPEC-52 as corrected by PR #406: its laws 2–11 and its
Resolution and lifetime section. Its law 1 is law 2 above. The `agent` seat
holds the pinned Tag, and the Contacts are Tags. The examples refer to the
second program in the Example section:

- `Acquainted` grants `Knows`.
- `Fellowship`, a Shape of `Acquainted`, grants `Allies`.
- `Registrar` grants `Listed`, and has pinned the Tag `Registry`.

The header is `class Allies(Acquainted, agent.Knows, contact.Knows,
Registry.Listed)`, and the call is `Wizard.Allies(Elf)`.

13. **The class header is the ordered Form.** Entries are resolved and
    applied from left to right. Each entry is resolved only when its own turn
    arrives, after every earlier Tagging has completed. An earlier entry may
    therefore establish a Map that a later entry selects. Every resolved
    entry is applied to the current `contact`: the expression selects the Tag,
    not its Target. The selected actual Map runs after the header completes.
    In the example, Elf holds no Knows Map before the call. The first entry,
    `Acquainted(Elf)`, grants it one, and the third entry then finds
    `Elf.Knows`. Resolving every entry before the first Tagging would wrongly
    refuse that valid Form. The header is TOP syntax. It grants no Python MRO
    lookup, copies no members, creates no `issubclass` promise and joins no
    Map families.
14. **A Pin entry applies to the Contact.** A Pin named in the header pins
    the Contact: `Acquainted(contact)`, here `Acquainted(Elf)`. A Pin is the
    only declared Tag that applies to a Tag, so it is the only plain class a
    Map header may name. An ordinary Tag in a Map header is refused with a
    Declaration Failure at class use, since every call would refuse it
    (§1.9).
15. **Agent-seat Map.** `agent.Knows` resolves the actual Knows Map through
    the `agent` seat, which is the pinned Tag receiving the call. The Form
    then applies that Map to the Contact. In `Wizard.Allies(Elf)`, it means
    `Wizard.Knows(Elf)`.
16. **Contact-seat Map.** `contact.Knows` resolves the actual Knows Map
    through the Contact seat. The Form still applies that Map to the Contact.
    In `Wizard.Allies(Elf)`, it therefore means `Elf.Knows(Elf)`: the
    Contact's own Knows, applied to the Contact. **It is not a reciprocal.**
    TOP does not reinterpret the self-Map or swap the Target. An author who
    forbids the self-Map states that rule in a condition. If the Contact holds
    no actual Map of that name when the entry's turn arrives, that turn fails
    with a Tag Resolution Failure before the selected Map's Gate: the
    Failure model's "required view is unavailable". The header never applies the
    granting Pin on the Contact's behalf. An earlier Pin entry, such as
    `Acquainted` here, is the explicit way to grant it.
17. **A particular Tag's Map.** `Registry.Listed` resolves that Tag's current
    actual Map and applies it to the Contact: `Registry.Listed(contact)`,
    here `Registry.Listed(Elf)`. The declaration stores a soft Tag-and-name
    reference. It does not store the current Field or a Pair, and it holds no
    strong reference that keeps `Registry` alive.
18. **No bare Relation, and a closed list of entries.** `Knows` alone is
    refused in the header, because a Relation is a blueprint and owns no
    Field. `agent.Knows`, `contact.Knows` and `Registry.Listed` identify
    actual Maps that can take a target. Together with the Pin entries of law
    14, these are the entries a Map header may contain. An ordinary Tag (law
    14) is refused, and so is an Agent's actual Link, whose Field holds Agents
    (law 6). Each refusal is a Declaration Failure at class use.
19. **Complete independent turns.** Every header entry performs an ordinary,
    complete Tagging with its own Gate, Gainings, Imprints, Field admission,
    Posts, diagnostics and recovery. A failed turn stops the sequence: no
    later entry runs, and neither does the selected Map. Earlier completed
    turns stay complete under the ordinary Tagging law.
20. **Selected Map last.** After the header, TOP applies `Wizard.Allies` to
    Elf. Its Pair stays distinct from the Pairs in `Wizard.Knows`,
    `Elf.Knows` and `Registry.Listed`, even when a protocol explicitly
    connects the same Tags. Each header turn and the selected Map keep their
    own Field, Pair, Gains, Services, Gate, Contract and Rip state.
21. **Seats stay available to protocols, and the reciprocal is explicit.**
    Within the selected Map's protocols, `agent` and `contact` resolve to the
    two current Map seats. An Imprint may therefore write
    `contact.Knows(agent)` to create the reciprocal `Elf.Knows(Wizard)`. That
    call is nested inside the selected Allies Tagging. It is not a header
    entry, and it is never implicit. TOP creates no other reciprocal. A nested
    Link or Map call establishes its own seats. It restores the outer seats
    afterwards, on success and on failure, before a later outer protocol
    runs.
22. **Repeated admitted call.** Calling `Wizard.Allies(Elf)` when Elf is
    already admitted to that actual Map is the ordinary active-Tag no-op. It
    does not rerun the header merely because the Relation later changed. To
    run the current Form and training, Rip Elf from `Wizard.Allies` and then
    map Elf again. When `agent is contact`, as in `Wizard.Allies(Wizard)`,
    the entries `agent.Knows` and `contact.Knows` both resolve to
    `Wizard.Knows(Wizard)`. The second is the ordinary active-Tag no-op, not
    a second Pair application.
23. **Seats and coordinates resolve live.** `agent.Knows` captures no Tag at
    declaration. Each Map call substitutes its own receiver, and
    `contact.Knows` substitutes its own Contact. Two pinned Tags calling
    `Allies` therefore resolve different actual Knows Maps. A concrete
    `Registry.Listed` also resolves live. The Relation remembers `Registry`
    weakly, together with the coordinate `Listed`. The coordinate follows
    `Registry`'s ordinary Overlay: a later Map at that coordinate is the one
    the next call uses. A saved Pair view behaves differently: it never
    follows a name Overlay (law 12). If `Registry` is gone, or no longer
    answers an actual Map at `Listed`, that turn fails with a Tag Resolution
    Failure before the selected Map's Gate. A Tag is usually a module-level class that outlives
    every call, so this branch is reached mainly by a Tag built at run time
    and since collected.
24. **Ordered inputs, no shared storage.** Inputs supplied to the selected
    Map call are available to the header turns through the ordinary
    ordered-input abstraction. This STEP makes no Field or Pair share storage
    between a header entry and the selected Map, and it merges no protocols.

## Example

This is the intended language, **not** a runnable example. Neither Links nor
Maps exist on `main`, and the Draft in PR #435 does not run Maps.

The first program shows two same-name Maps from two Pin layers and the Pair
receiver (laws 1–12):

```python
from TopKit import Link, Pin, Record, Tag, agent, contact


@Pin
class Social(Tag):

    @Link(agent, contact)
    class Knows(Tag):

        @Record
        def since(tag, contact, *, since=None):   # a Record of the Pair
            return since


class Spy(Social):                        # a Shape of a Pin is a Pin (§1.9)

    @Link(agent, contact)
    class Knows(Tag):                     # a second Relation of the same name

        @Record
        def cover(tag, contact, *, cover=None):
            return cover


class Wizard(Tag):
    pass


class Elf(Tag):
    pass


Social(Elf)
Spy(Wizard)                               # Form: Social, then Spy

base_map = Social[Wizard].Knows           # the Social layer's actual Map
spy_map = Wizard.Knows                    # the visible Map, from the Spy layer
assert base_map is not spy_map

spy_map(Elf, cover="courier")             # one Map turn, Tag to Tag
assert Elf in spy_map[:]                  # a Field of Tags
assert Elf not in base_map[:]             # the other Map did not admit Elf

base_map(Elf, since=1204)                 # a separate, explicit Map turn
assert base_map[Elf].since == 1204        # read through the Pair
assert spy_map[Elf].cover == "courier"

assert Wizard not in Elf.Knows[:]         # no reciprocal is implied
assert not hasattr(Wizard, "since")       # a Pair Record is on neither Tag
assert not hasattr(Elf, "since")
```

Neither Relation in this program names the other as an underlay.

The second program is separate. It shows the ordered header (laws 13–24):

```python
from TopKit import Imprint, Link, Pin, Tag, agent, contact


@Pin
class Acquainted(Tag):

    @Link(agent, contact)
    class Knows(Tag):
        pass


@Pin
class Registrar(Tag):

    @Link(agent, contact)
    class Listed(Tag):
        pass


class Registry(Tag):
    pass


Registrar(Registry)                       # Registry now holds its own Listed Map


class Fellowship(Acquainted):             # a Shape of a Pin is a Pin (§1.9)

    @Link(agent, contact)
    class Allies(Acquainted, agent.Knows, contact.Knows, Registry.Listed):

        @Imprint
        def Reciprocate():
            contact.Knows(agent)          # the explicit reciprocal


class Wizard(Tag):
    pass


class Elf(Tag):
    pass


Fellowship(Wizard)                        # Wizard holds Knows and Allies
Wizard.Allies(Elf)
```

`Wizard.Allies(Elf)` performs:

1. `Acquainted(Elf)`, which pins Elf and grants it its own Knows Map;
2. `Wizard.Knows(Elf)`;
3. `Elf.Knows(Elf)`, resolved only now, after the first turn granted
   `Elf.Knows`;
4. `Registry.Listed(Elf)`; and
5. `Wizard.Allies(Elf)`.

Within the fifth turn, the explicit `Reciprocate` Imprint calls
`contact.Knows(agent)`, which resolves as `Elf.Knows(Wizard)`. The self-Pair
from the header and the reciprocal Pair from the Imprint are distinct Pair
applications in Elf's one actual Knows Map. Without that Imprint there is no
reciprocal. The header's `contact.Knows` entry by itself gives Elf a
self-Pair, not a Pair with Wizard.

## Python profile boundary

STEP-SPEC-52's Python profile boundary applies to a Map header unchanged,
with Tags in the Agent's seat. An implementation must:

- consume the symbolic seats before ordinary Python base behaviour can leak
  through;
- keep the entries out of Relation-extension bases, shared families and
  Pair-Tag inheritance;
- preserve source order;
- drop the strong reference to `Registry` after it records the soft
  coordinate; and
- establish the seat context, which here holds Tags, before a Map protocol
  runs, and restore it afterwards.

Four points are particular to Maps:

- **A Pin entry is not a Python base.** `Acquainted` in the header of
  `Allies` does not make the Relation a Shape of `Acquainted`. If it did, the
  Relation would become a Pin, which law 1 refuses.
- **The level is known at class use.** A Relation's class body runs before
  its enclosing class exists, and `@Pin` marks that class after its body has
  run. Whether a Relation is a Map template can therefore be settled only at
  class use, once the enclosing class is known to be a Pin. The Declaration
  Failures of laws 8, 14 and 18 depend on it. This matches the Failure
  model, where a Declaration Failure takes effect at class use.
- **One set of seat symbols.** `agent` and `contact` are the seat symbols
  that STEP-SPEC-52 proposes TopKit export for Links. Nothing in the spelling tells the two levels
  apart; the enclosing class does.
- **A concrete entry must already exist.** In the intended spelling, Python
  evaluates `Registry.Listed` when the class statement runs. `Registry` must
  therefore already hold its `Listed` Map when `Allies` is declared, which is
  why the example pins `Registry` first. STEP-SPEC-52's example likewise
  applies `Registry(server)` before declaring `Social`.

## Rationale

**Mechanism reuse over new machinery.** A Map is Link code applied where the
holder and the Contacts are Tags. A separate Tag-to-Tag subsystem would
duplicate admission, Pairs, doors and teardown for no semantic gain. It would
also be a second place for the same bugs to live.

**One spelling; the place of declaration decides.** `@Link(agent, contact)`
is written the same way in an ordinary Tag and in a Pin, just as `@Record`
and `@Action` are. Where a declaration lands decides what it grants, not a
word the author picks. §1.9 already calls the pinned Tag the Pin's Agent in
every sense of Ring 0, so an `agent` seat that holds a Tag simply applies
that sentence. The receiver's own word appears where §1.9 already puts it:
on the first parameter, written `tag`.

**The Pair is the receiver at both levels.** A fact about Wizard and Elf
belongs to neither of them alone. A Report is one value held on the Tag for
its whole Field. If a Map's Record were a Report of Wizard, two Contacts
would fight over one slot. That is the defect STEP-SPEC-22 cured for Agents
by giving Links a Pair, and Maps reuse the same cure. §1.1's receiver rule
renames only the two Agent-scope contribution kinds a Pin receives
(Record → Report, Action → Operation). Protocols and a Pin's own Tag-scope
members keep their names, and so do a Map's Pair members.

**The name follows the Field's level.** The language already gives a Tag
whose Field holds Tags its own name, Pin, apart from a Tag whose Field holds
objects. A Link and a Map differ in exactly that way, so the Tag level gets
its own name for the same reason. The rename does not come from the
receiver rule: it names the connection by its Field's level, not its
contributions by their receiver.

**Independence is not optional.** Lifting STEP-SPEC-51 is what keeps
`for t in Wizard.Knows` honest: one actual Map, one Field, one Pair per
Contact. Sharing a Pair across same-name Maps is the defect STEP-SPEC-51 was
written to correct one level down.

**One Target per header.** Every header entry applies to the Contact
(STEP-SPEC-52 as corrected by PR #406). The header then reads as the ordered
list of Tags the Contact receives before the selected Map. A reciprocal
changes which Tag is the Target, so it belongs in protocol work that is
visible in an Imprint. It is not a direction inferred from a selector.

## Backwards compatibility

This is a new capability, and no program that runs today declares a Map.
`Link` does not exist in TopKit on `main`, so `from TopKit import Link`
fails there. The Links draft refuses `@Link` inside a `@Pin`
(STEP-SPEC-22 rule 2.8), and the Draft port in PR #435 implements that
refusal. Once the Links STEPs and this STEP are Cleared, this STEP replaces
that one refusal with Maps. The refusal of a Relation that is itself a Pin
stays.

The Specification changes in five places:

- **§1.1** needs one line naming the Pair receiver. The Links work must add
  that line in any case (STEP-SPEC-22 rule 2.3), and it must also cover Maps
  (law 4).
- **§1.9's sentence "An ordinary Tag applies to objects only"** gains the
  actual Map as a named exception (law 7).
- **§1.9's collision control** gains one line: a Map named like the Tag's own
  Operation or Report is refused (law 8).
- **STEP-SPEC-9 §2 rule 2**, "An ordinary Tag applies to objects only.
  `Wizard(Elf)` stays refused", needs a superseding note naming the same
  exception for an actual Map (law 7).
- **The Failure model's Overwrite Warning row**, defined for "a visible
  Action or Record", gains "or a Map" (law 8).

§1.9's list of Pin Targets does not change.

## Status gate and dependencies

This STEP **cannot be Deployed before Links are**.

1. **STEP-SPEC-51 and STEP-SPEC-52 are both Brief.** STEP-SPEC-52 is read as
   corrected by PR #406, which is open. Laws 2, 4, 5 and 9–24 and the Python
   profile boundary lift their laws. If either STEP changes in review, the
   lifted laws here change with it.
2. **The Link core is not on `main`.** PR #435 is a Draft port of
   STEP-SPEC-51 laws 1–4 and is not green yet. Lazy saved Pair views
   (STEP-SPEC-51 law 5) and the STEP-SPEC-52 header runtime are later,
   separate PRs. Maps have no runtime, and no part of this STEP is claimed
   as runtime behaviour.
3. **Order of work.** First Clear STEP-SPEC-51 and STEP-SPEC-52 (with
   PR #406). Then merge the Link core (PR #435), the saved Pair views and the
   header runtime. Only then build Maps, as that core applied where holder
   and Contacts are Tags.
4. **STEP-SPEC-64 is independent of this STEP.** Maps neither need nor imply
   that a Pin may pin a Link.

This STEP asks for **Cleared**. Deployment waits on the Link core.

## Alternatives considered

| Alternative | Why set aside |
| --- | --- |
| Name it **Relation** | *Relation* already names the template class declared under `@Link`. One word would have two jobs. |
| Keep the name **Link** at the Tag level | The language names a Tag whose Field holds Tags (a Pin) apart from one whose Field holds objects. A connection whose Contacts are Tags differs from a Link in the same way. |
| A separate Tag-level seat word in the decorator | This would make the level an author's choice at declaration, although the place of declaration already decides it. It would also split one Relation spelling into two. The receiver's word appears where §1.9 puts it: the first parameter, `tag`. |
| Make a Map's Record a Report of the pinned Tag | A Report is one value for the Tag's whole Field. A fact about Wizard and Elf belongs to neither Tag alone, and two Contacts would fight over one slot. |
| Build each actual Map as a Pin | This would leave §1.9's sentence unamended. But a Pin lands its Records on its Target as Reports, while a Map's land on the Pair (law 4), so the two receiver rules would collide on every Map. |
| A separate Tag-to-Tag subsystem | It duplicates admission, Pairs, doors and teardown, giving one set of bugs two homes. |
| Read `contact.Knows` in a header as the reciprocal | The Director rejected this for Links (STEP-SPEC-52, corrected by PR #406). Every header entry applies to the current Contact, so `contact.Knows` means `Elf.Knows(Elf)`. A reciprocal is written explicitly, `contact.Knows(agent)`, in a protocol (law 21). |
| Imply a reciprocal Map automatically | This would create hidden Taggings, with no Gate called at a clear turn. |
| Let this STEP also make a Link a Pin Target | That is a second topic. It is split out as STEP-SPEC-64. |
| Do nothing | The Director asked for report-links, and the gap is real: TOP has no declared, named arrow between two particular Tags that carries facts of its own about that pair. Pinning, `Rare(Wizard)`, is an arrow, but its facts belong to one Tag, never to the pair. |

## Acceptance requirements

Once Links are Deployed and this STEP is Cleared, Maps are accepted when all
of the following hold:

- A Relation declared in a Pin's body grants each pinned Tag its own actual
  Map. A Relation that is itself a Pin is still refused with a Declaration
  Failure (law 1).
- A Relation in a Pin is declared `@Link(agent, contact)`. Bare `@Link`, or
  any other seat words, is refused in a Pin with a Declaration Failure. Inside
  a Map's protocols, `agent` and `contact` are the current Map's two Tags
  (law 2).
- The guides and examples write a Map member's first parameter as `tag`. The
  name is not enforced (law 3).
- A Map's Record is read through the Pair, `Wizard.Knows[Elf].since`. It lands
  on neither Tag itself nor on either Tag's Agents. A Map's own Report is read
  through the actual Map. A Pin's own Records still land on the pinned Tag as
  Reports (law 4).
- A template alone has no Field. `Wizard.Knows` is an actual Map with its own
  Field, and reading a Map admits no Contact (laws 5 and 9).
- A Map's Field holds Tags, and refuses an object with a Composition Failure.
  A Link's Field refuses a Tag. Nothing a Map holds appears on either Tag's
  Agents (law 6).
- An actual Map is not a Pin. It is not listed among the Contact's Pins, and
  its Records do not land on the Contact (law 7).
- A Map name is refused at the gate when it collides with the pinned Tag's
  Agent-scope members, protocols, metaclass names, Operations or Reports, and
  it cannot replace or hide a Constant. Within one Form, a same-name Map
  overlays silently. From an independent Pin, it overlays with an Overwrite
  Warning. `@Public` and `@Secret` on a Map's members are Declaration
  Failures (law 8).
- Two same-name Maps from different Pin layers are distinct actual Maps, with
  distinct Fields and Pairs for the same Contact. Direct access chooses the
  visible Map, and `Social[Wizard].Knows` chooses that layer's Map (laws 9
  and 10).
- Applying a later Pin does not retrain Contacts already held by an earlier
  layer's same-name Map merely because the Relations share a name or the
  declaring Pin's Form (laws 9–11).
- A Map call is one turn. Another Map's Contact Tagging, requested by a
  header entry or by a protocol, is its own turn and its own Field admission
  (law 11).
- Ripping one Map's Contact or whole Field leaves another Map's Field, Pair
  and saved Rip work intact. A saved Pair view re-resolves the current Pair of
  its chosen actual Map and Contact after Rip and reTag, under the Map's
  ordinary access rule, and never switches to another same-name Map
  (law 12).
- The ordered header applies its entries left to right, each one resolved at
  its own turn. An entry that is established by an earlier entry resolves
  successfully, as `contact.Knows` does after `Acquainted(Elf)`. Every entry
  applies to the Contact (law 13).
- A Pin entry in the header applies to the Contact. An ordinary Tag in a Map
  header is refused with a Declaration Failure (law 14).
- `agent.Knows` means the holding Tag's actual Map applied to the Contact
  (law 15).
- `contact.Knows` means the Contact's own Map applied to that same Contact,
  `Elf.Knows(Elf)`. If the Contact holds no such Map at that turn, the turn
  fails with a Tag Resolution Failure before the selected Map's Gate. The header never applies the granting
  Pin on the Contact's behalf (law 16).
- A concrete entry such as `Registry.Listed` applies to the Contact without
  keeping `Registry` alive. After a later Map lands at `Listed`, the next call
  uses that Map. A coordinate that no longer resolves fails that turn with a
  Tag Resolution Failure before the selected Map's Gate (laws 17 and 23).
- A bare Relation in a Map header is refused with a Declaration Failure, and
  so is an Agent's actual Link (law 18).
- A failed header turn stops the later turns and the selected Map, without
  undoing the earlier completed Taggings (law 19).
- Header entries and the selected Map have independent Fields, Pairs, Gains,
  Services, Gates, Contracts and Rip state (law 20).
- A reciprocal Map occurs only through an explicit protocol call such as
  `contact.Knows(agent)`. The exact trace distinguishes the header's
  `Elf.Knows(Elf)` self-Pair from the Imprint's `Elf.Knows(Wizard)`
  reciprocal Pair. A nested Link or Map call restores the outer seats on both
  success and failure (law 21).
- Repeating an admitted Map call is the ordinary no-op and does not rerun
  the header. Rip and map again runs the current ordered Form. When
  `agent is contact`, the duplicate header resolution is the no-op rather
  than a second Pair application (law 22).
- Two pinned Tags calling `Allies` resolve different actual Maps for
  `agent.Knows`, each its own holder's (law 23).
- Inputs reach the header turns through the ordered-input abstraction, and no
  Field or Pair shares storage with another (law 24).
- The implementation proves that a Map header creates no Python inheritance,
  no Map-family sharing, no Pair reuse and no implicit reciprocal. It also
  proves that a Pin entry does not make the Relation a Pin (Python profile
  boundary).
- The Specification (§1.1 and §1.9), STEP-SPEC-9, STEP-SPEC-22, wiki 2.1, the
  guides and the tests all agree before this STEP is Deployed.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
