\* WalkTurns: the saved-turn population walk (STEP-SPEC-35) under adversarial acts.
\*
\* PROMISE: A population walk checks current Field membership at each member's
\*   turn: a member Ripped before its turn is skipped, and the same Agent tagged
\*   again before its turn belongs again and keeps its turn
\*   (spec/SPECIFICATION.md:1467-1470; steps/spec/STEP-SPEC-35-population-walk-membership.md:26-40).
\* HARM: A loop acts on a departed Agent, or skips (or double-acts on) a retagged
\*   one; an arrested Agent is judged or acted on as sound or broken.
\*
\* COVERS:
\*   - TopKit/fields.py: _Field._Walk (saved join order + membership check at turn)
\*   - TopKit/fields.py: _Partition.__iter__ / __contains__ (sound/defective views,
\*     arrest exclusion, Post-time membership recheck)
\*   - TopKit/fields.py: _Partition.__invert__ (absorbing ~, STEP-SPEC-38)
\*   - TopKit/tags.py: MetaTag.__contains__ / __iter__ (sound membership rule)
\*   - TopKit/contracts.py: _holds_for_population (soundness + arrest False)
\* CONFIRMED AGAINST COMMIT 1bd5a2548a6bc8fadab9ca4c2451428dbf9b93e4
\*
\* ASSUMPTIONS (single thread; no user code runs inside one action):
\*   - One TLA+ action = one indivisible code step. Adversary acts (Rip, re-Tag,
\*     Post break/repair, arrest) run as whole user callbacks between walk turns;
\*     the walk's own per-turn check (membership + soundness + arrest) is atomic.
\*     Why atomic: TopKit is single-threaded and a turn holds no user callback
\*     between its membership test and its yield decision; a Post that Rips a
\*     member runs strictly before that member's turn, i.e. as an adversary act.
\*   - Saved join order is fixed as 1..N (join-order permutations need no
\*     separate check: the rule is per-turn and order-symmetric).
\*   - Adversary acts target only members at positions >= cursor. Acts on
\*     already-yielded members cannot change future yields: the walk never
\*     revisits a saved turn (STEP-SPEC-35 rule 4), and past members' soundness
\*     is never re-read. This cuts states, not behaviours.
\*   - One Field stands for the walked Tag's Field. An arrest by the WALKED
\*     tag removes membership (ArrestHere: _rip_field revokes the starting
\*     Field first; tests/test_arrest_guards.py:479,486-502). An arrest by
\*     ANOTHER tag keeps membership in the walked Field while the Agent is in
\*     custody (ArrestElsewhere: the agent stays in Fighter[:] but is in
\*     neither Fighter nor ~Fighter; tests/test_arrest_guards.py:90-94).
\*     Only the second shape can reach a sound/defective turn: it is the case
\*     PO3 guards.
\* NOT MODELLED:
\*   - The population algebra (`|` `&` `-`, laziness, ordering across sides):
\*     pure functions of the walk, no interleaving; covered by exhaustive
\*     real-code probes, not by this model.
\*   - `len` / `bool` / `in` sharing the walk's checks; Pins; safehouse walks;
\*     Post-concurrency (Ring 4: one Agent, one thread); GC/weakref expiry.
\*   - Release of an arrest mid-walk (no release act in the bound).
\*
\* INVARIANTS (each one plain sentence):
\*   - PO1_RipSkipped: a member Ripped before its turn is never yielded.
\*   - PO2_RetagKept: a member tagged again before its turn keeps its turn.
\*   - PO3_ArrestExcluded: an arrested Agent is never yielded by the sound or
\*     the defective walk (it is in neither `Wizard` nor `~Wizard`,
\*     spec/SPECIFICATION.md:1432-1434).
\*
\* Break CONSTANT (able to fail; each switch has a _<break>.cfg):
\*   - "none": the current code.
\*   - "frozen": the walk yields from the membership snapshot taken at walk
\*     start (the pre-STEP-35 behaviour); must violate PO1_RipSkipped.
\*   - "skipRetagged": the walk skips any agent ever Ripped even if re-tagged
\*     (the rejected "original weak-reference seat" implementation,
\*     STEP-SPEC-35 alternatives); must violate PO2_RetagKept.
\*   - "arrestedSound": the sound walk ignores arrest (counts arrested as
\*     sound); must violate PO3_ArrestExcluded.
\*
\* FINDING: none. The model of the current code satisfies all invariants.

