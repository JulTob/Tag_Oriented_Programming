# STEP-SPEC-28: Category Error

- **STEP:** SPEC-28
- **Desk:** spec
- **Title:** Category Error
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A new named failure, the **Tag Category Failure**, `TagCategoryError`.
It is raised when a program treats one kind of TOP thing as another kind:
a value of the Tag written over a name the Tag gives its Agents, a
population used as a type, a Projection asked a population's question,
an ordinary Tag applied to a class. Nothing changes when it is raised.
It is a `TagError`, and also a `TypeError`, so code that catches
`TypeError` today keeps working.

```python
class Wizard(Tag):

    @Record
    def hp(agent, stored) -> int:
        return 5

Wizard.hp = 10        # TagCategoryError: hp is a Record of each Wizard,
                      # not a value of the Tag Wizard.
                      # Write: for wizard in Wizard: wizard.hp = 10
```

## Motivation

The Director, on 2026-10-08: "you were right if Wizard.hp is a record,
doing "Wizard.hp = 10" should probably rise a category error, as it is
probably a misconception." And: ""Category error" should be a type of
error in tags. it will come in handy."

A *category error* is the philosopher Gilbert Ryle's name for giving a
thing a property that belongs to another kind of thing. TOP has several
kinds that look alike in Python's syntax: a Tag, its Agents, a
population, a Projection, a Pin, a Relation. Today the mistakes between
them fail in scattered ways, or not at all:

- `Wizard.hp = 10`, when `hp` is a Record, raises nothing. What it does
  depends on timing (checked on TopKit 0.2.0a4): before the Tag's first
  use it erases the Record, so new Wizards, and the Agents of its Shapes,
  get no `hp`; after, every Agent still gets the Record, because the kit
  read the declaration at first use, but `Wizard.hp` now reads 10: the
  Tag and its Agents disagree (STEP-SPEC-23, section 6).
- `Wizard(int)` raises a plain `TypeError`: "Wizard is applied to
  objects, not classes".
- `isinstance(x, Wizard | Fighter)` raises Python's generic `TypeError`
  on `main`; the `step-19-sound-in` line refuses it with a named rewrite,
  still a plain `TypeError` (STEP-SPEC-13, item 5).
- STEP-SPEC-23 refuses `ruth in Wizard.level` and `bool(Wizard.level >
  3)` with plain `TypeError`s.

One name for one kind of mistake lets a program catch it, a test assert
it, and a reader recognise it.

## Specification

1. **The failure.** `TagCategoryError` is a subclass of `TagError` and of
   `TypeError`. The Failure model (§ Failure model) gains a row:

   | Failure | When | Effect |
   | --- | --- | --- |
   | **Tag Category Failure** | An act treats one kind of TOP thing as another: a Tag as its Agents, a population as a type, a Projection as a population. | refused, nothing changed |

2. **Its message names both kinds and the spelling to use.** "hp is a
   Record of each Wizard, not a value of the Tag Wizard. Write: for
   wizard in Wizard: wizard.hp = 10".
