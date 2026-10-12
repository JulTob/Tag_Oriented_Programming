# STEP-SPEC-36: Tools

- **STEP:** SPEC-36
- **Desk:** spec
- **Title:** Tools: class admission for a Record that holds an object
- **Author:** Julio Toboso (@JulTob); originally drafted with Claude Code
  from the Director's brief of 2026-10-12
- **Review refinement:** Codex, 2026-10-12
- **Status:** Brief
- **Created:** 2026-10-12
- **Refs:** PR #143; STEP-SPEC-33 (Presence), STEP-SPEC-34 (Constant),
  STEP-SPEC-39 (Tagging Admission, Cleared, PR #78), STEP-SPEC-40
  (Agent contract truth, Brief, PR #151), STEP-SPEC-42 (condition names,
  Brief, PR #155), issues #30, #71 and #74, and PR #156

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A **Tool** is an object an Agent *has*, held as a Record value. It can be
an Agent in its own right: a Fighter holds a sword, the sword may be
Cursed, and the Fighter does not thereby become Cursed. This is *tener*,
beside a Tag's *ser* and a Record's *estar*.

An ordinary Record already holds such an object. This STEP proposes the
modifier `@Tool(Class)` to check its **Python host class** when that
Record is gained or assigned. It does not require Tag membership, create
an object, or train it. Records read and calculate initial values;
Actions and Imprints perform training and other effects.

```python proposed
class Sword:
    def __init__(self, name):
        self.name = name


class Fighter(Tag):

    @Tool(Sword)                 # implies Record; @Record may restate it
    def weapon(agent, *, weapon):
        return weapon           # a Sword instance, tagged or untagged

    @Post
    def Armed(agent):
        return ("weapon" @ agent
                and agent.weapon in Weapon[:]
                and Contract.Holds(agent.weapon))

    @Action
    def Strike(agent):
        if not agent.Armed:
            raise RuntimeError("a sound Weapon is required")
        return agent.weapon.Swing()


sword = smith.Forge()            # an Action creates and Tags the Sword
Fighter(charlie, weapon=sword)
```

Here `Sword` is a Python class and `Weapon` is a Tag. A plain Sword passes
Tool admission. The optional Post `Armed` additionally requires that it
be a current, sound Weapon. Tagging does not change its host identity.
A Weapon made from a different host class fails this Tool declaration.

The added rule is **class compatibility at admission**, not continuous
Tag membership or validity. A seated object that later leaves Weapon's
Field stays held. Its host class still qualifies; the bearer's Posts
control whether it can be used.

| Question | Spelling | Meaning |
| --- | --- | --- |
| Does the Gain exist? | `"weapon" @ agent` | Presence; no value read or Post evaluation. |
| Is the object currently a Weapon? | `agent.weapon in Weapon[:]` | Tag membership, including deficient members. |
| Do its promises hold? | `Contract.Holds(agent.weapon)` | Its visible Posts, independently of the bearer. |
| Is an Agent Tool valid? | `bool(agent.weapon)` | Agent contract truth; plain objects retain Python truth. |

**Implementation status.** `@Tool` is proposed, not exported by TopKit.
The [wiki pattern](https://github.com/JulTob/Tag_Oriented_Programming/wiki/1.4-TopKit-Tools)
uses ordinary Records today. This proposal follows the Director's approved
Tagging order and truth decisions. Main may still implement earlier
behavior until the prerequisite changes land; that history is not a
second normative law for Tools.

## Director's decisions recorded in this revision

The Director confirmed:

- **Ordinary Overlay:** Rip and dropping a value preserve the Tool rule;
  `@Delete` or a permitted plain Record/Action Overlay ends it. Constant
  provides stronger protection.
- **Self-reference:** allowed when the bearer satisfies the declared
  host class. An author may forbid it with a Post.
- **Class, not Tag:** `@Tool(Weapon | None)` means instances of the Python
  host class named Weapon, or None; no Weapon Tag membership is required.

The names in the examples deliberately distinguish the host `Sword`
from the Tag `Weapon`. This supersedes the first draft's Field-based
admission rule and its automatic self-reference refusal. It does not
reopen the meaning of `in`, Agent truth, or the accepted Tagging order.

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
Tool can be untagged, Rogue or deficient. Those questions belong to
membership and Posts, not class admission.

## Specification

### 1. Vocabulary and scope

| Term | Meaning |
| --- | --- |
| **Tool** | An object held as the value of a Tool-marked Record; it may itself be an Agent. |
| **Bearer** | The Agent receiving the Record; ownership is a domain question. |
| **Declared class** | The Python host class admitted by the Record. It is not a Tag or population. |
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
2. The initial spelling takes one Python host class or Python class
   union. Union alternatives retain Python's **or** meaning:
   `@Tool(Sword | Staff)` admits either class. `@Tool(Sword | None)` also
   admits None. A declared base class admits its subclasses, including
   the runtime classes TOP uses to actualize its instances.
3. Tag classes, including the root Tag and Pins, are not host-class
   requirements. Populations such as `Weapon | Blessed`, `~Weapon` and
   `Weapon[:]` are refused too. This distinction prevents accidental use
   of a Tag's historical `isinstance` behavior as a membership check.
   Required current Tags belong in Posts.
4. No argument, None alone, a non-class, or a union containing a Tag or
   unsupported non-class is a Declaration Failure. The initial spelling
   does not add multiple positional class requirements or reinterpret
   class unions as conjunctions. Parameterized typing expressions and
   protocols with no runtime instance test are outside this first scope.
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
   binding. Class acceptance follows Python's runtime instance check;
   None is accepted only when explicitly included.
2. Admission does not require that the object be an Agent, inspect its
   Field membership, evaluate its Posts, or invoke its truth protocol.
   An untagged compatible object, a deficient Agent and a compatible
   Rogue are all admitted.
3. Supported Record assignment paths share the check, including
   `object.__setattr__` for ordinary names. A refused write keeps the
   prior binding and declaration intact. Existing Secret, Constant and
   host compatibility checks still apply.
4. Reading does not revalidate. Tagging or Rip of the held object does
   not update or remove the reference. Reassigning a compatible Rogue is
   permitted: only a separate domain Post requires current membership.
5. Self-reference is allowed when the bearer satisfies the class. This
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
binding. It also skips fresh class admission. Constant protects the
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
STEP-SPEC-42, with implementation in PRs #155 and #156:

- For ordinary object Agents, bool asks whether visible Posts hold,
  including before Field entry when Posts have already been gained.
- Hosts with explicit or inherited `__bool__` are refused before Tagging
  effects. Tool admission alone does not Tag a host, so it does not
  trigger that eligibility check.
- Plain objects retain Python truth, including their own `__bool__`.
  Holding one does not make it an Agent or give it TOP contract truth.
- Conditions cannot use dunder names, and ordinary Agent truth cannot be
  replaced by another Contribution.
- `bool(Tag)` keeps population truth even when a Pin makes the Tag an
  Agent. `Contract.Holds(Tag)` asks its Pin contract. This proposal does
  not change Tag population truth. A host-class rule such as `@Tool(type)`
  may admit a Tag value; holding it does not change either truth question.

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
| Invalid class, union, population or scope | Declaration | Tool name and an accepted spelling such as `@Tool(Sword | None)`. |
| Conflicting Contribution marks | Declaration | Name and conflicting kind, in either decorator order. |
| Builder returns incompatible value or disallowed None | Composition | `Fighter.weapon`, unsatisfied class; value not acquired. |
| Incompatible assignment or disallowed None | Composition | Tool name and requirement; old binding unchanged. |
| Constant replacement or deletion | Existing Constant failure | Existing protection and diagnostics. |
| Existing Record collision | Existing composition failure | Ordinary Record collision rules. |

Compatible untagged values, deficient Agents, Rogues, self-reference and
sharing are permitted. None requires an explicit nullable union.

## Rationale and alternatives

**Ordinary Record, class admission.** Existing storage, Overlay, presence
and protection supply the held value's structure. A permanently closed
Tool species would duplicate Constant's deliberate name protection.
Class checks and TOP Posts answer different questions; this modifier
must not silently substitute Field membership for a Python class.

**Explicit effects.** A smith is an Action and training is an Imprint.
Automatic construction or Tagging behind a Record would require new
input and failure rules. The proposed modifier needs neither.

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

1. **Proposal and patterns:** this STEP and the runnable wiki; distinguish
   available Record patterns from proposed Tool syntax.
2. **Complete opt-in core:** metadata, declaration validation, class
   admission at gaining, guarded assignment and deletion, Presence,
   Secret/Constant, Overlay and retry, with regression tests. Do not
   export a modifier that checks initial values but leaves writes open.
3. **Capacity evidence:** extend the oracle and performance checks on
   the agreed implementation, including retained Gains and runtime-type
   sharing. Defer new construction syntax and scopes.

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

Before proposing implementation for merge, demonstrate:

- invalid classes, Tag classes, populations, unions, scope and conflicting
  marks fail by declared name in both decorator orders;
- untagged and actualized host instances, subclasses, class alternatives,
  optional None, and compatible self-reference are admitted;
- a different host class is refused even when tagged Weapon, while a
  compatible Rogue remains admissible;
- bad initial values are not gained, with earlier Gains retained under
  STEP-SPEC-39 and declaration-order visibility preserved;
- ordinary and kernel-path writes preserve old bindings on refusal;
  dropping makes Presence false and reassignment remains guarded;
- protocol-named Records preserve ordinary lookup, presence and Agent
  finalization; their stated direct-kernel bypass remains explicit;
- ordinary and Constant retries, Secret/Constant stacking, frozen hosts,
  Overlay, Delete, sharing and views follow existing patterns;
- early Posts guard retained unsafe Gains on a Rogue; Tool admission and
  reads never evaluate the held object's truth or Posts;
- plain objects with __bool__ can be held, while later Tagging still
  enforces the independent Host eligibility rule;
- runtime-type sharing with different class policies does not mix rules
  or retain bearers or held values;
- executable documentation and the full suite pass; the oracle and opt-in
  budgets measure the changed paths.

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