------------------------------ MODULE WalkTurns ------------------------------
EXTENDS Integers, Sequences, TLC

CONSTANTS N, Break

VARIABLES
    \* code: TopKit/fields.py:_Field._members lines 375, 388-411 (live Field set)
    members,
    \* code: TopKit/contracts.py:_holds_for_population lines 84-101 (per-agent Post verdict)
    sound,
    \* code: TopKit/arrest.py:_safehouse lines 22, 25-32 (custody set); mirrors _arrest_of
    arrested,
    \* code: TopKit/fields.py:_Partition._label lines 482-490 (which view is walked)
    view,
    \* code: TopKit/fields.py:_Field._Walk lines 442-459 (position in saved order)
    cursor,
    \* history: yielded members in order, to state the walk rule as invariants
    yielded,
    \* history: set TRUE when a turn yields an agent the rule says to skip
    badSkip,
    \* history: set TRUE when a turn skips an agent the rule says to yield
    badMiss,
    \* history: set TRUE when a sound/defective turn yields an arrested agent
    badArrest,
    \* history: agents ever Ripped (lets the skipRetagged break tell rip+retag apart)
    everRipped,
    \* history: walk-start snapshot (lets the frozen break use stale membership)
    initMembers, initSound, initArrested

vars == <<members, sound, arrested, view, cursor, yielded,
          badSkip, badMiss, badArrest, everRipped,
          initMembers, initSound, initArrested>>

Views == {"sound", "defective", "raw"}
Agents == 1..N

\* code: TopKit/fields.py:_Partition.__iter__ lines 493-501 + TopKit/tags.py:MetaTag.__contains__ lines 396-403
Eligible(a) ==
    IF view = "raw" THEN a \in members
    ELSE IF view = "sound" THEN (a \in members) /\ (a \in sound) /\ (a \notin arrested)
    ELSE (a \in members) /\ (a \notin sound) /\ (a \notin arrested)

InitEligible(a) ==
    IF view = "raw" THEN a \in initMembers
    ELSE IF view = "sound"
        THEN (a \in initMembers) /\ (a \in initSound) /\ (a \notin initArrested)
    ELSE (a \in initMembers) /\ (a \notin initSound) /\ (a \notin initArrested)

\* Later members only (see header: acts on past members cannot change future yields).
Later(a) == cursor <= N /\ a >= cursor /\ a \in Agents

Init ==
    /\ members = Agents
    /\ sound = Agents
    /\ arrested = {}
    /\ view \in Views
    /\ cursor = 1
    /\ yielded = <<>>
    /\ badSkip = FALSE
    /\ badMiss = FALSE
    /\ badArrest = FALSE
    /\ everRipped = {}
    /\ initMembers = Agents
    /\ initSound = Agents
    /\ initArrested = {}

\* code: TopKit/lifecycle.py:_rip lines 47-93 (Rip half leaves the Field)
Rip(a) ==
    /\ Later(a)
    /\ a \in members
    /\ members' = members \ {a}
    /\ everRipped' = everRipped \cup {a}
    /\ UNCHANGED <<sound, arrested, view, cursor, yielded,
                   badSkip, badMiss, badArrest, initMembers, initSound, initArrested>>

\* code: TopKit/lifecycle.py:_apply path (re-Tagging restores Field membership,
\*   STEP-SPEC-35 rule 3: visited once at the saved turn, no second turn added)
RipRetag(a) ==
    /\ Later(a)
    /\ (a \notin members) \/ (a \notin everRipped)
    /\ members' = members \cup {a}
    /\ everRipped' = everRipped \cup {a}
    /\ UNCHANGED <<sound, arrested, view, cursor, yielded,
                   badSkip, badMiss, badArrest, initMembers, initSound, initArrested>>

\* code: TopKit/contracts.py:_holds... a Post flips its verdict (break / repair)
Brk(a) ==
    /\ Later(a)
    /\ a \in sound
    /\ sound' = sound \ {a}
    /\ UNCHANGED <<members, arrested, view, cursor, yielded,
                   badSkip, badMiss, badArrest, everRipped,
                   initMembers, initSound, initArrested>>

Fix(a) ==
    /\ Later(a)
    /\ a \notin sound
    /\ sound' = sound \cup {a}
    /\ UNCHANGED <<members, arrested, view, cursor, yielded,
                   badSkip, badMiss, badArrest, everRipped,
                   initMembers, initSound, initArrested>>

