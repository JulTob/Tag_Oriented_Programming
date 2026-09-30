# STEP-SPEC-14: A Condition Is Read on the Agent by Its Name

- **STEP:** SPEC-14
- **Desk:** spec
- **Title:** A Condition Is Read on the Agent by Its Name
- **Author:** Julio Toboso (@JulTob)
- **Status:** Vetting
- **Created:** 2026-09-21

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

Every condition on an Agent can be read on the Agent by its own name, as
a plain boolean computed on read: `agent.Has_Book` is True while the
promise called `Has_Book` holds and False when it does not. Nothing lands
on the Agent: the name answers on the miss path, so no value is stored
and no proxy stands in for the boolean. The member and
`Contract.Status(agent)` give the same True or False. A condition that
returns anything but True, False or None raises the Contract Failure on
the member, while the status reads it as False, and so does
`bool(agent)` for a Postcondition. Because the name is read on the
Agent, **a condition may not share its name** with an Action, a Record,
a member the host defines, or a value the Agent already holds; the
tagging is refused at the door.

## Motivation

The 0.2-alpha line offered `agent.Has_Spellbook` and `agent.Has_Spellbook()`
as one member; the 2026-09-04 review Redacted it with uniform access
because the thing behind the name was a proxy that leaked into host
code. What was lost with it was the one-name read: asking about one
promise without asking about all of them. `Contract.Status(agent)["Has_Book"]`
does it, at the cost of a dictionary in the middle of an `if`. The
Director, 2026-09-21, chose the member back, as a plain bool: "Bring
back the Agent member."

## Specification

1. **Read.** For every visible Precondition and Postcondition called
   `Name`, `agent.Name` is `True` or `False`: the condition evaluated on
   read, under the same re-entrancy guard as `bool(agent)`. A
   Postcondition is looked up before a Precondition of the same name
   (a `@Requirement` is one function; both answer the same). A gate is
   read now, without the tagging's inputs: a later read calls it with its
   defaults, so `@Pre def Has_Code(agent, code=None): return code ==
   "007"` reads False once the call is over, and a gate that requires an
   input reads False.
2. **Plain.** The value is the language's boolean and nothing else. It is
   not stored on the Agent, cannot be assigned, and is not callable.
3. **A condition that raises reads False; a non-boolean raises.** A
   condition that returns something other than True, False or None (0,
   say) raises the Contract Failure on read. `Contract.Status(agent)`
   reads it as False. For a Postcondition, `bool(agent)` reads False too
   and the Agent waits in `~Tag`: the member names the defect, the status
   counts it. A gate is not part of `bool(agent)`.
4. **The name is the condition's own.** A tagging whose condition is
   called like an Action or a Record already on the Agent, like a
   member the host class defines, or like a value the Agent already
   holds, is refused with a Composition Failure at the door; so is an
   Action or a Record laid over an existing condition's name. Nothing is
   silently shadowed.
5. **Pins.** A pinned Tag reads its own conditions the same way:
   `Wizard.Has_Members`.
6. **Sticky.** A condition that outlived its Tag (STEP-SPEC-12) still
   reads by name until the author ends it.
7. **Spelling.** `agent.Has_Book` joins §0.8 beside `Contract.Status`.
   `hasattr(agent, "Has_Book")` is True for a condition on the Agent that
   returns True, False or None; for one that returns anything else,
   `hasattr` and `getattr(agent, "Has_Book", None)` raise the Contract
   Failure, as the read does. A name that is no condition is the
   ordinary attribute miss.

## Rationale

The proxy was the problem, not the name. A boolean computed on read is a
value, leaks nothing, and needs no call form. Answering on the miss path
keeps the kernel's rule that nothing TOP-level is written into the
Agent's namespace, and makes the collision rule the only new law: it
protects the reader from a condition that a Record of the same name
would hide.

## Backwards compatibility

A program that used a Record, an Action or a host member with the same
name as one of its conditions now fails at the door where before the
condition was simply unreadable by name.

`hasattr(agent, "Has_Book")` and `getattr(agent, "Has_Book", None)` gave
False and None in 0.2.0a3. Now they give True and the value for a
condition on the Agent, and raise the Contract Failure when it returns a
non-boolean.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| `Contract.Check(agent, "Has_Book")` | Set aside by the Director: the member reads best |
| A callable member (`agent.Has_Book()`) as well | Rejected with uniform access: needs a proxy |
| Land the member as a descriptor on the runtime type | Rejected: per-Agent runtime types, or a shared type that lies for Agents without the condition |
| Let a Record shadow a condition of the same name silently | Rejected: a silent shadow is the thing the read is for |

## Acceptance requirements

Covered by `tests/test_topkit.py::ConditionMemberTests` and by the
oracle (`Assert_Contract`), which reads every condition by name after
every transition and compares it with `Contract.Status`.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* Cleared on 2026-09-21, per
> the Director's review of the archived features: "Bring back the Agent
> member."
>
> *Added 2026-09-29:* two points of wording, ruled by the Director. A
> condition that returns a non-boolean: "Keep raising, fix the words"
> (Summary, items 3 and 7, Backwards compatibility). A gate that uses the
> tagging's inputs is read afterwards without them, with its defaults:
> "Keep it, write it down" (item 1).
