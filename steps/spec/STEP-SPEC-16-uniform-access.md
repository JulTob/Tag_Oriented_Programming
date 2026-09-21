# STEP-SPEC-16: Uniform Access

- **STEP:** SPEC-16
- **Desk:** spec
- **Title:** Uniform Access
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-09-21

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

Uniform access is the rule that one name may be read as a value and
called as a function with the same meaning: `agent.hp` and `agent.hp()`
read the same Record; a nullary Action may be read without `()`. The
0.2-alpha line had it; the 2026-09-04 review Redacted it ("explicit
before magical"; the proxy leaks into host code), and STEP-SPEC-4
records that. The Director asked on 2026-09-21 for this STEP as an
independent record with the full case, to review later: "why not using
dunder methods for the call to retrieve the value?"

This STEP opens at Brief with a recommendation to keep it Redacted.

## What it would give

- A Record and a nullary Action read the same way: the caller need not
  know which one a name is, so a Tag may change a stored value into a
  computed one without touching its callers. This is the classic
  argument for uniform access.
- One less thing to remember at the call site.

## Why the language resists it

For `agent.hp` to be both a value and a call, the object behind the name
must carry the value's behaviour and a `__call__`. There are two ways to
make such an object in Python, and both are a **proxy**: a thing that
acts like the value but is not the value.

**Wrap the value.** A class that forwards `__add__`, `__eq__`, `__str__`,
`__iter__` and the rest to the wrapped value and adds `__call__`. This is
what the archived kit did. It looks like `42` until someone asks
`type()`, `isinstance()`, `json.dumps()`, `pickle`, `is`, or hands it to
code written in C that expects a real `int`. Every such place is a leak,
and the review found them.

**Subclass the value's type.** Make the object a real `int` with a
`__call__`, by building a subclass of the value's type on the fly. Closer,
but:

- `bool` and `NoneType` cannot be subclassed, so `agent.alive` and any
  empty Record can never be callable; the rule would have holes exactly
  where it is least expected;
- `type(agent.hp) is int` is False, and `type(agent.hp) is
  type(agent.other_hp)` is False for two dynamic subclasses;
- pickling and copying a value of a class made at run time fails or
  produces the wrong class;
- every read allocates a new object, which shows in the read path that
  today costs about fifty nanoseconds.

**The other direction is worse.** Making a nullary Action readable
without parentheses means naming the Action runs it: passing
`agent.Attack` as a callback fires the attack; `if agent.Attack:` fires
it; a debugger listing the Agent's members fires everything.

## What is lost by not having it

A Tag that changes a Record into an Action of the same name changes its
callers from `agent.hp` to `agent.hp()`. In TOP this is rare and visible:
the two are different kinds, an Overlay may replace one with the other
only within a Form (independent Tags may not, §1.2), and the change is
the author's to make at the call sites the Tag owns.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Proxy wrapper (archived) | Rejected by the review: leaks into host code |
| Dynamic subclass per value type | Rejected here: `bool` and `None` cannot; identity, pickling and cost |
| Read a nullary Action without `()` | Rejected here: naming runs it |
| A property-like Record that computes on read | This exists: a Record builder runs at tagging, and an Action computes on call; a third kind would blur both |
| Keep it Redacted | **Recommended**: "a Record is a value, an Action is a call" is the rule a beginner can hold in one hand |

## Acceptance requirements

None while Redacted. If the Director reopens it, the STEP must name the
proxy strategy and list every leak it accepts.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's review:* Redacted, on the case above; the
> STEP stands as the record of why.
