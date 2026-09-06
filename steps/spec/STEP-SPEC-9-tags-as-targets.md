# STEP-SPEC-9: Tags as Targets (Pins)

- **STEP:** SPEC-9
- **Desk:** spec
- **Title:** Tags as Targets (Pins)
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting
- **Created:** 2026-09-05

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A Tag may be the Target of another Tag. STEP-SPEC-1 named this act
**pinning** and gave it its one law: the receiver decides the scope, so a
Pin's Agent-scope members land in the pinned Tag's **Tag scope**. This STEP
makes that law observable. A Tag declared `@Pin` applies to Tags and to
nothing else; its Field is a population of Tags; membership, contracts,
views and Rip work exactly as they do for objects, with the Tag as the
Agent. Ordinary Tags keep refusing classes, loudly.

```python
@Pin
class Rare(Tag):

    @Record
    def rarity(tag):                     # lands as Wizard.rarity, a Report
        return "rare"

    @Action
    def Describe(tag):                   # lands as Wizard.Describe, an Operation
        return f"{tag.__name__} is {tag.rarity}"


Rare(Wizard)

assert Wizard in Rare                    # active membership, from the Pin's side
assert list(Rare) == [Wizard]            # the Field of Tags
assert Wizard.rarity == "rare"           # Tag scope: shared by the whole Field
assert Wizard.Describe() == "Wizard is rare"
assert not hasattr(ari, "rarity")        # never on the Agent (§1.4)
```

## Motivation

Categories have categories. A game marks Tags as *Rare*, *Homebrew* or
*Deprecated*; a rules engine keeps a table of Tags by *School*; a tool
walks "every Tag that is Deprecated" to warn. Today this is done with a
Report per Tag and a plain set outside TOP, which loses what TOP is for:
membership as an act, a Field to walk, a gate that can refuse, a promise
that can be checked, and a Rip that ends membership without erasing
history.

The paradigm already says the Tag is an object with its own scope (§1.1)
and STEP-SPEC-1 already wrote the Pin rule: "When a Tag is applied to
another Tag, an Action may be adapted into an Operation and a Record may be
materialized as a Report. The resulting contributions occupy Tag scope
because the Pinned Tag is their receiver." The Specification rewrite of
2026-09-04 kept the two-scope law but did not carry the Pin sentence, and
neither TagKit 0.1 nor 0.2 ever accepted a class as a Target. This STEP
restores the rule as its own topic and gives it a shape that can be built
and tested.

## Specification

### 1. Vocabulary

| Term | Meaning |
| --- | --- |
| **Pin** | A Tag declared `@Pin`. Its Targets are Tags. |
| **Pinning** | Applying a Pin to a Tag: `Rare(Wizard)`. |
| **Pinned Tag** | A Tag that belongs to at least one Pin. It is the Agent of that Pin. |

`Pin` is a mark on the Tag class, like `@Flag`. It is not a Base and does
not appear in the Form.

### 2. Who may be a Target

1. A Pin applies to Tags only. `Rare(ari)` on an object is refused with a
   Composition Failure: "Rare is a Pin: apply it to a Tag".
2. An ordinary Tag applies to objects only. `Wizard(Elf)` stays refused,
   as today.
3. A Pin is a Tag, so a Pin may be pinned: `Meta(Rare)`. A Pin may not be
   its own Target; `Rare(Rare)` is refused.
4. A Pin's Field holds Tags only. Fields never mix Agents and Tags.

### 3. The receiver rule (from STEP-SPEC-1)

The Pinned Tag is the Agent of the Pin. Every contribution keeps its kind
by receiver, so:

| Declared in the Pin | Lands on the Pinned Tag as | Receiver |
| --- | --- | --- |
| `@Action def f(tag, ...)` | an **Operation** | the pinned Tag |
| `@Record def r(tag, stored)` | a **Report** value, built once at pinning | the pinned Tag |
| `@Operation`, `@Report` | stay on the Pin, in the Pin's own Tag scope | the Pin |
| `@Pre`, `@Post`, `@Imprint`, `@Rip`, `@Delete` | protocols of the pinning, receiving the pinned Tag | the pinned Tag |

The first parameter of a Pin's Agent-scope member is the pinned Tag. The
Guide spells it `tag`, not `agent`, so the receiver reads right.

