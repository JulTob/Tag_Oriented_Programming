# STEP-SPEC-20: Conditions Across Independent Tags

- **STEP:** SPEC-20
- **Desk:** spec
- **Title:** Conditions Across Independent Tags
- **Author:** Julio Toboso (@JulTob)
- **Status:** Brief
- **Created:** 2026-10-08

> One STEP, one topic. If this grows a second purpose, split it into another
> STEP.

## Summary

A condition laid over an **independent** Tag's condition of the same name
and kind follows the slot law that already governs Actions and Records
(§1.1–§1.3). The latest Layer is visible. Without `@Underlay` it
**replaces** the other Tag's gate or promise, which then no longer binds
the Agent; TOP allows it and diagnoses it with an **Overwrite Warning**.
With `@Underlay` it **extends** it, silently: the author writes the merge.
The Contract Warning keeps its meaning along the Geometry, where
"weakened" has one: a Shape's promise against its Base's.

## Motivation

Two Tags that know nothing of each other each promise `Honest`:

```python
class Sworn(Tag):
    @Post
    def Honest(agent):
        return agent.oath

class Guild(Tag):
    @Post
    def Honest(agent):
        return True

Sworn(ari)
Guild(ari)    # TagContractWarning: Guild.Honest overrides a Base Postcondition ...
```

