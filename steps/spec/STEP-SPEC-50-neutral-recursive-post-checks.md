# STEP-SPEC-50: Neutral Recursive Post Checks

- **STEP:** SPEC-50
- **Desk:** spec
- **Title:** Neutral Recursive Post Checks
- **Author:** Codex, recording the Director's 2026-10-20 ruling
- **Status:** Brief
- **Created:** 2026-10-20
- **Issues:** [#291](https://github.com/JulTob/Tag_Oriented_Programming/issues/291), [#295](https://github.com/JulTob/Tag_Oriented_Programming/issues/295), [#33](https://github.com/JulTob/Tag_Oriented_Programming/issues/33)

> One STEP, one topic. This Brief defines what a Post check returns when
> judging validity reaches a Post already being judged. It does not change
> when Posts run, their lifetime, or whether they may change TOP state.

## Summary

When a Post's validity calculation reaches that **same active Post** again,
the recursive occurrence supplies the neutral truth value `True` without
running the check again. This holds whether the path came through
`bool(agent)`, sound or defective Field algebra, a named condition read, or
`Contract` diagnostics. Other visible Posts still contribute their own
verdicts. The Director chose this rule on 2026-10-20 and explicitly applied
it to every recursive validity cycle. It replaces the same-Agent Contract
Failure introduced with sound membership in [#216](https://github.com/JulTob/Tag_Oriented_Programming/pull/216).

## Motivation

A Post may depend on another Post, perhaps through an Action, a Link, or a
population query. That chain may eventually reach the first Post again.
Repeating the calculation can recurse without bound; refusing every cycle
prevents otherwise useful checks from asking about a larger contract. TOP
already gives an absent lower Post the neutral `True` when a Post Underlay
has no check beneath it. A revisited check has the same neutral role in a
validity calculation: it adds no new failure and does not certify any other
promise.

The current runtime has three different answers to this situation. A
recursive `bool(agent)` takes a broad `True` shortcut, a recursive sound
population query raises Contract Failure, and a named Post or
`Contract.Status(agent)` may repeatedly run the check. One neutral rule
should replace those inconsistent paths and cut recursive edges in queries such
as a Post that asks `len(Group)` while each Group member asks the same
question.

## Proposed specification

1. **Recursive edge.** A check is identified by its Agent or Tag receiver
   and the particular Post calculation being run, not merely by its name.
   If a validity query reaches that check while it is already active in
   the same evaluation, that occurrence answers `True` immediately. The
   check itself continues toward its own final verdict. A same-name lower
   Post invoked by `@Underlay` is a different check and runs normally
   unless its own calculation is revisited.
2. **Other promises still count.** The neutral answer replaces only the
   recursive occurrence. `bool(agent)`, `Contract.Postconditions(agent)`,
   `Contract.Conditions(agent)`, sound membership (`agent in MyTag`), and
   the sound/defective populations must still judge the other visible
   Posts. Thus an unrelated failing Post keeps the Agent defective even
   while another Post is in a cycle. `agent in MyTag[:]` remains a raw
   Field-admission question and does not evaluate Posts.
3. **Named and diagnostic reads.** `agent.Ready` returns neutral `True`
   when it reaches its own active `Ready` check, whether directly or through
   other checks. `Contract.Status(agent)` and `Contract.Display(agent)`
   show the provisional neutral result for an active Post and calculate
   the other entries normally. A query of a different Agent proceeds
   normally until it too encounters an active check. This rule also
   applies to a future Tag-owned Post when its Tag is the checked receiver.
4. **Bounded recursion and one-query reuse.** TOP must stop recursion at
   the active check. Within one outer validity query, the first completed
   verdict for the same receiver and exact Post becomes that query's answer
   wherever the Post is reached again. It is reused even when another path
   reaches it beneath a different active Post. A contradictory cycle can
   therefore depend on which check the query reaches first; that is the
   declared operational answer, not an attempt to solve a fixed point. A
   sensor may change while the query runs; a separate validity query starts
   fresh and sees the later value.

   Reuse never crosses a permission boundary that can change what the
   calculation may see. Opening or closing a Secret door invalidates the
   query's reusable verdicts; if the query later reaches that Post again, it
   calculates a fresh verdict under the current door. An interruption or
   raised check failure retains its existing diagnostic and cause rather than
   becoming neutral. The broader rule for checking a published Service both
   before protected work and before releasing its result is recorded
   separately in [issue #389](https://github.com/JulTob/Tag_Oriented_Programming/issues/389);
   it is not implemented by this Post memo.
   This does not grant permission for Posts to mutate TOP state; the
   observational-Post rule is proposed separately in
   [#346](https://github.com/JulTob/Tag_Oriented_Programming/pull/346)
   (STEP-SPEC-49).
5. **Operational truth.** Neutral `True` is a rule for an encountered
   recursive edge, not a global fixed-point solver. A direct paradox such
   as `Ready = not bool(agent)` sees its own neutral `True` and therefore
   returns `False`. Mutually negating checks can depend on which query is
   entered first; authors should express a stable contract without such
   contradictory cycles. TOP does not silently turn a completed `False`
   into `True` after the check returns.

For example, `Ready` cannot hide a separate broken `Brakes` Post:

```python
class Car(Tag):
    @Post
    def Ready(agent):
        return bool(agent)  # Ready contributes neutral True on this edge

    @Post
    def Brakes(agent):
        return agent.brakes_work

# With brakes_work False, the nested bool and the final Car verdict are False.
```

## Rationale

The unit of recursion is one Post calculation. Returning `True` for the
entire Agent as soon as any of its Posts is active would skip independent
promises. Re-entering the same calculation instead contributes the neutral
element while the rest of the contract can still fail. Tracking check
identity also respects layered same-name Posts: an upper Post may ask its
lower check without being mistaken for a self-reference.

Cutting a recursive edge guarantees termination for a finite, stable set
of checks, but it need not make a dense collective predicate cheap. An
eight-member Field whose Posts each ask for the Field's sound size can
execute a Post over 100,000 times in one query. The Director chose the first
completed verdict as the answer for that exact Post throughout one query,
including the deliberately pathological case in which a different path
would meet a different recursive edge. This keeps finite collective checks
tractable without pretending to solve a contradictory contract.

Permission is a separate dimension. A Secret door can change what a check
is allowed to observe, so a reusable verdict cannot cross the door's opening
or closing. This STEP conservatively invalidates that query's Post memo; it
does not claim an Agent-state epoch can prove arbitrary Python inputs stable.
STEP-SPEC-49 blocks explicit TOP mutations inside a Post, but it does not
make arbitrary reads pure or authorize reuse between separate queries.
Service entry/release authorization belongs to issue #389.

## Backwards compatibility

This reverses the Contract Failure sentence in deployed
[STEP-SPEC-4](STEP-SPEC-4-defective-taggings.md)'s 2026-10-15 amendment and
the corresponding current Specification §2.5 paragraph introduced by
#216. Those texts remain on record until this STEP is Cleared and the
current law is amended. Existing callers that catch that failure to choose
a fallback will instead receive a boolean verdict. Existing programs that
rely on a broad recursive `bool(agent)` shortcut may now see a separate
failing Post during the same query. The `Contract.Status`/named Post loops
become bounded results.

Open [#277](https://github.com/JulTob/Tag_Oriented_Programming/pull/277)
currently tests rejection of a collective cycle; it must be revised to
test bounded neutral evaluation. Draft [#294](https://github.com/JulTob/Tag_Oriented_Programming/pull/294)
and [#309](https://github.com/JulTob/Tag_Oriented_Programming/pull/309)
also implement rejection and must not merge as written. The separate
observational Post work in #348 mechanically blocks explicit TOP acts
inside a check, but does not make all Post inputs stable. Direct Python
writes remain the author's responsibility.

## Alternatives considered

| Alternative | Reason not chosen for this Brief |
| --- | --- |
| Raise Contract Failure on every recursive Post validity query | The Director replaced the earlier #216 choice with neutral `True` for every recursive cycle. |
| Return `True` for the whole Agent whenever one Post is active | This can hide an independent broken Post in the nested answer. |
| Re-run the active check until it returns or Python stops it | It may never terminate and lets diagnostics repeat arbitrary check code. |
| Re-run every completed Post within one query | Dense collective cycles terminate but repeat the same work an exponential number of times; the Director chose a stable verdict for one query. |
| Cache by Post name or across separate queries | Same-name layers are distinct checks, and later queries must see current values. |
| Reuse a verdict after Secret/access state changes | The read may have been allowed only inside the earlier door; invalidate and check again. |

Pure Precondition cycles and mixed Pre/Post cycles require a separate
decision. This STEP defines Post validity recursion and does not change a
Precondition's Gate result.

## Acceptance requirements

- Direct and indirect self-checks terminate through named reads, Agent truth,
  sound membership and Contract diagnostics; a direct negation of its own
  neutral answer is False.
- An unrelated failing Post still makes the whole Agent false during a
  recursive query, while raw Field membership remains readable.
- Layered same-name Posts distinguish their exact calculations. Repeated
  reads of the same exact Post in one validity query reuse its first completed
  verdict even when reached through a different active-Post path. A separate
  outer query sees changed Records or outside inputs.
- Opening or closing a Secret door invalidates completed verdicts in that
  query. A later path recomputes rather than leaking an inside-door answer.
- A finite collective Field query terminates, and each repeated exact Post
  is evaluated at most once while reuse remains safe. A separate performance
  test must measure dense collective checks before this rule is deployed.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