A Record landed by a Pin is a Report of the pinned Tag: one value for the
whole Field, held on the Tag, extended by a Shape through the `inherited`
seat (§1.4), and inherited by the pinned Tag's Shapes the way every Report
is. Membership does not inherit: `War_Caster in Rare` is False unless
`Rare(War_Caster)` was applied.

### 4. One slot per scope and name

A Pin **adds** to a Tag; it never replaces what the Tag declares. On an
object, an Action shadows a host method in the instance dictionary and
the host keeps its own; a Tag's own dictionary *is* its host, so the same
write would destroy the declaration. Therefore:

- A Pin member may not use a name the pinned Tag declares itself or
  inherits from a Base (its Operations, Reports, Actions, Records or
  conditions). The pinning is refused at the gate with a Composition
  Failure; nothing changes.
- A Pin member may not use a name every Tag already answers through its
  metaclass (`mro`, `__name__`, the TOP acts). Refused at the gate.
- Names another Pin landed are TOP-managed: two Pins on one Tag follow
  the Overlay laws of §1.2 and §1.3, independent Pins warn, Pins in one
  Form overlay in Form order, `@Underlay` extends, the view keeps the
  prior.

### 5. Publication

Pinned members are Tag scope: readable on the Tag, `Wizard.rarity` and
`Wizard.Describe()`, as every Report and Operation is (§1.7, direct Tag
access), and **never projected onto the Tag's Agents**: `ari.rarity` does
not exist. That is the whole of STEP-SPEC-3 for a Tag receiver.

A Pin's members are **plain**. `@Secret`, `@Public` and `@Delete`, and
special-method Actions, are refused at declaration with a Tag
Declaration Failure. Each of them would put a descriptor or a hook on
the Tag's metaclass, and none has a meaning there yet; a later STEP may
give them one.

### 6. Spellings

Every Tag-level act of §0.8 applies, with a Tag in the Agent's seat:

| Act | Spelling |
| --- | --- |
| pin | `Rare(Wizard, **inputs)` |
| active member? | `Wizard in Rare` |
| ever a member? | `isinstance(Wizard, Rare)` |
| the sound population | `for tag in Rare`, `len(Rare)`, `if Rare:` |
| the defective population | `for tag in ~Rare` |
| everyone in the Field | `Rare[:]` |
| the Tag-bound view | `Rare[Wizard]` |
| leave the Field (Rip) | `del Rare[Wizard]` |
| a Tag's Pins, as text | `f"{Wizard:pins}"` |
| a Tag's contract, as text | `f"{Wizard:contract}"`, `Contract.Display(Wizard)` |

Two seats are already taken on a Tag and stay as they are:

- `bool(Wizard)` remains "is anyone a sound Wizard" (§0.8). A pinned Tag's
  own promises are read from the Pin's side: `Wizard in ~Rare`.
- `x in Wizard` remains membership, so a Pin cannot be a Flag: `@Flag`
  and `@Pin` together are refused at declaration. A word on a Tag is a
  Report.

`Wizard.Rare` reads the Pin-bound view by name, as `ari.Wizard` does on
an Agent, on the same miss-path rule.

### 7. Contracts, Imprints and Rip

A Pin's Preconditions gate the pinning and receive the Tag:
`@Pre def Has_Members(tag): return bool(tag)`. Postconditions are checked
once per pinning and re-checked at later pinning boundaries of that Tag;
a broken promise leaves the Tag pinned and defective (STEP-SPEC-4).
Imprints run after commit with the Tag as receiver. `del Rare[Wizard]`
runs the Pin's Rip protocol; landed Operations and Report values stay,
sticky, and `isinstance(Wizard, Rare)` stays True. Pinning again after a
Rip is a fresh pinning and silent: a Tag replacing its own earlier
promise is not a Shape weakening a Base. (This closes the same gap for
objects: re-applying a Ripped Tag with a Postcondition warned in
0.2.0a2.)

A Pin does **not** change the pinned Tag's own gate over its Agents. A
Deprecated Tag that should refuse new members writes that as its own
Precondition reading its Pins: `return self_tag not in Deprecated`. A
later STEP may give Pins that reach.

### 8. Identity and history