Guild is not a Shape of Sworn, so "a Base Postcondition" was false (the
kit's text is fixed with this STEP; see below). The text was wrong
because the Specification has no law for this case:

| Where | What it covers | Independent conditions? |
| --- | --- | --- |
| §1.1 | one slot per `(scope, name)`; independent Tags refused across kinds | Actions and Records only |
| §1.2, §1.3 | an independent Tag replacing an Action or Record: allowed, diagnosed (Overwrite Warning) | not conditions |
| §2.2 | a Shape relaxes its Base's Precondition: silent | Geometry only |
| §2.4 | a Shape weakens its Base's Postcondition: Contract Warning | Geometry only |
| §2.5 (STEP-SPEC-14) | a condition's name is an Agent name, refused to Actions and Records | across kinds only |
| §2.6 rule 3 | two Tags that each declare `Ready` share `Precondition.Ready` | the failure class, not the slot |
| Failure model | Contract Warning: "A Shape weakened a Base Postcondition" | — |

STEP-SPEC-11 (Redacted) met the case once, in its open question, where
`Elf` laid an `@Underlay` promise over an independent `Alive`'s. It
decided what Rip should do about it, not what the laying itself is.

Issue [#10](https://github.com/JulTob/Tag_Oriented_Programming/issues/10)
reported the same wrong text from another side: a Shape `class C(A, B)`
whose two unrelated Bases both promise `Fine` warns on every application
of `C` and calls B's promise a weakened Base Postcondition. Its option D,
"route unrelated same-name Postconditions to the Overwrite Warning", is
this STEP's proposal; its other options are about the Form (see *Out of
scope*).

### What actually happens today

The kit keeps one condition per name and kind, latest Layer visible, as
for an Action. So the other Tag's promise is gone **at tagging**, not
at Rip:

```python
ari.oath = False
Sworn(ari)                 # TagPostconditionError: ari is defective
Guild(ari)                 # warns; Guild.Honest replaces Sworn.Honest
bool(ari)                  # True: repaired by erasure, not by an oath
```

Rip changes nothing afterwards, because conditions are sticky
(STEP-SPEC-12): after `del Guild[ari]` the surviving `Honest` is still
Guild's. If Guild's `@Rip` protocol ends it with `Contract.Delete(ari,
"Honest")`, Ari is left a member of Sworn with no `Honest` at all.

Preconditions behave the same way and say **nothing**: an independent
Tag's `@Pre def Ready` silently replaces another's, and from then on
`Contract.Preconditions(agent)` and `agent.Ready` read the newcomer's
gate.

## Specification

1. **One law for every Agent name.** A condition is laid like any
   contribution: the latest Layer is visible under its name, one
   Precondition and one Postcondition per name.
2. **Across independent Tags** (neither in the other's Form, §1.1)
   applied by separate taggings, a Precondition laid over a
   Precondition, or a Postcondition over a Postcondition, of the same
   name (two Bases inside one Form: see *Out of scope*):
   - **without `@Underlay`** replaces it. The other Tag's gate or promise
     no longer binds the Agent. TOP allows it and diagnoses it with an
     **Overwrite Warning** that names the Tag whose condition no longer
     binds, exactly as for an Action (§1.2) or a Record (§1.3);
   - **with `@Underlay`** extends it, silently. Both bind.
3. **Along the Geometry nothing changes.** A Shape relaxing its Base's
   Precondition is silent (§2.2). A Shape replacing its Base's
   Postcondition without `@Underlay` is a **Contract Warning** (§2.4);
   so is a Base re-applied over its own Shape's sticky promise (a
   promise that was at least the Base's, replaced by the Base's alone).
   The warning's text names the Base or the Shape.
4. **A Tag re-applied over its own condition** (after its own Rip) is
   silent, as before (§0.7, STEP-SPEC-12 rule 6).
5. **Failure model.** The two rows read:

   | Failure | Meaning | Effect |
   | --- | --- | --- |
   | **Overwrite Warning** | An independent Tag replaced a visible Action, Record or condition without an Underlay. | diagnostic |
   | **Contract Warning** | Within one Form, a Postcondition was replaced without its Underlay: a Shape weakening its Base's promise, or a Base laid over its Shape's. | diagnostic |

6. **§2.4 gains one paragraph**, proposed text:

   > **Across independent Tags** (STEP-SPEC-20), a promise is laid like
   > an Action: the latest Layer is visible under its name. A Tag that
   > lays a promise over an independent Tag's without `@Underlay`
   > replaces it, and that promise no longer binds the Agent. TOP allows
   > it and raises an Overwrite Warning. To keep both, take the Underlay;
   > to keep them apart, name them apart. The same holds for a gate.

   with the example:

   ```python
   class Guild(Tag):
       @Post
       @Underlay
       def Honest(agent, base):
           if agent not in Guild:
               return base()                          # Guild's part ends with Guild
           return base() and agent.ledger_balanced    # while a member, both bind
   ```

   and §1.1's slot sentence names conditions beside Actions and Records.

### Ending one part of a shared name

When one name carries two Tags' promises, `Contract.Delete` from one
Tag's `@Rip` ends the **whole** name, the other Tag's part included
(checked against the kit: Ari stays in Sworn with no `Honest` left). The
guard in the example above is the way to end only your own part. This is
STEP-SPEC-12's guarded Underlay, applied; no new law.

## Rationale

**It is not a new law; it is the existing one, applied to a third kind.**
STEP-SPEC-14 made a condition's name an Agent name. §1.1 already says
what an Agent name is: one slot, latest Layer, refused across kinds
between independent Tags, replaced-and-diagnosed within a kind. The
diagnostic is chosen by **how the two Tags relate**, never by what kind
of contribution met. That is an algebra, not a special case.

**"Weakened" only means something along a Form.** The contract direction
(§2.2, §2.4) is the substitution rule: a Shape must stand in wherever its
Base is expected, so it may ask less and must promise more. Two
independent Tags have no such relation. `Guild.Honest` is neither
stronger nor weaker than `Sworn.Honest`; it is a different promise that
happens to share a name. Calling it "weakened" sends the reader looking
for a Base that is not there, which is how this STEP was found.

**The author writes the merge.** §1.3 already decided this for Records:
independent builders pile up only when the author takes the stored
value. The kernel never merges by itself. `@Underlay` is the same seat
for conditions, and it already works across independent Tags (the
example runs today, silently).

**It closes the silent Precondition case** with no extra rule.

## Backwards compatibility

- The slot behaviour does not change. Only diagnostics do.
- An independent Postcondition replacement raises `TagOverwriteWarning`
  instead of `TagContractWarning`. A program that turns
  `TagContractWarning` into an error stops catching this case; one that
  turns `TagOverwriteWarning` into an error starts.
- An independent Precondition replacement, silent today, raises
  `TagOverwriteWarning`.
- A program that wants both conditions adds `@Underlay` (as above) or
  renames one.

## Alternatives considered

| Alternative | Verdict |
| --- | --- |
| **Refuse it** without `@Underlay`: a Composition Failure, atomic, like a cross-kind collision (§1.1) | **The live alternative.** It is the safest reading of Commitment 6 ("a failed promise is never silent") and of STEP-SPEC-12 ("the loud failure is the safe one"); it would make the repair-by-erasure above impossible. Set aside because it turns a naming accident between two Tags that never met into a hard stop that a program using both cannot fix (it owns neither Tag), and because §2.6 rule 3 already expects two Tags to declare `Ready`. If the Director weighs safety above composition here, this is the choice, and the kit change is as small. |
| **Both stand**: conditions kept per Tag, `agent.Honest` the conjunction | Set aside: the kernel would write the merge (against §1.3), `Contract.Delete` and `Contract.Display` would need a Tag to say whose part, and an `@Underlay` over two lineages reopens STEP-SPEC-11's chain question. |
| **Contract Warning, text fixed** (the kit after this STEP's fix, until a decision) | Keeps the class, but the class claims a weakening that only exists along a Form, and leaves Preconditions silent. |
| One warning class that is both an Overwrite and a Contract Warning | Set aside: the failure model keeps its types distinct; a warning that means two things means neither. |
| Silent, as a Shape's Precondition is | Rejected: the promise disappears with no trace. |

## Out of scope

- **What "independent" means inside one Form.** In `class C(A, B)`, A
  and B are independent pairwise (neither is in the other's Form), yet
  C's author declared, once, that B lays over A. Whether that is silent,
  diagnosed once at the `class` line, or diagnosed at every application
  of C is issue #10's question (its options A to C), and it holds for
  Actions and Records as much as for conditions. This STEP's law is for
  Tags applied separately; inside one Form it follows whatever #10
  decides.
- A Precondition of one Tag and a Postcondition of another under one
  name. They are two kinds and do not replace each other; `agent.Name`
  reads the Postcondition first (§2.5). Unchanged.
- The number. STEP-SPEC-19 is claimed twice already, by
  [#26](https://github.com/JulTob/Tag_Oriented_Programming/pull/26)
  (Links) and by the branch `Julio_Cl/step-19-sound-in` (`in` answers
  for sound members); this STEP takes 20 to stay clear of both.

## The kit until a decision

Shipped with this STEP, without changing any law: the Contract Warning's
text names the real relationship ("replaces the Postcondition of
independent Tag Sworn without @Underlay; Sworn's promise no longer binds
this Agent"; "its Shape Knight"; "its Base Soldier"), and it points at the
tagging line instead of the frame above it. The warning class is
unchanged. `IMPLEMENTATION_NOTES.md` records the judgment call. This
corrects the wording #10 reports; #10's repetition at every application
of a Shape, and the class it should carry, stay open there.

## Acceptance requirements

When Cleared:

- `TopKit/overlay.py` raises `TagOverwriteWarning` for an independent
  Precondition or Postcondition laid without `@Underlay`, naming the Tag
  whose condition no longer binds, and keeps `TagContractWarning` within
  one Form;
- `tests/test_topkit.py`: the independent case for Pre and for Post; the
  `@Underlay` composition silent, with both promises binding; the guarded
  Underlay ending only its own part at Rip; the Geometry cases unchanged;
- the Specification: §1.1, §2.4 and the failure model as in §5–§6 above;
  `CONFORMANCE.md` Ring 1 names conditions in the slot law.

---

### Decision *(filled by the Director)*

> Status set to **____** on YYYY-MM-DD, because ____.
