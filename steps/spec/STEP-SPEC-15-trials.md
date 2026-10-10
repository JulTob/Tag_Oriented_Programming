# STEP-SPEC-15: Trials (Recoverable Phases)

- **STEP:** SPEC-15
- **Desk:** spec
- **Title:** Trials (Recoverable Phases)
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-09-21

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A **Trial** is a proposed phase during which every tagging on one Agent is
provisional. Leave it well and everything done in it stays; leave it on
an error and the Agent is put back exactly as it was when the Trial
began: same identity, same Tags, same values. The original proposal treated
a Trial as a one-call rollback boundary stretched over many calls. Current
TOP does not promise whole-Form atomicity: completed Tags remain when a
later Tag fails, so a future Trial design must define its own boundary.

```python
with Try(ari):                  # historical candidate; not reserved TOP syntax
    Species(ari)
    Background(ari)
    Feat(ari)                   # refused? the whole draft is undone
                                # clean exit: the whole draft is kept
```

The 0.2-alpha line had this as `Tag.Checkpoint(agent)` with `Commit()`
and `Restore()`; that record is on the branch `archive/pr-1-recoverable-checkpoints`.
This STEP asks for it back with the vocabulary, the bloat and one law
reconsidered.

## Motivation

The Director, reviewing the archived feature on 2026-09-21: "It is really
useful and can save a program from unwanted states. It is highly secure
and safe to have the feature but the bloat and vocabulary must be
optimized and understandable." And on the mechanism: "I would consider
this if we can use codewords like 'try' or 'with' to start the
'hypothetical' code with restoration."

Use cases: a character generator that builds a sheet in steps and throws
the whole draft away if a late step is refused; a mod loader that applies
a bundle of Tags and backs out if any one is refused; try-then-approve in
tools, where a candidate is built, inspected, and kept or dropped.

## The considerations, expanded

**Vocabulary.** `Tag.Checkpoint(agent)` mixed a Tag-level act into the
dotted namespace §0.8 leaves to the program, and "checkpoint", "commit",
"restore" are a database's words. This STEP originally proposed the
language's own block, `with Try(agent):`, for a Trial's two endings. That
spelling is now only a historical candidate: STEP-SPEC-31 leaves `with`
free, and no recoverable-phase spelling has been selected. Candidates and
their cost:

| Spelling | For | Against |
| --- | --- | --- |
| `with Try(agent):` | one word, the language's own idea of an attempt; reads at the call site | shadows nothing, but sits next to the keyword `try` in the reader's eye |
| `with Trial(agent):` | a noun, the TOP word for the phase; the Agent "is on trial" | one letter longer; less obviously an attempt |
| `with Draft(agent):` | says what the Agent is during the block | a draft is a thing, not a phase |
| `Tag.Checkpoint(agent)` | the archived spelling | mixes Reports and kernel acts on the Tag; three words for one act |

The Director's earlier word was "try". No noun, block protocol or handle
form is accepted by this Brief. A future design must first establish that
a recoverable phase fits `with` naturally and preserves ordinary Python
contexts. The original handle candidate was `trial = Try(agent)`, followed
by `trial.Keep()` or `trial.Undo()`; it is likewise unselected.

**Fully real while the Trial is on.** The archived version made a
provisional Tag invisible even to the Agent (`ari not in Species` until
commit). The Director: "I'm inclined towards fully real while the try is
on. You could see it like an agent in training period." So: inside the
block, membership, Fields, Records, Actions and conditions are exactly
what they would be outside it. Nothing is hidden from anyone. The Trial
changes one thing only: what happens on a bad exit. This keeps the
Agency pattern intact (an Agent works through the Tags it carries) and
removes the second visibility rule the review objected to.

**Bloat.** The archived implementation was the largest piece of the old
kernel: snapshots of the instance namespace, of slots, of every mutable
container reachable from the Agent, of the runtime type, of Field
memberships, with a query object registered in a context variable. Most
of it tried to extend the old call boundary. The proposed implementation
was a snapshot (namespace copy, state copy, active Tags, class) held for
the length of a block, plus a Rip of every Tag joined during the block.
That mechanism is historical too: a future design must start from TOP's
current per-Tag Gate and failure rules rather than inherit it implicitly.