The pinned Tag keeps its identity: `is`, `id`, hash, name, module and
Form are unchanged; its Shapes keep their own metaclass. Its nominal
metaclass may be wrapped, as an Agent's type is (Ring 4). Snapshots and
rollback cover the Tag's namespace the way they cover an Agent's.

## Rationale

**`@Pin`, not "any Tag on any class".** Fields are the query surface of
the paradigm; `for w in Wizard` must never yield a class. An opt-in mark
keeps every Field homogeneous, keeps the refusal on ordinary Tags loud,
and follows the precedent of `@Flag`: name the concept, contain the risk.

**The receiver rule, not a third scope.** Two scopes were enough because
the receiver decides. A Pin does not introduce "meta scope"; it is a Tag
whose Agent happens to be a Tag, and everything it contributes is read by
the scope of that receiver. This is STEP-SPEC-1's sentence made testable.

**Records become Reports, not class attributes with special rules.** A
Report is already "one value held on the Tag, inherited by Shapes,
extended through the second seat". Landing a Pin's Record as a Report
reuses those laws instead of inventing near-copies.

**Internal by default.** Tag scope is internal (STEP-SPEC-3). A Pin that
wants `Wizard.rarity` readable from main says `@Public`, one word, the
same word a Report uses.

## Backwards compatibility

No existing program changes. Ordinary Tags keep refusing classes with the
same error. `@Pin` is new. `Contract` and format specs gain a Tag receiver.
STEP-SPEC-1's Pin sentence returns to the Specification under §1.1 with a
pointer to this STEP.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Any Tag accepts a class as Target | Rejected: Fields would mix Agents and Tags; `for w in Wizard` could yield a class |
| A separate `MetaTag` base class instead of a mark | Set aside: puts Pin into the Form and Outline of every Pin; `@Flag` precedent chosen |
| Pin Records as plain class attributes, no Report laws | Rejected: two sets of rules for one thing; inheritance and the second seat would need restating |
| Pinned members public by default (Agent-scope default) | Rejected: they live in Tag scope, and Tag scope is internal (STEP-SPEC-3) |
| `bool(Wizard)` answers the Tag's own contract when pinned | Rejected: the seat means "any sound member" and a Tag-level meaning must not depend on whether a Pin exists |
| Pins that alter the pinned Tag's gate over its Agents | Deferred to a later STEP; the pinned Tag can read its Pins in its own Precondition today |
| Reports plus a set of Tags outside TOP (today) | Kept as the fallback; it lacks membership acts, gates, promises and Rip |

## Acceptance requirements

To be covered by `tests/test_tagkit.py::PinTests`:

1. `Rare(Wizard)`: membership, Field, `isinstance`, `len`, `bool`, `~Rare`,
   `Rare[:]`, `Rare[Wizard]`, `del Rare[Wizard]`, rollback on a failed
   gate, defective Tag on a failed promise.
2. Receiver rule: a Pin Record reads as a Report of the pinned Tag and is
   inherited by its Shapes; a Pin Action calls as an Operation with the
   Tag as receiver; neither appears on any Agent.
3. Refusals: a Pin on an object, an ordinary Tag on a class, a Pin on
   itself, a Pin Record over the Tag's own Report, reserved names.
4. Publication: internal by default; `@Public` publishes; the door opens
   from the pinned Tag's own protocols.
5. Identity: `id`, hash, `__name__`, Form and the Shapes' metaclass are
   unchanged by pinning.
6. Every Guide and Specification block for Pins runs.

## TagKit notes

Built on the 0.2 kernel without a new mechanism (0.2.0a3): the runtime
type of a pinned Tag is a `(MetaTag, Tagged)` metaclass assigned through
`__class__`, as an Agent's is; state lives in the class namespace under
the same key, written through a small adapter over the class dictionary;
rollback restores the namespace key by key, since a class namespace has
no `clear`; a landed Action is a descriptor that binds to the Tag it is
read from, as a classmethod does; a landed Record is a plain class
attribute, which is what a Report's value is; Fields hold classes by weak
reference as they hold objects. The Tag's own scan skips TOP-managed
names, so a pinned Tag applied to an Agent never projects its pinned
members. Agents' paths are untouched: tagging costs the same and the
membership check got faster (`_state_of` reads the dictionary directly).

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-06, per the
> Director's direction ("Establish a STEP for Tags as Targets. The Pins we
> established in the last version are a good basis for it"; "Implement the
> step with optimized code").