\* code: TopKit/lifecycle.py:_rip_field lines 173-202 (a failed Rip of the
\*   WALKED tag revokes the starting Field first: the Agent leaves the Field).
\*   tests/test_arrest_guards.py:479,486-502.
ArrestHere(a) ==
    /\ Later(a)
    /\ a \in members
    /\ members' = members \ {a}
    /\ arrested' = arrested \cup {a}
    /\ UNCHANGED <<sound, view, cursor, yielded,
                   badSkip, badMiss, badArrest, everRipped,
                   initMembers, initSound, initArrested>>

\* code: TopKit/access.py lines 470-472 + TopKit/contracts.py lines 87-88
\*   (an arrest by ANOTHER tag keeps the Agent in this Field, but soundness
\*   and the partition walks answer False while custody lasts).
\*   tests/test_arrest_guards.py:73-96: agent in Fighter[:] but in neither
\*   Fighter nor ~Fighter; list(Fighter) == [] and list(~Fighter) == [].
ArrestElsewhere(a) ==
    /\ Later(a)
    /\ a \in members
    /\ a \notin arrested
    /\ arrested' = arrested \cup {a}
    /\ UNCHANGED <<members, sound, view, cursor, yielded,
                   badSkip, badMiss, badArrest, everRipped,
                   initMembers, initSound, initArrested>>

\* The turn's yield decision. Correct code uses current eligibility; each Break
\* switch re-introduces one plausible mistake in exactly this decision.
\* "arrestedSound" drops the arrest guard in both walk layers that carry it
\* (sound and defective views): the `_arrest_of(agent) is None` guards in
\* TopKit/fields.py lines 500, 511, 514 and TopKit/tags.py lines 399, 402.
\* Soundness alone already returns False under custody
\* (TopKit/contracts.py lines 87-88), so a sound-only break would be masked
\* and could never yield an arrested agent. Its cfg therefore lists PO3
\* alone: TLC stops at the first violated invariant and names exactly one.
Decide(a) ==
    LET base == IF Break = "frozen" THEN InitEligible(a) ELSE Eligible(a)
    IN IF Break = "arrestedSound" /\ (view = "sound" \/ view = "defective")
       THEN (a \in members) /\ (a \in sound)
       ELSE IF Break = "skipRetagged"
       THEN base /\ (a \notin everRipped)
       ELSE base

\* code: TopKit/fields.py:_Field._Walk lines 455-459 (membership asked at the
\*   turn) + _Partition recheck lines 493-501 (judge, then recheck membership).
\*   No user code runs between the check and the yield: single thread.
Yield ==
    /\ cursor <= N
    /\ LET a == cursor IN
       LET elig == Eligible(a) IN
       LET dec == Decide(a) IN
           /\ yielded' = (IF dec THEN Append(yielded, a) ELSE yielded)
           /\ badSkip' = (badSkip \/ (dec /\ ~elig))
           /\ badMiss' = (badMiss \/ (~dec /\ elig))
           /\ badArrest' = (badArrest \/ (dec /\ (a \in arrested)
                                         /\ (view = "sound" \/ view = "defective")))
           /\ cursor' = cursor + 1
           /\ UNCHANGED <<members, sound, arrested, view, everRipped,
                          initMembers, initSound, initArrested>>

Adversary == \E a \in Agents :
    Rip(a) \/ RipRetag(a) \/ Brk(a) \/ Fix(a) \/ ArrestHere(a) \/ ArrestElsewhere(a)

\* Terminal stuttering step: with cursor past the last turn nothing can change.
Done == cursor = N + 1 /\ UNCHANGED vars

Next == Adversary \/ Yield \/ Done

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ members \subseteq Agents
    /\ sound \subseteq Agents
    /\ arrested \subseteq Agents
    /\ view \in Views
    /\ cursor \in 1..(N + 1)
    /\ everRipped \subseteq Agents
    /\ initMembers = Agents /\ initSound = Agents /\ initArrested = {}

\* A member Ripped before its turn is skipped (STEP-SPEC-35 rule 2).
PO1_RipSkipped == ~badSkip
\* A member tagged again before its turn keeps its turn (STEP-SPEC-35 rule 3).
PO2_RetagKept == ~badMiss
\* An arrested Agent is in neither the sound nor the defective walk
\* (spec/SPECIFICATION.md:1432-1434: "It is in neither `Wizard` nor `~Wizard`").
PO3_ArrestExcluded == ~badArrest

=============================================================================