**Host values.** The hard question. A Record or an Imprint may append to
a list the Agent already held, or to a list another object shares. The
archived kit snapshotted every mutable reachable from the Agent and
restored it in place on rollback. That is thorough, expensive, and can
surprise: a value shared with another object is restored too. Options:

| Rule | Gain | Cost |
| --- | --- | --- |
| Restore TOP state and the Agent's own attribute bindings only (what one call rolls back today) | cheap, predictable, one rule for calls and Trials | an Imprint that appended to an existing list leaves the append; the author undoes it in `@Rip` |
| Also restore the contents of lists, dicts and sets the Agent's attributes point to, one level deep | catches the common append | more copying; a container shared with another object is rewound under it |
| Deep, as archived | nothing escapes | the most copying; the most surprising |

The first rule matched the kernel behavior assumed when this Brief was
written. It is not accepted merely by appearing here. A future Trial that
wants deeper undo could ask its Tags to write `@Rip` teardowns, under the
ordinary teardown law (STEP-SPEC-12), but must settle how that interacts
with the current failure protocol.

**What a Trial must refuse.** A Trial on a Target that is inside another
Trial is nested: the inner ending happens first; an inner undo does not
end the outer. A Trial cannot end while a tagging on its Target is in
progress (an Imprint that opens or closes one). Ripping a Tag inside a
Trial that was active before it began is allowed and is undone by the
Trial's undo (the Tag comes back, its Records with it, as sticky
contributions that were never lost).

**Pins.** A Trial on a Tag as Target (a pinning phase) follows the same
rule with the class namespace as the snapshot, as the archived version
did.

## Historical proposal (not accepted)

The rules below preserve the proposal for later review. They do not reserve
`with`, `Try`, `Trial`, or a handle API in TOP.

1. `with Try(agent):` opens a Trial on one Target. On a clean exit the
   Trial ends and nothing else happens. On an exception the Target is
   restored to its entry state and the exception propagates.
2. Entry state: the Target's TOP state, its active Tags and Field
   memberships, its attribute bindings, and its runtime type. Restored
   as one act, in the reverse of the order things were done, with each
   Tag joined inside the Trial Ripped through its own `@Rip` protocol
   first, so authors' teardowns run.
3. Inside the Trial everything is real: no view, Field, member or
   condition tells the block from the world outside it.
4. `trial = Try(agent)` without `with` returns the handle; `trial.Keep()`
   ends it; `trial.Undo()` restores. A handle collected without either
   undoes. A handle ends once; a second ending is a Composition Failure.
5. Nested Trials on one Target end innermost first. Ending a Trial while
   its Target is being tagged is a Composition Failure.
6. Host containers are not rewound (rule one above) unless the Director
   chooses otherwise below.

## Open questions for the Director

1. Whether recoverable phases are a natural use of an explicit `with`
   protocol at all. Any accepted form must coexist with host and Agent
   context protocols under STEP-SPEC-31.
2. The noun: `Try`, `Trial`, `Draft`, or another word.
3. Host containers: rule one (bindings only), one level deep, or deep.
4. Whether the handle form is wanted at all in the first version, or the
   block form alone.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| The archived `Tag.Checkpoint` with hidden membership | Rejected by the Director: vocabulary and bloat; and the review's Agency objection |
| `Scope` with an undo flag | Retired by STEP-SPEC-31; no future phase inherits its policy |
| Leave it out | Rejected by the Director: "highly secure and safe to have the feature" |

## Acceptance requirements

To be written with the implementation: the four archived checkpoint
tests (commit publishes an ordered sequence; restore recovers identity,
state and history; the context form restores on error and keeps on exit;
each inner tagging keeps its own transaction) rewritten in the new
vocabulary, plus nested Trials, Rip inside a Trial, a Trial on a Tag, and
the oracle extended with a Trial transition.

---

### Decision *(filled by the Director)*

> This STEP remains **Brief**. On 2026-10-09 the Director retired `Scope`
> and asked TOP to leave `with` free unless a use arises naturally. That
> decision removes the old assumption that `with Try(...)` is the primary
> spelling; it does not reject the recoverable-phase need recorded here.
