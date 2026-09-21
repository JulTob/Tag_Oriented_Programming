# STEP-SPEC-17: The Index

- **STEP:** SPEC-17
- **Desk:** spec
- **Title:** The Index: the Field as a mapping
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-09-21

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A Record marked `@Index` is a component of the Tag's key. The key is
**constant** on the Agent, **unique as a whole** across the Tag's Field,
and there is **one Index per Form, declared in one Tag**, its components
in declaration order. The key orders the Field. Read on the Tag, a
component is a **handle**: the values of that component, as a
dictionary's keys are, and the seat for that one component. `Signal.t[5]`
is the member at five, `Signal.t[a:b]` the half-open window in key order,
`Signal.t[:]` everyone in key order, `Event.t[1].seq[2]` one component
per bracket, and `5 in Signal.t` the question that never fails. The whole
key names one Agent; part of it names a population. A chain is the
intersection the Field algebra already defines, then the one member.

## Motivation

A Field is a set. Some Fields are also maps, and today TOP has no word
for that: a signal with a sample at each time, a ledger with a line at
each number, a register with a citizen at each identity. Each was a
Record and a comprehension by hand, with nothing to say that the key may
not change, that two members may not share it, or that the Field has an
order at all. The gap was found while scouting "indexed Tags" for
signals and ordered chains of events. The scouting went through and
rejected, in order: durable "Logs" (a Field never keeps an Agent alive);
symbolic filters in brackets (`Signal[0 <= index < 100]`, which Python
evaluates to `Signal[index < 100]` in silence, and `"x" in column`,
whose result the language forces to a boolean); a general `Where`
filter (a loop with an `if`, or a Tag, already does its job); unary
`+Tag` and `-Tag` for order (superseded by the handle, which names the
key); a tuple lookup `Signal.t[1, 2]` (positional, hides which value is
which component); a non-unique `@Key` (a composite Index with a counted
tiebreaker covers colliding timestamps, and every other order is the
language's own sort); and an ordering rule on the modifier (a value's
type carries its order, as it does for `sorted`, `min`, `max` and
dictionaries). What remained is small, and every piece of it is defined
by a law the Specification already has.

## Specification

1. **Declaration.** `@Index` marks a Record as a component of the Tag's
   key. It is stackable with `@Record` (which it implies) and refuses a
   stored seat, `@Secret`, a Report, a condition, and a Pin. A Tag may
   declare one or more components; their declaration order is the key's
   order.
2. **One Index per Form, declared in one Tag.** A Shape inherits the key
   and may not add a component; two Tags declaring components in one
   Form is a Declaration Failure, found when the class is made. The
   reason is Ring 0: membership is closed upward, so every member of the
   Shape is in the Base's Field, where the Base's key already decides
   uniqueness; a component that can never separate two members is a
   trap.
3. **Constant.** The value is built at step 2 like any Record and stored
   on the Agent, where writes and deletes are refused with the language's
   own attribute failure, as a published Report's name is (§1.5). It
   stays after Rip, sticky and still constant. Another key means Rip,
   then apply again.
4. **Unique as a whole.** The whole key (the tuple of components) is
   unique across the Tag's Field. It is checked when the key is built,
   at step 2: a key that is taken, not hashable, or not comparable with
   the keys already present is a Composition Failure, and the call rolls
   back. Constant plus unique at the door is unique always.
5. **A free name.** A component's name must be free on the Agent: not a
   host member, not a value the Agent holds, not another Tag's Record,
   Action or condition, or the tagging is a Composition Failure. The
   name stays taken: a later Record, Action or `@Delete` over it is
   refused the same way. The declaring Tag applying again after a Rip
   finds its own sticky value and takes the name back.
6. **The key comes and goes with membership.** Registered at commit,
   released at Rip, at rollback and when the Agent dies. After a Rip a
   later member may take the key; the Rogue keeps its value. Keys are
   coordinates: a Rip leaves a gap and nothing renumbers.
