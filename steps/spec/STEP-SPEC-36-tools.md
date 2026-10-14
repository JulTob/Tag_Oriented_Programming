# STEP-SPEC-36: Tools

- **STEP:** SPEC-36
- **Desk:** spec
- **Title:** Tools: admission by Tag or class for a Record that holds an object
- **Author:** Julio Toboso (@JulTob); originally drafted with Claude Code
  from the Director's brief of 2026-10-12
- **Review refinement:** Codex, 2026-10-12; the Tag-or-class kind and
  the implementation with Claude Code, 2026-10-13
- **Status:** Vetting
- **Created:** 2026-10-12
- **Refs:** PR #143 (this STEP and its implementation); PR #159 (Codex's
  class-admission runtime, closed; its useful tests are carried here and in #174);
  STEP-SPEC-33 (Presence), STEP-SPEC-34 (Constant),
  STEP-SPEC-39 (Tagging Admission, Cleared, PR #78), STEP-SPEC-40
  (Agent contract truth, Cleared, PR #160), STEP-SPEC-42 (condition names,
  Brief, PR #155), issues #30, #71 and #74, and PR #156

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A **Tool** is an object an Agent *has*, held as a Record value. It can be
an Agent in its own right: a Fighter holds a sword, the sword may be
Cursed, and the Fighter does not thereby become Cursed. This is *tener*,
beside a Tag's *ser* and a Record's *estar*.

An ordinary Record already holds such an object. This STEP adds the
modifier `@Tool(Kind)` to check the value's **kind** when that Record is
gained or assigned. A kind is a **specific Tag**, asked as membership
now, or a **Python class**, asked as the language's own instance test;
several kinds all hold, and `| None` declares the empty hand. The mark
does not create an object or train it. Records read and calculate
initial values; Actions and Imprints perform training and other effects.

```python
class Sword:
    def __init__(self, name):
        self.name = name


class Fighter(Tag):

    @Tool(Sword, Weapon)         # a Sword that is a Weapon; @Record may restate it
    def weapon(agent, *, weapon):
        return weapon           # admitted if it is both, now

    @Post
    def Armed(agent):
        return ("weapon" @ agent
                and agent.weapon in Weapon[:]
                and bool(agent.weapon))

    @Action
    def Strike(agent):
        if not agent.Armed:
            raise RuntimeError("a sound Weapon is required")
        return agent.weapon.Swing()


sword = smith.Forge()            # an Action creates and Tags the Sword
Fighter(charlie, weapon=sword)
```

Here `Sword` is a Python class and `Weapon` is a Tag, and the slot asks
both. `@Tool(Sword)` alone admits any Sword, tagged or not; `@Tool(Weapon)`
alone admits any member of Weapon, whatever its class. The optional Post
`Armed` additionally requires that the sword be a sound Weapon when it
matters. Tagging does not change the sword's host identity.

The added rule is **kind at admission**, not continuous membership or
validity. A seated object that later leaves Weapon's Field stays held: a
class term still holds, and a Tag term is not re-asked. The bearer's
Posts control whether it can be used; a Tag term refuses such a Rogue
only if it is seated again.

| Question | Spelling | Meaning |
| --- | --- | --- |
| Does the Gain exist? | `"weapon" @ agent` | Presence; no value read or Post evaluation. |
| Is the object currently a Weapon? | `agent.weapon in Weapon[:]` | Tag membership, including deficient members. |
| Do an Agent Tool's promises hold? | `bool(agent.weapon)` | Its visible Posts, independently of the bearer; plain objects retain Python truth. |

**Implementation status.** Implemented in PR #143 (`TopKit/tools.py`,
exported as `TopKit.Tool`), with `tests/test_tools.py`, a Tool exercise
in the oracle, the Specification's §1.3 "Tools" subsection, and the
[wiki page](https://github.com/JulTob/Tag_Oriented_Programming/wiki/1.4-TopKit-Tools)
running its `@Tool` blocks. The failure outcomes follow the tagging
sequence the kit runs: whole-call rollback on `main` today, STEP-SPEC-39's
retained Gains once PR #78 lands; the laws of this STEP do not change
between the two.

## Director's decisions recorded in this revision

The Director confirmed:

- **Tag or class (2026-10-12, later the same day):** "a tool could be a
  specific tag or a python class, not just the root class. Probably tags
  are more flexible, but I also want to control by any object." A kind
  is a specific Tag, asked as membership now, a Python class, asked as
  the instance test, or both at once; the root `Tag` and `object` name no
  kind. This revises the "Class, not Tag" bullet below: a Tag is a kind
  again, and the distinction from a Tag's `isinstance` history is kept by
  asking `value in T[:]`, never `isinstance(value, T)`.
- **Ordinary Overlay:** Rip and dropping a value preserve the Tool rule;
  `@Delete` or a permitted plain Record/Action Overlay ends it. Constant
  provides stronger protection.
- **Self-reference:** allowed when the bearer satisfies the declared
  kind. An author may forbid it with a Post.
- **Class, not Tag** (revised the same day, above): a Python class is a
  kind, and no Tag membership is implied by naming one.

The names in the examples deliberately distinguish the host `Sword`
from the Tag `Weapon`, so that a reader sees which question each kind
asks. This revision supersedes the first draft's automatic self-reference
refusal and its closed slot. It does not reopen the meaning of `in`,
Agent truth, or the accepted Tagging order.

## Motivation

Characters hold weapons, drones hold batteries, and accounts hold keys.
The held object can be tagged, damaged, repaired or shared independently
of its bearer. A Record supplies the reference and its normal lifetime;
Posts supply domain requirements.

Without this modifier, `charlie.weapon = "a stick"` is an ordinary Record
assignment. A Post can notice it later. Tool adds a refusal at the write
when the value is incompatible with the declared class, preserving the
old binding. It also makes None an explicit choice.

Presence still does not mean "armed and safe". A non-optional, present
Tool can be deficient, and under a class kind untagged or Rogue. Those
questions belong to membership and Posts, not to admission.

## Specification

### 1. Vocabulary and scope

| Term | Meaning |
| --- | --- |
| **Tool** | An object held as the value of a Tool-marked Record; it may itself be an Agent. |
| **Bearer** | The Agent receiving the Record; ownership is a domain question. |
| **Declared kind** | What the Record admits: one or more terms, all holding. A term is a specific Tag (a member now) or a Python class (an instance), or alternatives of either joined by `\|`. Never a population. |
| **Use** | Calling the held object's behavior, for example `charlie.weapon.Swing()`. |

The Record occupies the existing `(Agent, name)` slot. There is no new
Contribution kind, proxy object, ownership index or reverse reference.
The existing Record seats, Overlay and acts retain their meanings.

This STEP covers Agent-scope Records. Kinded Reports, Pin Tools and
Pair-scope contributions would be separate topics.

### 2. Declaration

1. `@Tool(C)` declares a Record. `@Record` is accepted as a restatement.
   An explicitly marked Action, Report, Operation, Pre, Post, Imprint,
   Rip or Delete cannot also be a Tool. Conflicting marks are refused by
   the declaring Tag and Contribution name, in either decorator order.
2. `@Tool(K1, ..., Kn)` takes one or more kinds, **all** of which must
   hold: `@Tool(Sword, Weapon)` admits a Sword that is a Weapon now. Each
   `Ki` is a specific Tag, a Python class, or the language's own union of
   either, whose alternatives retain Python's **or** meaning:
   `@Tool(Sword | Staff)` admits either class, `@Tool(Weapon | Staff)` a
   member of Weapon or an instance of Staff. `| None` admits None. A
   declared class admits its subclasses, including the runtime classes
   TOP uses to actualize its instances; a declared Tag admits members of
   its Shapes (§0.3, membership closed upward).
3. A Tag term asks **membership now**, `value in T[:]`, sound or
   defective, never a Tag's `isinstance` history. The root `Tag` and
   `object` name no kind ("not just the root class"), nor does a Pin
   (§1.9: a Pin's Agents are Tags). Populations such as `Weapon | Blessed`,
   `~Weapon` and `Weapon[:]` are refused with the spelling meant:
   `@Tool(Weapon, Blessed)` for both, a common Base Tag for either, since
   `|` between Tags is the Field algebra (§2.5).
4. No argument, None alone, a bare `@Tool` on the builder, an instance,
   a non-class, or a typing construct with no plain instance test (`Any`,
   a `Protocol`, a subscripted generic) is a Declaration Failure that
   shows the spellings meant.
5. Tool inside a Pin is refused: the pinned Tag receives a Report there,
   not an ordinary object Agent's Record.
6. Secret, Public and Constant stack with Tool in either order, retaining
   their meanings. Validate the final Contribution kind rather than an
   intermediate decorator state.
7. The builder retains the ordinary bearer, stored-value and keyword-input
   seats. It reads, calculates and returns a value. Applying or Ripping
   Tags, repairing held objects, and assigning other Gains belongs in
   Actions or Imprints. Tool introduces no exception to that boundary.
   Constructing a local initial value is ordinary calculation; the mark
   does not require a separate factory for side-effect-free construction.

### 3. Admission and assignment

1. At the Record's gaining, validate the returned value before writing
   it. At assignment, validate the new value before replacing the old
   binding. A class term follows Python's runtime instance check; a Tag
   term asks current membership; None is accepted only when explicitly
   included. A term's own instance test that raises is a Composition
   Failure naming the slot, with the cause kept; an interrupt propagates.
2. Admission never evaluates the object's Posts or invokes its truth
   protocol. A class term does not inspect Field membership: an untagged
   compatible object, a deficient Agent and a compatible Rogue are all
   admitted. A Tag term asks membership and nothing more: a deficient
   member is admitted; a Rogue of that Tag is refused, and the refusal
   names the Tag it left.
3. Supported Record assignment paths share the check, including
   `object.__setattr__` for ordinary names. A refused write keeps the
   prior binding and declaration intact. Existing Secret, Constant and
   host compatibility checks still apply.
4. Reading does not revalidate. Tagging or Rip of the held object does
   not update or remove the reference. Reassigning a Rogue is permitted
   under a class term and refused under a Tag term; a domain Post is what
   requires current membership continuously.
5. Self-reference is allowed when the bearer satisfies the kind. This
   adds no ownership or distinct-identity promise. A Post can require
   `agent.weapon is not agent` when the domain needs it.
6. A Tool's own Python protocols are ordinary object protocols, or normal
   Agent protocols after Tagging. A bearer Record with a protocol name
   follows existing Record rules: its value is not promoted into the
   bearer's type-level protocol seat. Ordinary assignment is checked,
   while direct kernel writes to protocol-named Records bypass admission,
   like raw dictionary writes. Existing reserved Agent names still apply.

### 4. Gainings, training and failures

The order is STEP-SPEC-39's **Gate → Gainings/Imprints → Field → Posts**.
Gains are acquired in declaration order and visible to subsequent Gains.
The class check runs at this Record's turn, not in a preliminary pass.

> **On `main` today.** STEP-SPEC-39 is Cleared but not yet on `main`
> (PR #78; its implementation is PR #174, still a Draft). Until it lands, the kit follows the
> Specification's §0.6: **Gate → Parts → Commit → Write → Quality**.
> A builder or admission failure is a Record failure at Parts, so the
> whole call rolls back and an occupied slot keeps the Tool it held.
> Field entry is at Commit, before the Imprints: an Imprint failure
> raises with the Agent in the Field and the gained Tool kept. The
> bullets below describe STEP-SPEC-39's sequence; `tests/test_tools.py`
> (`Sequence_Tests`) pins today's.

- A refused Gate gains nothing for that Tag; completed independent
  Taggings remain.
- If the builder or its class check fails, that value is not acquired.
  Earlier acquired Gains, including Posts and Tools, remain. The
  unfinished Tag has not added the Agent to its Field.
- An Imprint can create, Tag, improve and assign a Tool. If it fails,
  actual earlier effects and Gains remain under ordinary Tagging rules;
  the unfinished bearer is outside the Field and may be tagged again.
- Once Imprints finish, Field entry precedes Posts. A failed Post judges
  an admitted member deficient; it is not a late Gate refusal.
- Other Agents' completed Taggings remain independent. Tool introduces
  no rollback across Agents or automatic Rip of held objects.

Strict and Constant Tool Records can receive prepared values as inputs.
An ordinary optional Record can start with None and be filled by an
Imprint. Imprints cannot rely on the unfinished Tag's published Reports
or Operations through the bearer; these become available through the
Agent after Field entry.

Builder and admission failures use the existing composition failure
path, naming `Tag.Record` and preserving the cause where applicable.
Training failures keep the normal Action or Imprint boundary and cause.
No new failure hierarchy or generic compensation recipe is added. Rip
is an explicit domain act, not restoration of a previous state.

### 5. Declaration lifetime and Overlay

The admission rule belongs to the **effective Record declaration**.

| Act | Result |
| --- | --- |
| `del agent.weapon` | Drop the value; retain its admission rule for reassignment. Presence becomes false. |
| Rip of the bearer's Tag | Keep acquired values and declarations unless its protocol changes them. |
| `@Delete` at the name | End the Record and Tool rule, subject to existing protection rules. |
| Shape redeclares it with Tool | Its declared class becomes effective; check the returned value. |
| Permitted plain Record or Action Overlay | Replace the Contribution normally; the old Tool rule ends. |
| Independent Tag collision | Keep ordinary cross-kind refusals and Overwrite Warning. |
| Constant binding | Refuse replacement and deletion as Constant already requires. |

No hidden conjunction with earlier class declarations is added. An
Action replacing a Record may retrieve an existing object or calculate
something; it need not forge a new object on every call.

Reapplication rebuilds an ordinary Record with its stored value and
checks the result again. Use `stored is None` to distinguish empty from
falsy; a deficient Agent must not be mistaken for an absent one. The
builder does not train a replacement.

Established Constant reapplication skips the builder and retains its
binding. It also skips fresh admission. Constant protects the
binding, not the held object's contents, Tags or contract. Another
bearer may hold the same object while this bearer cannot drop it.

### 6. Independence, doors and truth

Holding an object applies none of its Tags, keywords, Posts or published
members to the bearer. The bearer receives a strong Record reference and
only its own declared requirements. Fields remain weak.

Existing composition doors keep their duration. A bearer Action cannot
directly read its Tool Agent's Secret because that Tool's door is shut.
Calling the Tool's Action opens its door. If called inside a bearer
Action, the bearer's door remains open too: a callback given the bearer
can read its Secrets during that call. Tools add no nested-call
isolation or automatic bearer reference. With self-reference, these are
one Agent's door, not two independent doors.

The Director's truth decisions are recorded in STEP-SPEC-40 and
STEP-SPEC-42; their implementations are on `main` (PRs #155 and #160):

- For ordinary object Agents, bool asks whether visible Posts hold,
  including before Field entry when Posts have already been gained.
- Hosts with explicit or inherited `__bool__` are refused before Tagging
  effects (STEP-SPEC-40, PR #160, on `main`). Tool admission alone does
  not Tag a host, so it does not trigger that eligibility check.
  Admission never asks the held thing's truth.
- Plain objects retain Python truth, including their own `__bool__`.
  Holding one does not make it an Agent or give it TOP contract truth.
- Conditions cannot use dunder names, and ordinary Agent truth cannot be
  replaced by another Contribution.
- Under the Director's 2026-10-14 revision in STEP-SPEC-40, `bool(Tag)`
  checks the Tag's own visible Pin Posts; no Posts means true even with an
  empty Field. This supersedes the earlier population-truth exception.
  `len(Tag)` still counts sound members. A class kind such as `@Tool(type)`
  may admit a Tag value; holding it does not change its contract or its Field.

The Tool's contract is not transferred to its bearer. A bearer Post can
check presence, current required membership and the Tool's Posts. Such
an early Post remains useful on an unfinished Rogue: do not disable it
merely because the bearer has not entered its Field. Ordinary Actions
use explicit guards, such as `if not agent.Armed:` or `if agent:`; Tool
does not introduce automatic blocking of Actions.

An author can explicitly end a non-Constant promise with Contract.Delete
in Rip. That is a domain choice. A safety Post may need to remain while
unsafe Gains remain.

### 7. Sharing, views and other patterns

Hand-over is assignment followed by deletion where permitted, not an
atomic move. Sharing is allowed and implies no exclusivity. The object's
Tags travel with its identity. Its Rip affects membership, not the
binding; ending a bearer does not automatically Rip the held object.

An Agent-bound Tag view keeps the Record reference recorded at admission,
as existing views do. It is not a cloned Tool or an ownership claim.
Later mutation of that object remains visible through the reference.

A shared object can already be returned by a Report. Prepare it outside
the builder if training is needed. Ordinary Reports initialize per
receiving Tag; a Constant Report shares its declaring Tag's one fixed
value with Shapes. Guarded Reports are outside this STEP.

Search from known bearers works today:
`[f for f in Fighter[:] if "weapon" @ f and f.weapon is sword]`.
There is no reverse-reference index. Links and Projection syntax remain
separate Brief proposals, not APIs or dependencies required by Tools;
see their [design history in PR #26](https://github.com/JulTob/Tag_Oriented_Programming/pull/26).

### 8. Refusals

Messages identify the Tag and Record. Test error types, binding state
and causes rather than exact prose.

| When | Failure | Required information |
| --- | --- | --- |
| Invalid kind (root `Tag`, `object`, a Pin, a population, a typing construct, an instance), union or scope | Declaration | the spellings meant, `@Tool(Weapon)`, `@Tool(Sword)`, `@Tool(Weapon, Blessed)`, `@Tool(Sword | None)` |
| Conflicting Contribution marks, a Report wrapping a Tool builder included | Declaration | Name and conflicting kind, in either decorator order. |
| Builder returns a value outside the kind, or disallowed None | Composition | `Fighter.weapon`, the kind, the term unsatisfied ("is not a Weapon now", "Tag it in the builder"); value not acquired. |
| Incompatible assignment, a Rogue under a Tag term ("this Sword left Weapon"), or disallowed None | Composition | Tool name and requirement; old binding unchanged. |
| Constant replacement or deletion | Existing Constant failure | Existing protection and diagnostics. |
| Existing Record collision | Existing composition failure | Ordinary Record collision rules. |

Compatible untagged values, deficient Agents, Rogues, self-reference and
sharing are permitted. None requires an explicit nullable union.

## Rationale and alternatives

**Ordinary Record, kind admission.** Existing storage, Overlay, presence
and protection supply the held value's structure. A permanently closed
Tool species would duplicate Constant's deliberate name protection.
Class checks, Tag membership and TOP Posts answer different questions;
this modifier must not silently substitute one for another, so the
author says which question the slot asks by naming a class, a Tag, or
both, and a Tag term is spelled as membership (`in T[:]`), never as
`isinstance`.

**Explicit effects.** A smith is an Action and training is an Imprint.
Automatic construction or Tagging behind a Record would require new
input and failure rules. The modifier needs neither.

**Record-only scope.** Return-value requirements on Actions are a
separate feature. This bounded choice is not a claim that the law against
Post-wrapping Actions forbids every possible return-value modifier.

Deferred alternatives: nested-class construction syntax, guarded Reports,
Links as inventories, ownership or exclusive hand-over, reverse queries,
and Tool display. A nested class may describe the host; declaring it
alone does not establish how and when TOP should construct or train it.
The ordinary Record pattern remains useful without this modifier.

## Backwards compatibility

Opt-in. Unmarked Records retain their behavior. Tool-marked Records add
class checks and reject None unless declared. A new public Tool import
may collide with a program's wildcard-import name. No set algebra,
Tagging order, Agent truth, automatic Action guard or cross-Agent
restoration rule is introduced by this STEP.

## Actualization plan

This revision records the Director's choices; the STEP remains Brief
until the Director changes its status. Implementation can be prepared
for review without representing that formal decision as already made.

1. **Proposal and patterns** (done): this STEP and the runnable wiki,
   the ordinary Record patterns and the `@Tool` blocks alike.
2. **Complete opt-in core** (done in PR #143): metadata, declaration
   validation, kind admission at gaining, guarded assignment and
   deletion, Presence, Secret/Constant, Overlay and retry, with
   `tests/test_tools.py`. The modifier guards writes, `object.__setattr__`
   included, on ordinary names; protocol names keep the language's hook
   and their documented kernel bypass.
3. **Capacity evidence** (done): the oracle's `Exercise_Tools` checks a
   Tag kind and a class kind on every seed; the opt-in budgets pass; the
   runtime type is shared across Agents whose slots differ only in kind.
   Retained Gains under STEP-SPEC-39 are re-checked when PR #78 lands.

Runtime descriptors must obtain the effective policy from Agent state,
not capture bearers or values in shared classes or cache keys. Presence
recognises dropped bindings without evaluating getters or Posts. Views
retain ordinary references. Keep host refusal rules and kernel writes,
including support for taggable frozen dataclasses.

Ordinary writes and supported host/Action setters need coherent preflight.
For ordinary names, a descriptor also checks object.__setattr__. Placing
that descriptor on a protocol name would instead replace Python's type
hook, so protocol-named Records keep their normal representation and
kernel-write bypass. Raw instance-dictionary mutation is likewise a
kernel bypass, not a sandbox promise. This modifier cannot undo external
effects of a custom setter. State and test supported paths and limits;
no line-count or performance estimate precedes measurement.

## Validation

Implemented in PR #143. Each item names where it is shown; all pass on
2026-10-13 with the full suite (`PYTHONPATH=. python3 -m unittest discover
-s tests -t .`), the opt-in budgets (`TOPKIT_PERF=1`) and the oracle at
its audited size (`--seeds 50 --steps 1200 --population 18`).

- invalid kinds (the root `Tag`, `object`, a Pin, a population, a typing
  construct, an instance, `None` alone, a bare `@Tool`) and conflicting
  marks fail by declared name in both decorator orders, a Report
  wrapping a Tool builder included: `Declaration_Tests`;
- a class kind admits untagged and actualized instances, subclasses,
  class alternatives, optional None and compatible self-reference; a
  different class is refused even when tagged Weapon, while a compatible
  Rogue remains admissible: `Class_Kind_Tests`;
- a Tag kind admits a member now, a member of a Shape and a deficient
  member; it refuses a non-member, a Rogue ("left Weapon") and the
  bearer until the bearer is of the kind; a kind of two Tags, and of a
  class and a Tag, asks for all; a union of a Tag and a class admits
  either: `Tag_Kind_Tests`, `Class_Kind_Tests`;
- bad initial values are not gained; on `main` today the whole call rolls
  back and the host keeps its own type
  (`test_a_builder_returning_a_non_member_refuses_the_gaining`); under
  STEP-SPEC-39 the same refusal leaves the Gains already acquired, to be
  re-run on that branch when PR #78 lands;
- ordinary and kernel-path writes preserve the old binding on refusal;
  dropping makes Presence false and reassignment stays guarded; a host's
  own setter runs only after admission; a frozen dataclass host gains
  through the kernel path: `Emptiness_Tests`, `Host_Tests`;
- a Tool under a protocol name keeps the language's hook (presence through
  `__rmatmul__`, lookup through `__getattribute__`), its ordinary writes
  are checked, and `object.__setattr__` on it is the documented bypass:
  `Host_Tests`;
- ordinary and Constant retries, Secret, Constant and Public stacking in
  either order, Overlay (a Shape's own kind, a plain Record or an Action
  ending the rule, an independent Record with the usual warning, the
  cross-kind refusal kept), `@Delete`, sharing and a tool that bears a
  tool: `Stacking_Tests`, `Overlay_Tests`, `Lifecycle_Tests`,
  `Sharing_Tests`;
- Rip of the bearer keeps the slot and its rule; Rip of the tool's Tag
  leaves a Rogue in hand that the bearer's Post notices; a `@Rip`
  protocol may disarm; an Imprint may fill a declared empty hand:
  `Lifecycle_Tests`;
- admission never evaluates the held object's truth or Posts: a defective
  member is admitted (`test_a_defective_member_is_admitted_the_promise_judges_it`);
  a failing instance test is a named Composition Failure with its cause,
  and an interrupt propagates unchanged: `Class_Kind_Tests`;
- the two doors: a bearer's Action reading its tool's Secret fails closed
  (`Sharing_Tests`);
- runtime-type sharing: Agents whose slots differ only in kind share one
  type, the gate reads each Agent's own kind, and the type retains no
  bearer or value (`Host_Tests`, `Sharing_Tests`);
- the Record-write budget and the other twelve of `tests/test_performance.py`
  pass: the gate is a descriptor for the Tool's name only;
- the oracle's `Exercise_Tools` checks a Tag kind (`Armed`, `Gear`) and a
  class kind (`Carrying`, `Agent`) on every seed, 60,000 transitions;
- the wiki page's 15 blocks run as one program under
  `tests/test_documents.py`; the Specification's §1.3 example runs in
  `tests/spec_examples.py`.

Known limit, shared with `@Constant`: a host whose instances cannot
change class in place (`__slots__` without a compatible layout) cannot be
actualized, and the kit says so with the existing Composition Failure.

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
