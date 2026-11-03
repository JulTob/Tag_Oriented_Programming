------------------------------ MODULE FormClosure ------------------------------
(***************************************************************************
PROMISE: Every Tag's Form holds its Bases deepest-first in declaration
  order, each Base exactly once, then the Tag
  (spec/SPECIFICATION.md:141-143; conformance 1808-1812: "Base-first Form
  application, each Base once, active reapply a no-op").
  The spec's words (SPECIFICATION.md:156): "A Base reachable through
  several paths appears once." Example (SPECIFICATION.md:145-152):
  "class Arcane_Duelist(Spellcaster, Duelist)" has
  "Form(Arcane_Duelist) == (Spellcaster, Duelist, Arcane_Duelist)".
 HARM: A missing or duplicated Base silently drops or doubles that Base's
   Gates, Records, Imprints, Posts and membership with no error or warning.

COVERS:
  - TopKit/geometry.py:_form_of lines 179-243 (iterative closure, seen-set,
    pending stack, memo read/write-through)
  - TopKit/geometry.py:_direct_bases lines 167-176 (declaration-order bases)
  - TopKit/queries.py:Form lines 15-20 (thin wrapper over _form_of)
  - Same `in`-on-classes hazard, NOT separately modelled (noted in
    FINDING F1): geometry.py:_leaves lines 252-265, queries.py:Outline
    lines 80, 86, transactions.py line 124.
CONFIRMED AGAINST COMMIT 1bd5a2548a6bc8fadab9ca4c2451428dbf9b93e4

 ASSUMPTIONS and what is NOT modelled:
   - One indivisible step is one loop iteration of _form_of (pop one
     pending entry and push/emit at most one batch): no user code runs
     between those statements, so no thread switch or interrupt can
     interleave there. DAG construction (BuildEdge) is the test driver,
     not code: any interleaving of declarations reaches the same DAG.
   - Single thread; N nodes stand for N Tags declared in numeric order,
     so every Base has a smaller number than its Shapes (every DAG has a
     topological order; ordered Bases add every declaration permutation).
  - Eq models a Tag metaclass overriding __eq__/__hash__: groups[a]=
    groups[b] means the metaclass calls them equal (e.g. constant hash
    17 with isinstance equality). All Eq classes are assumed hashable;
    an unhashable metaclass (__hash__ = None) raises TypeError in the
    real set() and is NOT modelled (see real/repro_FC4.py notes).
  - EqMode selects the metaclass-equality scenario: "all" ranges over
    every Eq partition (adversarial metaclasses included); "identity"
    fixes one class per Tag (ordinary metaclasses: distinct Tags are
    never equal); "equal" merges every Tag into one Eq class (the F1
    scenario: an always-equal metaclass).
  - NOT modelled: memo cache ownership/lifetimes (a same-answer
    property; lifetimes belong to the memo_lifetimes area),
    unrelated-class churn, __bases__ mutation staleness (spec-silent
    design question #97), the tagging-application loop
    (transactions._apply walks the Form; Imprint order and the reapply
    no-op are properties of that walk, not of the closure), Pins/Flags/
    mixins (mixins contribute no Bases; Pin Forms use the same _form_of
    code path).
  - Default bound N=4 (160 ordered DAGs x targets x Eq partitions per
    the cfg's EqMode); N=5 (10,400 DAGs) was explored on the real code
    during the survey (0 failures under identity semantics) but ships
    as no script: harnesses are not a deliverable.

 INVARIANTS (each with its plain meaning):
   - FC1_ClosureExact: the finished Form holds exactly the Tag-reachable
     closure, nothing missing, nothing extra.
   - FC2_EachBaseOnce: no Tag appears twice in the finished Form.
   - FC3_BaseFirst: every Base sits before every Shape built on it.
   - FC4_DeclarationOrder: the finished Form equals the independent
     recursive declaration-order oracle (the code+tests+GUIDE reading of
     "deepest first, in declaration order": strict depth-sorting differs
     on 646/10,400 DAGs at N=5, e.g. D(B,C),C(A) -> (B,A,C,D); the
     declaration-order DFS reading is adopted).

FINDING F1 (brief FC-4; violated invariant FC1_ClosureExact):
  Counterexample in code words: declare metaclass Equal_Meta(MetaTag)
  with __eq__ always-true and __hash__ constant; declare Prize(Tag)
  then Sub(Prize); Form(Sub) is (Sub,) instead of (Prize, Sub): the
  `base not in seen` push-time test (geometry.py:226) calls the metaclass
  __eq__, sees Prize as already present, and never pushes it. No
  exception, no warning; Tagging Sub never applies Prize (Imprint/Post/
  membership silently lost). Classification: (a) violates a spec promise
  only if class identity is read as independent of custom equality --
  the spec says 'Fields are indexed by identity: two equal but distinct
  Agents are two members' (SPECIFICATION.md:135-137) for Agents/Hosts
  and IMPLEMENTATION_NOTES states identity-based entries for Hosts with
  custom equality; for Tags the spec is (b) silent/ambiguous, so F1 is
  reported as spec-silent with real harm. Real-code replay:
  repro_FC4.py. TLA+ witness: EqMode="equal", N=2, bases[2]=<<1>>,
  target=2 gives form=<<2>>.

  Latent instances of the same hazard, not separately modelled: the
  `candidate in seen` pop-time test (geometry.py:214), the `seen.add`
  set itself (geometry.py:199,217: equal classes collapse to one set
  slot), geometry.py:_leaves lines 252-265, queries.py:Outline lines
  80 and 86, transactions.py line 124.

BREAK switch (one per invariant, each must violate its cfg invariant):
  - "none": current code, Eq-based seen tests (finds F1 under
    EqMode="equal").
  - "fixed": identity-based seen tests (the obvious fix; must pass
    under every EqMode).
  - "skip_diamond": push only the first direct Base (misses Bases).
  - "no_dedupe": drop the pop-time `candidate in seen` skip (duplicates).
  - "base_after_shape": append the Shape before its Bases (preorder).
  - "reverse_order": push Bases in declaration order, not reversed
    (visits them last-first).
 ***************************************************************************)

EXTENDS Integers, Sequences, TLC

CONSTANTS N, Break, EqMode

ASSUME N \in 1..6
ASSUME EqMode \in {"all", "identity", "equal"}

Nodes == 1..N

VARIABLES bases, target, groups, phase, form, seen, pending

vars == <<bases, target, groups, phase, form, seen, pending>>

(***************************************************************************
 \* code: TopKit/geometry.py:_direct_bases lines 167-176
 \* mirrors the declaration-order direct Bases of one Tag.
 ***************************************************************************)
RangeSeq(s) == {s[i] : i \in 1..Len(s)}

(***************************************************************************
 Identity vs metaclass equality for the seen-set tests.
 \* code: TopKit/geometry.py:_form_of lines 214, 226 (`in` / `not in`
   on set[type] consult a metaclass __eq__/__hash__).
 "none" models the CURRENT code (equality); every other Break value
 models identity, so each break isolates exactly its own mistake.
 ***************************************************************************)
Eq(a, b) == groups[a] = groups[b]

IdentityMode == Break # "none"

CodeMember(x, S) ==
    IF IdentityMode THEN x \in S ELSE \E y \in S : Eq(x, y)

(***************************************************************************
 Restricted-growth strings: every Eq partition exactly once.
 ***************************************************************************)
MaxRGS(g, k) ==
    CHOOSE m \in 0..N : (\A j \in 1..k : g[j] <= m)
                      /\ (k = 0 \/ \E j \in 1..k : g[j] = m)

RGS == {g \in [Nodes -> 1..N] :
            g[1] = 1 /\ \A i \in 2..N : g[i] \in 1..(MaxRGS(g, i - 1) + 1)}

\* code: EqMode selects the metaclass-equality scenario. "all" ranges over
\* every Eq partition (adversarial metaclasses included); "identity" fixes
\* one class per Tag (ordinary metaclasses); "equal" merges all Tags into
\* one Eq class (the F1 scenario: an always-equal metaclass).
Groups ==
    IF EqMode = "identity" THEN {[n \in Nodes |-> n]}
    ELSE IF EqMode = "equal" THEN {[n \in Nodes |-> 1]}
    ELSE RGS

(***************************************************************************
 Sequence helpers (all iterative, TLC-evaluable).
 ***************************************************************************)
RECURSIVE Rev_(_, _)
Rev_(s, i) == IF i < 1 THEN <<>> ELSE <<s[i]>> \circ Rev_(s, i - 1)
ReverseSeq(s) == Rev_(s, Len(s))

RECURSIVE Filt_(_, _, _)
Filt_(s, S, i) ==
    IF i > Len(s) THEN <<>>
    ELSE IF CodeMember(s[i], S) THEN Filt_(s, S, i + 1)
         ELSE <<s[i]>> \circ Filt_(s, S, i + 1)

RECURSIVE Recs_(_, _)
Recs_(s, i) ==
    IF i > Len(s) THEN <<>>
    ELSE <<[node |-> s[i], expanded |-> FALSE]>> \circ Recs_(s, i + 1)
ToRecs(s) == Recs_(s, 1)

(***************************************************************************
 Independent recursive declaration-order oracle, written from the spec
 ("its Bases, deepest first, in declaration order, each once, then the
 Tag"), using identity throughout.
 ***************************************************************************)
RECURSIVE Visit(_, _, _), VisitN(_, _, _, _)
Visit(b, t, Sn) ==
    IF t \in Sn THEN [f |-> <<>>, s |-> Sn]
    ELSE LET r == VisitN(b, t, Sn, 1)
         IN [f |-> Append(r.f, t), s |-> r.s \cup {t}]

VisitN(b, t, Sn, i) ==
    IF i > Len(b[t]) THEN [f |-> <<>>, s |-> Sn]
    ELSE LET d == b[t][i]
         IN IF d \in Sn THEN VisitN(b, t, Sn, i + 1)
            ELSE LET r1 == Visit(b, d, Sn)
                 IN LET r2 == VisitN(b, t, r1.s, i + 1)
                    IN [f |-> r1.f \circ r2.f, s |-> r2.s]

Oracle(b, t) == Visit(b, t, {}).f

RECURSIVE Clos(_, _)
Clos(b, t) == {t} \cup UNION {Clos(b, d) : d \in RangeSeq(b[t])}

FormSet == {form[i] : i \in 1..Len(form)}

Init ==
    /\ bases = [n \in Nodes |-> <<>>]
    /\ target \in Nodes
    /\ groups \in Groups
    /\ phase = "build"
    /\ form = <<>>
    /\ seen = {}
    /\ pending = <<>>

(***************************************************************************
 \* code: declaring `class S(B1, B2)` appends one ordered Base edge.
 Driver only: every declaration order reaches the same DAG state.
 ***************************************************************************)
BuildEdge ==
    \E n \in Nodes : \E bb \in 1..(n - 1) :
        /\ phase = "build"
        /\ bb \notin RangeSeq(bases[n])
        /\ bases' = [bases EXCEPT ![n] = Append(@, bb)]
        /\ UNCHANGED <<target, groups, phase, form, seen, pending>>

(***************************************************************************
 \* code: TopKit/geometry.py:_form_of lines 200-205 (seed the stack).
 ***************************************************************************)
StartRun ==
    /\ phase = "build"
    /\ phase' = "run"
    /\ pending' = <<[node |-> target, expanded |-> FALSE]>>
    /\ UNCHANGED <<bases, target, groups, form, seen>>

Top == pending[Len(pending)]
Rest == SubSeq(pending, 1, Len(pending) - 1)

PushList(direct, seen1) ==
    IF Break = "skip_diamond" THEN
        IF Len(direct) = 0 THEN <<>>
        ELSE IF CodeMember(direct[1], seen1) THEN <<>>
             ELSE <<[node |-> direct[1], expanded |-> FALSE]>>
    ELSE IF Break = "reverse_order" THEN ToRecs(Filt_(direct, seen1, 1))
    ELSE ToRecs(Filt_(ReverseSeq(direct), seen1, 1))

Marker(node) ==
    IF Break = "base_after_shape" THEN <<>>
    ELSE <<[node |-> node, expanded |-> TRUE]>>

(***************************************************************************
 \* code: TopKit/geometry.py:_form_of lines 210-212 (pop an expanded
   marker: the Tag's turn to join the Form, Bases already placed).
 ***************************************************************************)
EmitBase ==
    /\ phase = "run"
    /\ pending # <<>>
    /\ Top.expanded
    /\ pending' = Rest
    /\ form' = Append(form, Top.node)
    /\ UNCHANGED <<bases, target, groups, phase, seen>>

(***************************************************************************
 \* code: TopKit/geometry.py:_form_of lines 214-215 (pop-time skip of an
   already-seen Tag). Absent under Break="no_dedupe" (the break).
 ***************************************************************************)
SkipSeen ==
    /\ phase = "run"
    /\ pending # <<>>
    /\ ~Top.expanded
    /\ Break # "no_dedupe"
    /\ CodeMember(Top.node, seen)
    /\ pending' = Rest
    /\ UNCHANGED <<bases, target, groups, phase, form, seen>>

(***************************************************************************
 \* code: TopKit/geometry.py:_form_of lines 217-232 (first visit: join
   the seen-set, schedule emission, push unseen Bases). Under
   Break="base_after_shape" the Shape joins the Form BEFORE its Bases.
 ***************************************************************************)
VisitBase ==
    /\ phase = "run"
    /\ pending # <<>>
    /\ ~Top.expanded
    /\ Break = "no_dedupe" \/ ~CodeMember(Top.node, seen)
    /\ seen' = seen \cup {Top.node}
    /\ pending' = Rest \circ Marker(Top.node)
                      \circ PushList(bases[Top.node], seen \cup {Top.node})
    /\ form' = IF Break = "base_after_shape"
               THEN Append(form, Top.node) ELSE form
    /\ UNCHANGED <<bases, target, groups, phase>>

(***************************************************************************
 The Form is complete when the stack drains.
 ***************************************************************************)
FinishRun ==
    /\ phase = "run"
    /\ pending = <<>>
    /\ phase' = "done"
    /\ UNCHANGED <<bases, target, groups, form, seen, pending>>

DoneStutter ==
    /\ phase = "done"
    /\ UNCHANGED vars

Next == BuildEdge \/ StartRun \/ EmitBase \/ SkipSeen \/ VisitBase
        \/ FinishRun \/ DoneStutter

Spec == Init /\ [][Next]_vars

(***************************************************************************
 FC1_ClosureExact: the finished Form holds exactly the Tag-reachable
 closure, nothing missing, nothing extra. (Violated by F1.)
 ***************************************************************************)
FC1_ClosureExact == phase = "done" => FormSet = Clos(bases, target)

(***************************************************************************
 FC2_EachBaseOnce: no Tag appears twice in the finished Form.
 ***************************************************************************)
FC2_EachBaseOnce ==
    phase = "done" => \A i, j \in 1..Len(form) : i # j => form[i] # form[j]

(***************************************************************************
 FC3_BaseFirst: every Base sits before every Shape built on it.
 ***************************************************************************)
FC3_BaseFirst ==
    phase = "done" =>
        \A m \in 1..Len(form) :
            \A b \in RangeSeq(bases[form[m]]) :
                (\E i \in 1..Len(form) : form[i] = b)
                /\ (\A i \in 1..Len(form) : form[i] = b => i < m)

(***************************************************************************
 FC4_DeclarationOrder: the finished Form equals the independent
 recursive declaration-order oracle. Guarded by set equality so one
 equality-bug trace violates exactly FC1, never FC1+FC4 together.
 ***************************************************************************)
FC4_DeclarationOrder ==
    phase = "done" /\ FormSet = Clos(bases, target)
        => form = Oracle(bases, target)

=============================================================================
