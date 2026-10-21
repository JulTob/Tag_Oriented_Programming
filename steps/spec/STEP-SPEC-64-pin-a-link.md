# STEP-SPEC-64: A Pin may pin a Link

- **STEP:** SPEC-64
- **Desk:** spec
- **Title:** A Pin may pin a Link
- **Author:** Claude, recording the Director's 2026-10-21 ruling
- **Status:** Brief
- **Created:** 2026-10-21
- **Split from:** law 6 of the earlier Maps draft (STEP-SPEC-63 at commit
  `576703a`), in
  [PR #400](https://github.com/JulTob/Tag_Oriented_Programming/pull/400)
- **Amends:** [STEP-SPEC-9](STEP-SPEC-9-tags-as-targets.md) §1 and §2
  (Cleared), and §1.9 of the [Specification](../../spec/SPECIFICATION.md),
  *Who may be a Target*
- **Design dependency:** [STEP-SPEC-51](STEP-SPEC-51-independent-link-fields.md)
  (Brief), and the Link core in
  [PR #435](https://github.com/JulTob/Tag_Oriented_Programming/pull/435)
  (Draft)
- **Pin spelling:** `class Rare(Pin)`, as the Director approved in [PR #426](https://github.com/JulTob/Tag_Oriented_Programming/pull/426).
  `main` still spells `@Pin class Rare(Tag)`.

> One STEP, one topic. This Brief says what a Pin's Target may be once Links
> exist. A `@Link` declared inside a Pin's body, a Map, is STEP-SPEC-63's topic
> and stays refused here.

## Summary

On 2026-10-21 the Director ruled: *"pins should also be able to tag links."*
A Pin is TOP's set pointer. It may point at a set (a Tag), at another pointer
(a Pin), or, under this ruling, at a connection (a Link). It never points at
an object.

The ruling leaves one question open, and this Brief puts it before the
Director. Is the Pin's Target the Relation blueprint, `Social.Knows`
(**Option A**), or one Agent's actual Link, `ari.Knows` (**Option B**)? The
two give different answers to where a Pin's members land, what `isinstance`
reports, what Rip does and what keeps the Target alive. The Brief recommends
Option B. The §1.9 text proposed in [PR #426](https://github.com/JulTob/Tag_Oriented_Programming/pull/426) already lists "actual Link
Tags" among a Pin's Targets, which matches Option B. The Decision is still
the Director's to record. It also names the existing rules the ruling amends.

Links are not on main. The Link core is a Draft port in PR #435, and that
Draft refuses both Targets. This Brief changes no runtime and claims none.

## Motivation

The ruling was first recorded as law 6 of the Maps Brief. It is split out
here for two reasons. It amends the Pin rules of a Cleared STEP, and it does
not depend on Maps: a Pin on a Link is still an ordinary Pin, at the level
Pins already work at.

Each option serves a different use.

- **One connection.** A program audits a particular relationship: Ari's
  acquaintances, not everyone's. `Audited(ari.Knows)` gives that one Link a
  gate, a promise, a Field of audited Links to walk, and a Rip that ends the
  audit without erasing that it happened. This is Option B.
- **A kind of connection.** A program marks a whole Relation, for example
  *Knows is symmetric* or *Knows is deprecated*.
  `Symmetric(Social.Knows)` would say that once, about the Relation itself,
  rather than once per Agent's Link. This is Option A.

TOP cannot say either today. On main, §1.9 sorts Tags into two kinds: a Pin
applies to Tags, and an ordinary Tag applies to objects. A Link fits neither
kind as §1.9 states them. It is a Tag but not a Pin, and, unlike an ordinary
Tag, it is held by one Agent and applies only to that Agent's Contacts.

In PR #435, `Rare(Social.Knows)` fails with "Knows is a Relation: link
through an Agent, agent.Knows(contact)". `Rare(ari.Knows)` fails with "Rare
is a Pin, and Knows is one Agent's Link: Links between Tags need their own
receiver rule (STEP-SPEC-22)". The Maps Brief said that `_check_pin_target`
must admit a Link. Section 4 below shows that this is not quite right: the
refusal to lift is one that PR #435 adds.

## Specification

### 1. The ruling, and what stays

1. **A Pin may pin a Link.** The Director, 2026-10-21: *"pins should also be
   able to tag links."*
2. **The set-pointer reading.** A Pin points at a set (a Tag), at another
   pointer (a Pin), or at a connection (a Link). It never points at an
   object; that remains §1.9's Composition Failure.
3. **What does not change, under either option.**
   - A Pin refuses an object. A Pair is an object, the hidden Agent of a
     Link, and is refused with every other object.
   - A Pin refuses itself and every Tag of its own Form (§1.9).
   - The kit's Tag for a Pair is never a Pin Target. It is the kit's own
     Tag, and a Pair is reached only through its Link (STEP-SPEC-22 Draft,
     rule 7.1).
   - An ordinary Tag and a Link apply to objects only. A Link refuses a
     class as a Contact, so a Link's Field never holds a Tag.
   - A Relation and an actual Link are never Pins. A `@Link` inside a Pin's
     body stays refused until STEP-SPEC-63 is decided.
   - A Pin does not alter its Target's own gate (§1.9).

### 2. The Decision: which Link is the Target

The Director is asked to choose one option. Each option below gives exactly
what pinning means under it.

| Question | Option A: the Relation, `Rare(Social.Knows)` | Option B: an actual Link, `Rare(ari.Knows)` |
| --- | --- | --- |
| The Pin's Agent | the Relation blueprint declared in `Social` | the Link that one Agent holds |
| Where landed Records and Actions live | on the Relation: `Social.Knows.rarity`, `Social.Knows.Describe()` | on that Link: `ari.Knows.rarity`, `ari.Knows.Describe()` |
| Effect on actual Links | none, for Links granted before or after the pinning | that Link only |
| `isinstance` | `isinstance(Social.Knows, Rare)` is True; `isinstance(ari.Knows, Rare)` is False | `isinstance(ari.Knows, Rare)` is True; `isinstance(bob.Knows, Rare)` is False |
| `f"{T:pins}"` | `f"{Social.Knows:pins}"` is `"Rare"`; `f"{ari.Knows:pins}"` is `""` | `f"{ari.Knows:pins}"` is `"Rare"`; `f"{bob.Knows:pins}"` is `""` |
| `del Rare[T]` | the Pin's Rip, with the Relation as receiver; no Link touched | the Pin's Rip, with the Link as receiver; its Contacts and Pairs untouched |
| What keeps `T` alive | the declaring Tag's class holds the Relation | the Agent holds its Link |
| The Target's own acts | still refused, `bool` included | all of Ring 0, as for any pinned Tag |

#### Option A: the Relation blueprint

A1. **Target and receiver.** `Rare(Social.Knows)` pins the Relation, the
    class declared under `@Link(agent, contact)` in `Social`'s body. The
    Relation is the Pin's Agent and the receiver of everything the Pin lands.
    An actual Link is refused as a Target, with a Composition Failure that
    points to its Relation.

A2. **Landing.** A Pin's Record lands as a Report held on the Relation's
    class, one value: `Social.Knows.rarity`. A Pin's Action lands as an
    Operation that receives the Relation: `Social.Knows.Describe()`. Nothing
    lands on an actual Link, an Agent, a Contact or a Pair.

    This needs one new rule in the Link core. PR #435 builds each actual
    Link's Tag scope from a copy of its Relation's class dictionary
    (`_tag_scope_of` in `TopKit/links.py`), and the copy does not skip what a
    Pin landed there. Without the new rule, Links granted after the pinning
    would carry copies of the Pin's members and Links granted before would
    not. Option A therefore requires the Link builder to skip Pin-landed
    names. This matches the existing rule that a pinned Tag applied to an
    Agent never projects its pinned members (STEP-SPEC-9, *TopKit notes*).

A3. **Patching.** A Relation's own Reports and Operations are the template
    that each new Link copies. A Pin member over one of them would reach
    Links granted afterwards and not earlier ones, so Option A refuses it at
    the gate, with nothing changed. A Pin member named like one of the
    Relation's Pair members (an Action, a Record, a condition, an Imprint, a
    teardown) is already refused by §1.9's collision rule, because they share
    the Relation's class dictionary.

A4. **`isinstance` and `:pins`.** `isinstance(Social.Knows, Rare)` is True
    from the pinning on, and stays True after Rip. `f"{Social.Knows:pins}"`
    names `Rare`. Neither reaches an actual Link. PR #435 builds each Link on
    the root `Tag`, not on its Relation, and membership does not inherit
    (STEP-SPEC-9 §3).

A5. **The blueprint stays a blueprint.** STEP-SPEC-51 says that `Knows` alone
    "is not an actual Contact Tag and has no Contact Field". STEP-SPEC-52
    rule 7 calls it a blueprint that owns no Field, and STEP-SPEC-22 Draft §9
    refuses every Tag-level act on it. Option A keeps those refusals for
    every act in which the Relation is the Tag: applying it, `in`, walking,
    `len`, truth, `~`, `[:]`, `[x]` and `del`. A pinned Relation is reached
    only from the Pin's side: `Social.Knows in Rare`, `Social.Knows in
    ~Rare`, `Rare[Social.Knows]` and `Contract.Display(Social.Knows)`. So
    `bool(Social.Knows)`, which §1.9 calls the Tag's own contract, stays a
    Composition Failure. Option A must
    state this as an exception to §1.9. A Pin with a `@Public` member refuses
    a Relation Target, because a Relation has no Field to publish onto.

A6. **Rip.** `del Rare[Social.Knows]` ends that pinning's Posts and runs the
    Pin's Rip protocols with the Relation as receiver. Landed values stay,
    sticky, on the Relation. `isinstance` stays True. No actual Link,
    Contact or Pair is touched.

A7. **Lifetime.** The Pin's Field holds the Relation by weak reference, as
    every Field holds its members, so the Field does not keep it alive. The
    declaring Tag does: `Social.__dict__["Knows"]` holds the Relation
    strongly, so the Relation stays pinned as long as `Social` exists. In
    practice that is the life of the program. A Relation has no ending of its
    own, so only Rip ends the pinning.

#### Option B: an actual Link

B1. **Target and receiver.** `Rare(ari.Knows)` pins the actual Link that
    `ari.Knows` reads at that moment. Under STEP-SPEC-51 §2, that is the
    Agent's visible Overlay. `Social[ari].Knows` names the `Social` layer's
    Link, and pinning it pins that Link. Each actual Link is pinned on its
    own. Pinning one pins no other Link: not a same-name Link of another
    layer, and not another Agent's Link. A Relation is refused as a Target,
    with PR #435's message, "link through an Agent".

B2. **Landing.** A Pin's Record lands as a Report held on that Link's own
    class, one value for that Link: `ari.Knows.rarity`. A Pin's Action lands
    as an Operation that receives that Link: `ari.Knows.Describe()`. Nothing
    lands on Ari, on a Contact, on a Pair, on the Relation or on another
    Link. A Link is never a Base (PR #435), so the §1.9 clause about Shapes
    inheriting a landed Report has no case here. Pinning keeps STEP-SPEC-22
    Draft rule 6.3: the Pin's functions receive the Link, and nothing they
    can read on it names its Agent.

B3. **Patching and collision control.** The Link's own Reports and
    Operations are host members to the Pin, as §1.9 says of any Tag's own
    Tag-scope declarations. They are the Link's Tag scope, copied from its
    Relation for this Link alone (STEP-SPEC-22 Draft, rule 2.3). A Pin may
    patch them with an Underlay or the stored seat, and the patch reaches
    that Link only. Three kinds of name are refused at the gate, with
    nothing changed:
    - a name the Link's Relation layers give its Pairs;
    - a name of a line the Link publishes onto its Contacts (`@Public`,
      Draft rule 2.7);
    - a name that the kit's Link machinery answers.

B4. **Publication.** `@Secret` follows §1.9, with the Link as the Tag.
    `@Public` would publish onto the pinned Tag's Field, and a Link's Field
    is its Contacts. The Draft keeps a barrier: nothing lands on a Contact
    but membership and what the Relation publishes (the notes at the top of
    `TopKit/links.py` in PR #435, and Draft rule 2.7). So a Pin with a
    `@Public` member refuses a Link Target, with nothing changed. Opening
    that is its own topic.

B5. **Membership and reading.** The following work as §1.9 says for any
    pinned Tag: `ari.Knows in Rare`, `isinstance(ari.Knows, Rare)` (True
    from the pinning on, and after Rip), `list(Rare)`, `len(Rare)`, `~Rare`,
    `Rare[:]`, `Rare[ari.Knows]`, `ari.Knows.Rare` and `f"{ari.Knows:pins}"`.
    `bool(ari.Knows)` checks the Posts that its Pins gave it, and no Posts
    means true (STEP-SPEC-40). `Tags(ari)` does not name `Rare`, because the
    Pin is on the Link and not on Ari. Nothing on a Contact changes either:
    her Tags, Outline and format specs never list the Links that hold her
    (Draft rule 6.2), and so they never list those Links' Pins.

B6. **Contacts untouched.** Pinning admits no Contact, ends none, trains
    none and touches no Pair. The Pin's Preconditions, Imprints and
    Postconditions receive the Link, so `len(tag)` counts its sound
    Contacts. Ripping one Contact, `del ari.Knows[ruth]`, or the whole Field,
    `del ari.Knows[:]`, leaves the pinning in place.

B7. **Rip.** `del Rare[ari.Knows]` ends that pinning's Posts and runs the
    Pin's Rip protocols with the Link as receiver. Landed values and
    Operations stay, sticky, on that Link. `isinstance` stays True. The
    Link's Field and Pairs are not touched. Ripping the declaring Tag, `del
    Social[ari]`, leaves Ari's Link with him (Draft rule 4.5), and its
    pinnings stay with it.

B8. **Lifetime.** The Pin's Field holds the Link by weak reference and does
    not keep it alive. The Agent does. In PR #435 the Agent holds its Link
    strongly, by name and in its Link state, and the Link's record holds the
    Agent weakly. So a pinned Link lives as long as its Agent, and longer
    only while a program name holds it. Pinning must add no strong reference
    to the Agent, from the Link or from the Pin. A Link that is collected
    with its Agent leaves the Pin's Field, as any collected member does.

B9. **Ending.** §3.2 says: "Deletion of an Agent Rips it from its active
    Tags, so exit protocols run." A pinned Link is an Agent of its Pins, so
    the same rule applies when the Link ends. When an Agent's deletion ends
    its Links (Draft rule 8.3), each pinned Link is first Ripped from its
    Pins, best effort as every teardown at deletion is, and then its Field
    is Ripped. This follows rule 8.3's own order, in which the Agent's
    teardowns run before its Links' Fields are Ripped. So a Link that
    outlives its Agent, because a name holds it, is no longer pinned. Two
    pinnings are a Composition Failure, with nothing changed: pinning such a
    Link, and pinning a Link while its Agent's deletion is ending it. This is
    the same answer that linking through that Link gets (Draft rules 5.7 and
    5.8).

### 3. The rules this amends

This Brief amends existing rules. It does not leave them as they are.

1. **STEP-SPEC-9 §1, Vocabulary.** "Pin: A Tag declared `@Pin`. Its Targets
   are Tags." (PR #426 respells the declaration `class Rare(Pin)`.) Under the chosen option, the Targets include actual Links (B)
   or Relations (A). "Pinned Tag: A Tag that belongs to at least one Pin."
   Under B, a pinned Link is a Pinned Tag. Under A, a pinned Relation is one,
   although it is not a Tag in play.
2. **STEP-SPEC-9 §2, rules 1 and 4.** Rule 1, "A Pin applies to Tags only",
   widens to the chosen kind of Link. Rule 4, "A Pin's Field holds Tags only.
   Fields never mix Agents and Tags.", is re-derived below. Rules 2 and 3
   stand, with rule 3 as §1.9 now states it: a Pin may not pin any Tag of its
   own Form.
3. **Specification §1.9, *Who may be a Target*.** The two-kind sentences are
   "A Pin applies to Tags only; on an object it fails with a Composition
   Failure. An ordinary Tag applies to objects only; on a class it is
   refused, as before. [...] Fields therefore never mix Agents and Tags."
   They are replaced by one of the two paragraphs proposed below.
4. **Not on main: PR #435.** Its proposed §1.10 says that a Relation is
   "never a Pin's Target" and that "One Agent's Link is never a Pin's Target
   either". Its test in `tests/test_links.py`,
   `Integration_Review_Tests.test_a_pin_never_pins_a_relation_or_a_link`,
   asserts both. Option B reverses the second
   sentence. Option A reverses the first, and narrows Draft §9 ("a template,
   never a Tag in play") to the acts listed in A5.
5. **Law 6 of the earlier Maps draft** (STEP-SPEC-63 at commit `576703a`,
   PR #400) is superseded by this STEP. The current Maps Brief has already
   removed it and points here.

**Proposed §1.9 paragraph, Option B.**

> **Who may be a Target.** A Pin applies to Tags only: an ordinary Tag, a
> Pin, or one Agent's actual Link (§1.10). On an object it fails with a
> Composition Failure. So it does on a Relation, which is a blueprint, and on
> the kit's Tag for a Pair. An ordinary Tag and a Link apply to objects only;
> on a class they are refused, as before. A Pin may not pin itself or any Tag
> of its own Form. A Shape of a Pin is a Pin, and one Form is all Pins or no
> Pins: mixing them is a Declaration Failure. A Relation and a Link are never
> Pins. Fields therefore never mix Agents and Tags.

**Proposed §1.9 paragraph, Option A.**

> **Who may be a Target.** A Pin applies to Tags only: an ordinary Tag, a
> Pin, or a Relation, the blueprint of a Link (§1.10). On an object it fails
> with a Composition Failure. So it does on one Agent's actual Link and on the
> kit's Tag for a Pair. A pinned Relation is reached only from the Pin's side,
> and every act of its own stays refused. An ordinary Tag and a Link apply to
> objects only; on a class they are refused, as before. A Pin may not pin
> itself or any Tag of its own Form. A Shape of a Pin is a Pin, and one Form
> is all Pins or no Pins: mixing them is a Declaration Failure. A Relation and
> a Link are never Pins. Fields therefore never mix Agents and Tags.

§1.10 is the Links section that PR #435 proposes. Neither paragraph goes into
the Specification before Links are deployed.

**"Fields never mix", re-derived.** The kinds involved are:

| Kind | It applies to | Its Field holds | Pin Target in PR #435 | Option A | Option B |
| --- | --- | --- | --- | --- | --- |
| ordinary Tag | objects | objects | yes | yes | yes |
| Pin | classes of the admitted kinds | classes | yes | yes | yes |
| Relation | nothing: "link through an Agent" | no Field in the language (STEP-SPEC-51 §1) | refused | **yes** | refused |
| actual Link | objects, never classes | its Agent's Contacts | refused | refused | **yes** |
| the kit's Pair Tag | the kit's Pairs | Pairs | refused | refused | refused |
| any object, a Pair included | (not a Tag) | (none) | refused | refused | refused |

A Field holds exactly what its Tag was applied to. Every kind that applies to
objects refuses classes: the ordinary Tag and the Link, while the Pair Tag is
applied only by the kit, and only to Pairs. The only kind that applies to
classes, the Pin, refuses objects. So under either option
no Field holds both. The rule still holds. What changes is which kinds of
class a Pin's Field may hold:

- **Under B**, the new member is a Tag in play with its own Field, so every
  member of a Pin's Field still answers the acts of §0.8. One thing is new:
  the member may belong to one Agent. `t(x)` on it links `x` as that Agent's
  Contact, rather than tagging `x` in a Field that any object may join.
- **Under A**, the new member is a class with no Field that refuses every act
  of its own. "Fields never mix" still holds, because a Relation is a class
  and not an object. But §1.9 promises more: that the pinned Tag is the Pin's
  "Agent in every sense of Ring 0". That promise needs the exception of A5. A
  program that walks a Pin's Field and asks `len(t)` or `x in t` gets a
  Composition Failure on a pinned Relation.

### 4. What the code needs

On main, `_check_pin_target` in `TopKit/tags.py` raises in only two cases:
when `_is_tag(target)` is false, and when the target is in the Pin's own
Form. `_is_tag`, in `TopKit/geometry.py`, holds for any class whose metaclass
is `MetaTag`, other than the root `Tag`. Main has no Link core, and `TopKit`
does not export `Link`.

In PR #435, at head `93b156a` (unchanged at `d50683a`), both candidate Targets are `MetaTag` classes.
The Relation is the class the program declares under `@Link`. Each actual
Link is built by `_new_link` in `TopKit/links.py` as `MetaTag(name, (Tag,),
namespace)`. So both pass `_is_tag`, and main's check would admit both. PR
#435 adds two refusals of its own to `_check_pin_target`, after the `_is_tag`
test. `_refuse_relation(target)` refuses a Relation and the kit's Pair Tag.
`if _is_link(target): raise TagCompositionError(...)` refuses an actual Link.

So `_check_pin_target` does not need to start admitting anything that main
refuses. An actual Link already passes `_is_tag`, and so does a Relation. The
real work is defining the semantics of section 2, plus removing the refusal
that PR #435 added for the chosen Target. Law 6 of the earlier Maps draft
(commit `576703a`) said that `_check_pin_target` "must admit a Link". More precisely, main's check
already admits any Tag class, and the refusal to lift is in PR #435.

The changes each option needs, on top of PR #435:

- **Option B.** Remove the `_is_link` refusal and keep `_refuse_relation`.
  Extend collision control to the Link's Pair-member names, its line names
  and its machinery names (B3). Refuse a Pin with `@Public` members on a
  Link Target (B4). Refuse pinning an ended Link, or one whose Agent is
  being deleted, and Rip pinned Links from their Pins in the deletion path
  before their Field Rip (B9). Revise the PR #435 test named in section 3.
- **Option A.** Lift `_refuse_relation` for the Pin path only, and keep it
  for every act of the Relation's own (A5). Refuse an actual Link. Make the
  Link builder skip Pin-landed names (A2). Refuse Pin members over the
  Relation's own Reports and Operations (A3). Refuse `@Public` members (A5).
  Revise the same test.

A local probe was run against the PR #435 head with only the `_is_link`
refusal removed. It pinned an actual Link through the unchanged Pin path:
membership, a landed Report and Operation, `:pins`, and a sticky Rip all
worked. The Link stayed in the Pin's Field after its declaring Tag was
Ripped, and it left the Field when its Agent was collected. This suggests
that Option B needs no new mechanism for the ordinary cases. It is evidence
for planning only, not behaviour of any branch, and it did not exercise the
collision, publication or ending rules of B3, B4 and B9.

## Example

This is the intended language, not a runnable example. Links are not on
main, and PR #435 still spells a bare `@Link`.

```python
from TopKit import Action, Link, Pin, Pre, Record, Tag, agent, contact


class Social(Tag):

    @Link(agent, contact)
    class Knows(Tag):
        pass


class Audited(Pin):

    @Pre
    def Has_Contacts(tag):               # the Pin's gate receives the Link
        return len(tag) > 0

    @Record
    def auditor(tag, *, auditor=None):   # lands as a Report of that Link
        return auditor

    @Action
    def Summary(tag):                    # lands as an Operation of that Link
        return f"{len(tag)} known, audited by {tag.auditor}"


class Host:
    pass


ari, ruth, bob = Host(), Host(), Host()
Social(ari)
Social(bob)
ari.Knows(ruth)

Audited(ari.Knows, auditor="Dana")       # Option B: one actual Link
assert ari.Knows in Audited
assert list(Audited) == [ari.Knows]
assert isinstance(ari.Knows, Audited)
assert not isinstance(bob.Knows, Audited)    # another Agent's Link
assert ari.Knows.auditor == "Dana"
assert ari.Knows.Summary() == "1 known, audited by Dana"
assert f"{ari.Knows:pins}" == "Audited"
assert not hasattr(ari, "auditor")       # never on the Link's Agent
assert not hasattr(ruth, "auditor")      # never on a Contact
assert ruth in ari.Knows                 # no Contact admitted or ended

del Audited[ari.Knows]
assert ari.Knows not in Audited
assert isinstance(ari.Knows, Audited)    # the history stays
assert ari.Knows.auditor == "Dana"       # sticky
assert ruth in ari.Knows
```

Under Option A, `Audited(ari.Knows)` is refused, and `Audited(Social.Knows)`
fails inside the Pin's own gate, because `len(tag)` on a Relation is a
Composition Failure. A Pin without such a gate would pin the blueprint:

```python
class Symmetric(Pin):

    @Record
    def converse(tag):
        return tag.__name__


Symmetric(Social.Knows)                  # Option A: the blueprint
assert isinstance(Social.Knows, Symmetric)
assert Social.Knows.converse == "Knows"
assert not isinstance(ari.Knows, Symmetric)
assert not hasattr(ari.Knows, "converse")
```

## Rationale

The Brief recommends **Option B**. The choice is the Director's.

**It fits the ruling's own reading.** An actual Link is a set, the Contacts of
one Agent, and it is a connection, from that Agent. The blueprint is neither.
STEP-SPEC-51 says it has no Field, and Draft §9 says it is never a Tag in
play.

**The pinned Target stays an Agent in every sense of Ring 0.** Under B, every
act §1.9 promises for a pinned Tag works on the Link, its own truth included.
Under A, the Pin's member refuses most of those acts, so §1.9 needs an
exception, and code that walks a Pin's Field must allow for it.

**It keeps Links independent.** Under STEP-SPEC-51, each actual Link has its
own Field, Pair and Rip. Pinning one Link reaches no other, just as Ripping
one Link leaves the others alone. Under A, one pinning has a meaning for a
whole kind of Link but reaches no actual Link. Making it reach them would
need a copying rule, and that rule splits Links granted before the pinning
from Links granted after.

**It amends less.** B changes only who may be a Target, plus the Link-specific
details B3, B4 and B9. A also reopens Draft §9, adds a rule to the Link
builder and needs a truth exception.

**What B costs.** No single act marks a whole kind of Link. A program that
wants every Knows Link audited pins each one when it is granted. For example,
the declaring Tag's Imprint can call `Audited(agent.Knows)`, because a Link is
granted during Gainings (Draft rule 4.1), and Gainings come before Imprints
(§0.6). If the Director wants a single kind-level mark, Option A is the one
that gives it. A later STEP could also add one alongside Option B.

## Backwards compatibility

This STEP amends a Cleared STEP (STEP-SPEC-9 §1 and §2) and Specification text
that is on main (§1.9, *Who may be a Target*). It changes the documented
rule. It does not leave existing behaviour as it is.

- **Programs on main.** No program on main can build a Link, so no program
  on main gets a different result today.
- **What a Pin's Field may hold.** What §1.9 implies today, that every
  member of a Pin's Field is an ordinary Tag or a Pin, no longer holds.
  Under B, a member may be one Agent's Link, and `t(x)` on it links `x` as
  that Agent's Contact. Under A, a member may be a Relation, and every act
  of its own is a Composition Failure. A program that walks a Pin's Field
  must allow for the new kind.
- **PR #435 (Draft).** `Rare(ari.Knows)` under B, or `Rare(Social.Knows)`
  under A, changes from a Composition Failure to a pinning. Its proposed
  §1.10 sentence and its test change with it, as section 3 lists.
- **STEP-SPEC-63.** Its earlier draft's law 6 is superseded; the current
  Maps Brief has already removed it.

## Alternatives considered

| Alternative | Why this Brief sets it aside |
| --- | --- |
| Admit both the Relation and actual Links | Two meanings for one act, and it widens the Target rule twice. It could follow later, once one option has been tried. |
| A pinned Relation that reaches its Links | Membership does not inherit (STEP-SPEC-9 §3). Every Agent's Link would become a member without a pinning act. |
| Pin the declaring Tag instead, `Rare(Social)` | Already legal, but it marks the whole Tag, not the connection, so it does not answer the ruling. |
| Keep PR #435's refusal | Rejected by the Director's ruling. |
| Let an ordinary Tag pin a Link, without declaring a Pin | Ordinary Tags apply to objects. Fields would mix objects and classes, the reason STEP-SPEC-9 made Pins a declared kind. |
| Under B, publish a Pin's `@Public` members onto the Link's Contacts | Deferred. It crosses the Draft's barrier, in which a Contact receives only what the Relation publishes. |
| Leave this as law 6 of the Maps Brief | It amends a Cleared STEP's Pin rules and does not depend on Maps. One STEP, one topic. |

## Dependencies and status gate

1. **The Link core comes first.** PR #435 is a Draft and, by its own
   description, does not yet pass its Link tests. No part of this STEP can
   be implemented on main.
2. **STEP-SPEC-51 is Brief.** Option B relies on its actual Links and
   same-name layers. If STEP-SPEC-51 changes, B1 changes with it.
3. **STEP-SPEC-22 rules cited here are Draft text in PR #435**: rules 2.3,
   2.7, 4.1, 4.5, 5.7, 5.8, 6.2, 6.3, 7.1 and 8.3, and §9. They are not on
   main. If they are rewritten, sections 2 and 3 must be checked again.
4. **Maps are independent.** This STEP needs no Map, and STEP-SPEC-63 may
   proceed or not.

The Director is asked to choose an option and clear the design. The
implementation follows in a focused pull request after PR #435, or inside it.

## Acceptance requirements

Under either option:

- A Pin still refuses an object, a Pair included, itself, any Tag of its own
  Form, and the kit's Pair Tag, each with nothing changed.
- An ordinary Tag and an actual Link still refuse a class as a Target. A Pin's
  Field never holds an object, and a Link's Field never holds a class.
- A Relation and an actual Link are still never Pins.
- STEP-SPEC-9 §2, Specification §1.9, PR #435's §1.10 and its tests, and
  STEP-SPEC-63 agree with the chosen option before Links are deployed. Every
  Guide and Specification block for the chosen option runs.

If Option B is chosen:

- `Rare(ari.Knows)` pins that actual Link. Membership, the Field,
  `isinstance`, `len(Rare)`, `~Rare`, `Rare[:]`, `Rare[ari.Knows]`,
  `ari.Knows.Rare`, `f"{ari.Knows:pins}"` and `bool(ari.Knows)` over its Pin
  Posts work as for any pinned Tag. `Rare(Social.Knows)` is refused.
- A Pin's Record reads as a Report of that Link, and a Pin's Action calls as
  an Operation that receives that Link. Neither appears on the Agent, a
  Contact, a Pair, the Relation, another Agent's Link, or a same-name Link of
  another layer.
- Pinning admits, ends and trains no Contact and leaves every Pair unchanged.
  A Contact Rip or Field Rip of the Link leaves the pinning. `del
  Rare[ari.Knows]` runs the Pin's Rip with the Link as receiver, leaves the
  landed values sticky, and leaves the Link's Field and Pairs intact.
- A patch over the Link's own Report or Operation reaches that Link only.
  A Pin member named like a Pair member, a published line or a machinery name
  is refused, with nothing changed. A Pin with a `@Public` member refuses a
  Link Target.
- The Pin's Field keeps neither the Link nor its Agent alive. A Link collected
  with its Agent leaves the Pin's Field. An Agent's deletion Rips each pinned
  Link from its Pins, with their teardowns receiving the Link, before the
  Link's Field Rip. Pinning an ended Link, or one whose Agent is being
  deleted, is refused. Ripping the declaring Tag leaves the Link and its
  pinnings.

If Option A is chosen:

- `Rare(Social.Knows)` pins the Relation. `isinstance(Social.Knows, Rare)`,
  `Social.Knows in Rare`, `Social.Knows in ~Rare`, `Rare[Social.Knows]`,
  `f"{Social.Knows:pins}"` and `Contract.Display(Social.Knows)` answer. Every
  act of the Relation's own stays refused, `bool(Social.Knows)` included.
  `Rare(ari.Knows)` is refused.
- A Pin's Record reads as a Report of the Relation, and a Pin's Action calls
  as an Operation that receives the Relation. No actual Link, granted before
  or after the pinning, receives a copy. `isinstance(ari.Knows, Rare)` is
  False.
- A Pin member over the Relation's own Reports or Operations, or named like
  one of its Pair members, is refused, with nothing changed. So is a Pin with
  a `@Public` member.
- `del Rare[Social.Knows]` runs the Pin's Rip with the Relation as receiver
  and touches no Link, Contact or Pair. The Pin's Field holds the Relation
  weakly: the Relation of a declaring Tag that is collected leaves the Field.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, with Option **__**, because ____.