7. **The handle.** Read on the Tag, an Index component is a handle: one
   name in two scopes (§1.1), the value on the Agent and the map on the
   Tag. It is the set of that component's values among the members it
   sees: iterate, `len`, `in`, `min`, `max`. Its brackets are the seat
   for that one component:
   - `Tag.c[:]` everyone in Index order; `[::-1]` descending; any other
     step is refused;
   - `Tag.c[a:b]` the half-open value range, in Index order, either bound
     optional; a bound is a value of the component's type;
   - `Tag.c[v]` the members with `c == v`: one Agent when `c` completes
     the key by values, a population otherwise; a miss on the whole key
     is a Resolution Failure;
   - one component per bracket, chained by name; the chain means the
     intersection of the single-component views, then the one member;
     the same component twice, a name that is not a component, and a
     combined view's components are refused;
   - a handle walks everyone, as `Tag[:]` does; sound only is `if agent:`;
   - the Index has one order, declaration order; a handle constrains and
     never reorders;
   - nothing is assigned or deleted through a handle; membership comes
     from tagging and Rip is `del Tag[agent]`;
   - a population read through a handle is live and combines with `|`,
     `&` and `-` as any population.
8. **Shapes.** A Shape's handle is the Shape's Field through the Base's
   key.
9. **Types.** A value's type carries its order and its hash. A key that
   needs another order is a type that defines one.
10. **Deferred.** An Index on a Pin (ordering Tags by a key), a merge of
    two Indexed Fields by key, and any spelling beyond one component per
    bracket are not defined by this STEP.

## Rationale

Every law here is an old law applied. The value is a Record (§1.3). The
map is Tag scope, and one name in two scopes is allowed (§1.1). A
read-only name on the Agent is what a published Report already is (§1.5).
The check at step 2 rolls back like any Record failure (§0.6). Keys go
with membership because a Field never keeps an Agent alive (§0.3). A
chain is the intersection of §2.5, so the oracle's model of the algebra
covers it. One Index per Form falls out of upward closure (§0.3). The
handle's brackets carry only data, never code, so no expression can be
lost in evaluation; a comparison inside brackets is a syntax error in
Python and never a silent half-answer.

What the modifier buys over a Record and a Precondition is the law: the
gate is a convention that costs a scan, the law is the truth and costs one
dictionary read. With constant, unique keys the kit keeps a map from the
whole key and the keys in order, so a lookup is one read and a window a
bisection.

## Backwards compatibility

No spelling changes meaning. `@Index` is a new mark; `Tag.name` for a
Record not marked `@Index` is the builder function, as before. The plain
`Tag[0:2]` stays refused: positional slices have no meaning for a
population, and the keyed `Tag.c[0:2]` is a range of values. The failure
model gains no type; Declaration, Composition and Resolution Failures
cover the new cases and their rows say so.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Durable "Logs" | Set aside: a Field never keeps an Agent alive, and a history that forgets is not a log |
| A general `Where(Tag, predicate)` view | Rejected: a loop with an `if` does the one-off case, a Tag does the case worth naming |
| Symbolic filters in brackets, `Signal[0 <= index < 100]` | Rejected: Python evaluates the chained comparison to `index < 100` in silence, and `in` coerces to a boolean; the same proxy STEP-SPEC-16 keeps Redacted |
| Unary `+Tag` / `-Tag` for order | Superseded: the handle names the key and adds ranges and lookup with data in the seat |
| The tuple lookup `Tag.t[1, 2]` and `(1, 2) in Tag.t` | Rejected: positional, hides which value is which component |
| A non-unique `@Key` | Deferred: a composite Index with a counted tiebreaker covers colliding timestamps; other orders are the language's sort; the name reads backwards to a database audience |
| An ordering rule on the modifier | Rejected: a value's type carries its order, as for `sorted`, `min`, `max` and dictionaries |
| A Shape adding a component | Rejected: it could never separate members, by upward closure |
| Renumbering after a Rip | Rejected: keys are coordinates; a database never reuses a key |
| Positions on read | Kept as the language's: `enumerate(Tag.c[:])` |

## Acceptance requirements

Covered by `tests/test_topkit.py::IndexTests` (the laws of the mark:
constant, unique, one per Form, free names, rollback, Rip, death,
counted numeration) and `IndexHandleTests` (the handle: order, ranges,
lookups, chains as intersections, presence, refusals, Shapes, the
algebra, weak views, a key type of the program's own, and a random walk
of taggings, Rips and re-taggings checked against a dictionary and a
sorted list). Every block of `TopKit/INDEX.md` and the examples of §1.10
run under `tests/test_documents.py`.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
>
> *Drafted for the Director's confirmation:* the design was scouted and
> settled with the Director on 2026-09-21, one law at a time: "the laws
> make a lot of sense; they mostly behave as you would expect from
> vectors and dictionaries."