3. **Where it is raised.** Each case keeps the rule that already refuses
   it, and its message's rewrite; only the class of the failure is new.
   Four cases are new refusals, decided by the Director on 2026-10-09: a
   target that cannot be an Agent, a target with a truth of its own, a
   string target, and a Flag on a host with its own `in`.
   - **A value of the Tag over a name the Tag gives its Agents.**
     Assigning or deleting on a Tag a name it declares for its Agents (a
     Record, an Action, a condition): `Wizard.hp = 10`, `del Wizard.hp`.
     Refused at once, before anything changes. A name the Tag also
     holds in Tag scope, such as a Report `colour` beside a Record
     `colour` (§1.1), stays writable: the write changes the Report.
     Assigning a name the Tag does not give its Agents stays allowed: it
     is a Report written by hand (the Director: "if it looks like a
     report, then it is, and we just have more than one way to handle
     that"). STEP-SPEC-25, rule 4.2, refuses the same writes, with the
     same exception; this STEP names the failure.
   - **A Tag applied to the wrong kind of target.** An ordinary Tag
     applied to a class, `Wizard(int)`, and a Pin applied to an object
     (§1.9).
   - **A target that cannot be an Agent.** `Wizard(None)`, `Wizard(3)`,
     `Wizard(True)`, and any other value with no instance dictionary or
     no weak reference (a plain `str`, a `tuple`). Decided by the
     Director on 2026-10-09: "Wizard(None), Wizard(3), Wizard(True) those
     should all be category errors." On `main` these are Composition
     Failures today ("int cannot carry TOP state").
   - **A target with a truth of its own.** A host class that defines
     `__bool__` is refused at tagging. An Agent's truth is its contract
     (`if ari:` asks whether its promises hold), and a host's own truth
     would answer instead. Decided by the Director on 2026-10-09:
     "bool(ari), when ari's host class has its own __bool__ should be a
     category error to tag a target with bool behaviour. Bool-like
     behaviour conflicts with contracts. should be refused. (Or at least
     underlayed by the contracts). any bool behaviour can be set in a
     record or attribute, not directly on the target." A host that only
     defines `__len__` takes its truth from its length; open question 2
     asks about it.
   - **A target that is a string.** An instance of a `str` subclass is
     refused at tagging: `"Undead" in Wizard` reads a string as a Flag
     word (§1.9), so a string Agent could never answer `in` as a member.
     Decided by the Director on 2026-10-09: "s in Sworn, where s is an
     Agent made from a str subclass should be refused at tagging as a
     category error."
   - **A Flag on a host with its own `in`.** A Tag marked `@Flag` is
     refused on a target whose host class defines `__contains__`. On an
     Agent, `Wizard in ari` and `"Wizard" in ari` are the host's own
     question when it has one, and Flag words otherwise (§1.8). Decided
     by the Director on 2026-10-09: "Wizard in ari, "Wizard" in ari
     (Wizard is not a Flag) should be the underlaying object behavior,
     and flags should be refused on objects or agents with defined in
     behavior."
   - **A Projection asked a population's question.** `in` and `not in` on
     a Projection (STEP-SPEC-23, rule 1.8), and `bool()` of a Projection,
     a Filter, or a combination that holds one (STEP-SPEC-23, section 5).
   - **A population used as a type.** `isinstance(x, Wizard | Fighter)`,
     and `Wizard | Fighter | None` (STEP-SPEC-13, item 5, on the
     `step-19-sound-in` line).
   - **A Pin's population mixed with a Tag's**, `Combat | Wizard`
     (STEP-SPEC-13, item 6, on the same line). Decided by the Director
     on 2026-10-09: "Rare | Wizard should raise a category error. Pins
     are pinable, but the return population of pins are tags, but tags'
     populations are agents."
   - **A Relation used as a Tag.** `Scope(x, Social.Knows)` and
     `isinstance(x, Social.Knows)` (STEP-SPEC-22, section 9).
4. **What is not a category error.**
   - A Tag written wrong, at class use, is a Declaration Failure (§
     Failure model): the mistake is in the declaration, not in an act.
   - The right kind of thing in the wrong state is a Resolution Failure:
     a view of an Agent that is not a member, a Rogue Agent's published
     member.
   - A refused tagging is a Precondition Failure.

## Rationale

**A TOP failure and a Python one.** Python raises `TypeError` when an
operation meets the wrong kind of value. A category error is that
mistake, one level up: the wrong kind of TOP thing. Being both lets a
TOP program write `except TagCategoryError`, and lets code that does not
know TOP keep its `except TypeError`.

**Refused, not repaired.** The kit could guess what `Wizard.hp = 10`
meant: write every member, or keep a value of the Tag. Each guess is
right for some programs and silently wrong for others. The Director:
"it is probably a misconception". A refusal that prints the right
spelling teaches it.

**One class, not one per case.** The cases differ in the kinds involved,
not in what a program does about them: it fixes the line. The message
carries the difference.

## Backwards compatibility

1. `Wizard.hp = 10` over a declared Agent name was accepted silently, and
   is now refused. A program that did it was already broken, in a way
   that depended on timing.
2. Two cases were a Composition Failure and become a Category Failure:
   a Pin applied to an object (§1.9), and, without STEP-SPEC-23, a
   Relation used as a Tag (STEP-SPEC-22, section 9). Code that catches
   `TagCompositionError` there must catch `TagCategoryError`. A Pin's
   population mixed with a Tag's is allowed on `main`; it is refused only
   with STEP-SPEC-13, item 6. Every other case was already a `TypeError`
   and still is, because `TagCategoryError` is a `TypeError`. The
   messages keep their rewrites. A target that cannot be an Agent,
   `Wizard(3)`, was a Composition Failure too, and becomes a Category
   Failure.
3. Three kinds of target that could be tagged before are now refused:
   a host class with its own `__bool__`, a `str` subclass, and, for a
   Flag, a host class with its own `__contains__`. A program that tagged
   one keeps its truth, its text or its `in` in a Record or an attribute
   instead, as the Director says.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Plain `TypeError` everywhere (today) | Works, but a program cannot tell a TOP mistake from any other, and `Wizard.hp = 10` stays silent. |
| `TagCompositionError` | That failure is about forming an Overlay. A category error happens before anything is composed. |
| `TagDeclarationError` | That failure is about how a Tag is written, at class use. A category error is an act on a correct Tag. |
| A failure per case, `TagCategoryError.Projection_In` | The program's fix is the same in every case: change the line. The message says which. |

## Open questions for the Director

1. **The list.** Section 3 gathers the refusals found so far, from four
   STEPs on three lines of work. Should every one of them move to this
   failure, and should a refusal added later join it by default when it
   is about the wrong kind of thing?
2. **A host with `__len__`.** Python takes an object's truth from
   `__len__` when it has no `__bool__`: an empty container is false.
   Refusing every such host would refuse every container-like Agent, a
   `Shelf` of books for example. Recommended: the Director's "(Or at
   least underlayed by the contracts)". The Agent's truth is its contract
   (`bool(agent)` asks the promises), and `len(agent)` stays the host's.

## Acceptance requirements

- `TopKit/errors.py`: `TagCategoryError(TagError, TypeError)`, exported
  from `TopKit`.
- `tests/test_topkit.py`: a `CategoryErrorTests` class, covering:
  - `Wizard.hp = 10` and `del Wizard.hp` over a Record, an Action and a
    condition, before and after the Tag's first use: refused, and the
    Tag and its Agents unchanged;
  - assigning a name the Tag does not give its Agents still works;
  - `Wizard(int)` raises `TagCategoryError`, and `except TypeError`
    still catches it;
  - `Wizard(None)`, `Wizard(3)`, `Wizard(True)`, a host with
    `__bool__`, a `str` subclass, and a Flag on a host with
    `__contains__`: each refused at tagging, nothing changed;
  - each other case in rule 3, once its STEP is built.
- The Specification's Failure model gains the row of rule 1.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Asked for by the Director on 2026-10-08:* ""Category error" should be
> a type of error in tags. it will come in handy."
