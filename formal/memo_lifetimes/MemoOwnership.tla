\* MemoOwnership: owner-local Tag memo publication/invalidation + reference-graph
\* collection for "a Field never keeps an Agent alive".
\*
\* PROMISE (a): a Form/declaration memo lives on its owning Tag; publication never
\*   overwrites a program binding at the key, never accepts a foreign memo, and
\*   invalidation retires the value so a later warm read misses
\*   (TopKit/IMPLEMENTATION_NOTES.md:225-237; TopKit/memo.py).
\*   HARM: a Tag silently answers with another Tag's cached scan, or a program's
\*   class attribute is destroyed by kit internals.
\* PROMISE (b): a Field never keeps an Agent alive; when an Agent ceases to exist
\*   it vanishes from every Field (spec/SPECIFICATION.md:135-137: "A Field never
\*   keeps an Agent alive. When an Agent ceases to exist it vanishes from every
\*   Field. Fields are indexed by identity").
\*   HARM: dead Agents accumulate in Fields (memory leak; stale members walked).
\*
\* COVERS:
\*   - TopKit/memo.py:_memo_of (lines 174-181), _remember_memo (184-202),
\*     _forget_memo (205-223)
\*   - TopKit/geometry.py:_form_of (179-243, memo use), TopKit/declarations.py:
\*     _declarations_of (809-820), _invalidate_declarations (830-833)
\*   - TopKit/fields.py:_Field._Add (378-402, weak _Member), _Remove (404-411),
\*     _Forget (413-418), __iter__/_Walk (431-459, strong snapshot held by the
\*     walk iterator while open, released on close/exhaustion)
\*   - TopKit/state.py:_Bound (660-697, weak _reference, ReferenceError),
\*     access.py:_Tag_View (752-774, weak _reference, ReferenceError)
\* CONFIRMED AGAINST COMMIT 1bd5a2548a6bc8fadab9ca4c2451428dbf9b93e4
\*
\* ASSUMPTIONS AND WHAT IS NOT MODELLED:
\*   - Single thread. The memo lock (_publication RLock) makes each of
\*     _remember_memo/_forget_memo one indivisible step: no user code runs while
\*     it is held (user metadata is inspected only outside the lock; the
\*     _metaclass_binding/_class_namespace reads inside are physical and never
\*     evaluate program code). The two-thread cache race is NOT modelled here
\*     (belongs to the concurrent-admission area).
\*   - One Tag namespace slot (one memo key) plus program/inherited bindings:
\*     enough because every key behaves identically and keys never interact
\*     (the memo key is identity-qualified per Tag: memo.py:_memo_key).
\*   - Program bindings are abstract ("prog"/inherited flag); memo values are
\*     abstract versions (1, 2). Metaclass collision is a boolean flag (model of
\*     _metaclass_binding: publication/invalidation blocked while set).
\*   - Part (b) models the reference graph explicitly: the agent is reachable
\*     iff a program root holds it or a STRONG edge does (open walk snapshot).
\*     Weak edges (Field seat -> agent, bound handle -> agent, Tag view ->
\*     agent) never keep the agent reachable. The walk snapshot holds STRONGLY
\*     while the walk is open (fields.py:_Walk "Holding the starting members
\*     keeps identity stable"), released on close/exhaustion. Arrest custody
\*     (which owns the agent by design while Rip work is unfinished) is NOT
\*     modelled: DropRoot means the program released its last root outside
\*     arrest.
\*   - gc timing is a nondeterministic DropRoot action; Reachability is the
\*     oracle, recomputed from the strong-edge set at every step.
\*   - TLC's own error trace is the replay (no trace variable in the model).
\*   - Bounds: 2 memo values, 1 walk, 1 handle, 1 view. TLC enumerates every
\*
\* WHY THIS SHAPE: lifetimes are a reachability question over a small
\*   strong/weak edge set, not an event ordering over time; TLA+ checks the
\*   invariant at every reachable graph state. No threads here.
\*
\* INVARIANTS (plain meaning):
\*   ML3_NoForeign: our memo slot never serves another Tag's wrapper as ours.
\*   ML3_Retired: after invalidation, no warm read serves the retired value.
\*   ML1_FieldWeak: with no program root and no open walk, the agent is gone
\*     (Field seat, bound handle and Tag view do not root it).
\*   ML1_WalkReleases: after a walk closes with no program root, the agent is
\*     gone (the snapshot no longer roots it).
\*
\* FINDING: none on the current code. Each break variant re-introduces one
\*   plausible real mistake; every _break.cfg below violates its invariant.
\*   Spec classification of every invariant: spec promise (quoted above).

------------------------------ MODULE MemoOwnership ------------------------------
EXTENDS Naturals, TLC, FiniteSets

CONSTANTS Break
\* Break = "" (current code) | "strong-field" | "overwrite" | "foreign"
\*         | "no-retire" | "strong-handle" | "walk-leak"
ASSUME Break \in {"", "strong-field", "overwrite", "foreign",
                  "no-retire", "strong-handle", "walk-leak"}

\* ---- memo slot state (part a) ----
\* slot: what is physically stored at the Tag's memo key:
\*   "empty" | "prog" (program's own binding) | "memo" (owned wrapper, or an
\*   adopted foreign wrapper under Break="foreign") | "foreign" (another Tag's
\*   wrapper planted at our key) | "retired" (owned wrapper, value retired,
\*   left behind a program descriptor that blocked deletion).
\* owned: meaningful when slot="memo": TRUE iff WE published it.
\* warm: last warm-read result ("none" = miss). Every non-read action resets
\*   it so stale reads can never mask a violation.
\* progLost/originForeign/sinceInvalidate/closedOnce: history flags, each set
\*   by exactly one action family; the invariants read them.
VARIABLES slot, owned, val, warm, collision, inherited,
          agentLive, fieldSeat, walkOpen, walkHolds, handleHeld, viewHeld,
          progKept, progLost, originForeign, sinceInvalidate, closedOnce
\* code: TopKit/memo.py:_class_namespace(tag) physical slot at `name`
\* mirrors the class __dict__ entry at the memo key.
\* code: TopKit/memo.py:_metaclass_binding(tag, name) -- collision flag.
\* code: TopKit/fields.py:_Field._members -- fieldSeat = seat present.
\* walkOpen/walkHolds: code TopKit/fields.py:__iter__/_Walk -- the iterator's
\*   strong snapshot (held list) while the walk is unfinished.
\* handleHeld/viewHeld: code TopKit/state.py:_Bound / access.py:_Tag_View held
\*   by the program (constant per path: held or not).
\* progKept: the program still holds a root to the agent (DropRoot clears it).
vars == <<slot, owned, val, warm, collision, inherited, agentLive, fieldSeat,
          walkOpen, walkHolds, handleHeld, viewHeld, progKept,
          progLost, originForeign, sinceInvalidate, closedOnce>>

TypeOK ==
    /\ slot \in {"empty", "prog", "memo", "foreign", "retired"}
    /\ owned \in BOOLEAN
    /\ val \in 0..2
    /\ warm \in {"none", "prog", "memo"}
    /\ collision \in BOOLEAN
    /\ inherited \in BOOLEAN
    /\ agentLive \in BOOLEAN
    /\ fieldSeat \in BOOLEAN
    /\ walkOpen \in BOOLEAN
    /\ walkHolds \in BOOLEAN
    /\ handleHeld \in BOOLEAN
    /\ viewHeld \in BOOLEAN
    /\ progKept \in BOOLEAN

Init ==
    /\ slot = "empty"
    /\ owned = FALSE
    /\ val = 0
    /\ warm = "none"
    /\ collision \in BOOLEAN
    /\ inherited \in BOOLEAN
    /\ agentLive = TRUE
    /\ fieldSeat = TRUE
    /\ walkOpen = FALSE
    /\ walkHolds = FALSE
    /\ handleHeld \in BOOLEAN
    /\ viewHeld \in BOOLEAN
    /\ progKept = TRUE
    /\ progLost = FALSE
    /\ originForeign = FALSE
    /\ sinceInvalidate = FALSE
    /\ closedOnce = FALSE

ClearWarm == warm' = "none"

\* code: TopKit/memo.py:_memo_of lines 174-181 (warm physical read: only an
\* owned wrapper at our key with our name hits; program bindings, foreign
\* wrappers and retired wrappers all miss).
WarmRead ==
    /\ warm' = (IF slot = "memo" /\ owned THEN "memo"
                ELSE IF slot = "prog" THEN "prog"
                ELSE "none")
    /\ UNCHANGED <<slot, owned, val, collision, inherited, agentLive, fieldSeat,
                   walkOpen, walkHolds, handleHeld, viewHeld, progKept,
                   progLost, originForeign, sinceInvalidate, closedOnce>>

\* code: TopKit/memo.py:_remember_memo lines 184-202.
\* Existing owned hit -> keep; collision -> recompute, publish nothing; owned
\* retired wrapper reused only if no Base binding appeared meanwhile; a
\* foreign wrapper is NEVER accepted (Break="foreign" adopts it); a program
\* binding (own or inherited) is NEVER overwritten (Break="overwrite" does).
Publish ==
    /\ \/ /\ slot = "memo"
          /\ UNCHANGED <<slot, owned, val>>
          /\ UNCHANGED <<progLost, originForeign>>
       \/ /\ slot = "retired"
          /\ ~collision
          /\ ~inherited
          /\ slot' = "memo"
          /\ owned' = TRUE
          /\ val' = (val % 2) + 1
          /\ UNCHANGED <<progLost, originForeign>>
       \/ /\ slot = "retired"
          /\ (collision \/ inherited)
          /\ UNCHANGED <<slot, owned, val>>
          /\ UNCHANGED <<progLost, originForeign>>
       \/ /\ slot = "foreign"
          /\ IF Break = "foreign"
             THEN /\ slot' = "memo" /\ owned' = FALSE /\ val' = (val % 2) + 1
                  /\ originForeign' = TRUE
                  /\ UNCHANGED progLost
             ELSE /\ UNCHANGED <<slot, owned, val>>
                  /\ UNCHANGED <<progLost, originForeign>>
       \/ /\ slot \in {"empty", "prog"}
          /\ IF collision
             THEN /\ UNCHANGED <<slot, owned, val>>
                  /\ UNCHANGED <<progLost, originForeign>>
             ELSE IF Break = "overwrite"
                  THEN /\ slot' = "memo" /\ owned' = TRUE /\ val' = (val % 2) + 1
                       /\ progLost' = (slot = "prog") \/ progLost
                       /\ UNCHANGED originForeign
                  ELSE IF slot = "prog" \/ inherited
                       THEN /\ UNCHANGED <<slot, owned, val>>
                            /\ UNCHANGED <<progLost, originForeign>>
                       ELSE /\ slot' = "memo" /\ owned' = TRUE /\ val' = (val % 2) + 1
                            /\ UNCHANGED <<progLost, originForeign>>
    /\ ClearWarm
    /\ sinceInvalidate' = FALSE
    /\ UNCHANGED <<collision, inherited, agentLive, fieldSeat, walkOpen,
                   walkHolds, handleHeld, viewHeld, progKept, closedOnce>>

\* code: TopKit/memo.py:_forget_memo lines 205-223 (retire the value; delete
\* the same wrapper only when no program descriptor blocks it; a foreign
\* wrapper is never ours to retire. Break="no-retire" leaves the value live).
Invalidate ==
    /\ \/ /\ slot = "memo"
          /\ owned
          /\ IF Break = "no-retire"
             THEN /\ UNCHANGED <<slot, owned, val>>
             ELSE /\ val' = 0
                  /\ owned' = FALSE
                  /\ IF collision THEN slot' = "retired" ELSE slot' = "empty"
       \/ /\ slot = "memo"
          /\ ~owned
          /\ UNCHANGED <<slot, owned, val>>
       \/ /\ slot \in {"empty", "prog", "foreign", "retired"}
          /\ UNCHANGED <<slot, owned, val>>
    /\ ClearWarm
    /\ sinceInvalidate' = TRUE
    /\ UNCHANGED <<collision, inherited, agentLive, fieldSeat, walkOpen,
                   walkHolds, handleHeld, viewHeld, progKept,
                   progLost, originForeign, closedOnce>>

\* The program plants/removes its own binding at the key; toggles the
\* metaclass collision or an inherited Base binding; a foreign wrapper gets
\* planted (adversarial setup, cf. test_memo_invalidation.py and
\* test_geometry_retention.py foreign-memo cases).
PlantProg ==
    /\ slot \in {"empty", "memo", "retired"}
    /\ slot' = "prog"
    /\ ClearWarm
    /\ UNCHANGED <<owned, val, collision, inherited, agentLive, fieldSeat,
                   walkOpen, walkHolds, handleHeld, viewHeld, progKept,
                   progLost, originForeign, sinceInvalidate, closedOnce>>
RemoveProg ==
    /\ slot = "prog"
    /\ slot' = "empty"
    /\ ClearWarm
    /\ UNCHANGED <<owned, val, collision, inherited, agentLive, fieldSeat,
                   walkOpen, walkHolds, handleHeld, viewHeld, progKept,
                   progLost, originForeign, sinceInvalidate, closedOnce>>
PlantForeign ==
    /\ slot = "empty"
    /\ slot' = "foreign"
    /\ ClearWarm
    /\ UNCHANGED <<owned, val, collision, inherited, agentLive, fieldSeat,
                   walkOpen, walkHolds, handleHeld, viewHeld, progKept,
                   progLost, originForeign, sinceInvalidate, closedOnce>>
ToggleCollision ==
    /\ collision' = ~collision
    /\ ClearWarm
    /\ UNCHANGED <<slot, owned, val, inherited, agentLive, fieldSeat, walkOpen,
                   walkHolds, handleHeld, viewHeld, progKept,
                   progLost, originForeign, sinceInvalidate, closedOnce>>
ToggleInherited ==
    /\ inherited' = ~inherited
    /\ ClearWarm
    /\ UNCHANGED <<slot, owned, val, collision, agentLive, fieldSeat, walkOpen,
                   walkHolds, handleHeld, viewHeld, progKept,
                   progLost, originForeign, sinceInvalidate, closedOnce>>

\* ---- reference-graph actions (part b) ----
\* The agent is reachable iff the program roots it or a STRONG edge does:
\* an open walk's snapshot (fields.py:_Walk), or, under break variants, a
\* strong Field seat / a strong bound handle. Field seats, bound handles and
\* Tag views are WEAK in the code and never root the agent.
StrongSet ==
    (IF walkOpen /\ walkHolds THEN {1} ELSE {}) \union
    (IF Break = "strong-field" /\ fieldSeat THEN {1} ELSE {}) \union
    (IF Break = "strong-handle" /\ handleHeld THEN {1} ELSE {})

\* code: the program releases its last root (del + gc.collect()).
DropRoot ==
    /\ progKept = TRUE
    /\ progKept' = FALSE
    /\ agentLive' = (Cardinality(StrongSet) > 0)
    /\ ClearWarm
    /\ UNCHANGED <<slot, owned, val, collision, inherited, fieldSeat, walkOpen,
                   walkHolds, handleHeld, viewHeld,
                   progLost, originForeign, sinceInvalidate, closedOnce>>

\* code: TopKit/fields.py:__iter__ lines 431-440 (snapshot the members).
OpenWalk ==
    /\ walkOpen = FALSE
    /\ walkOpen' = TRUE
    /\ walkHolds' = TRUE
    /\ ClearWarm
    /\ UNCHANGED <<slot, owned, val, collision, inherited, agentLive, fieldSeat,
                   handleHeld, viewHeld, progKept,
                   progLost, originForeign, sinceInvalidate, closedOnce>>

\* code: TopKit/fields.py:_Walk lines 442-459 (the generator is closed or
\* exhausted: the held list is released. Break="walk-leak" keeps it).
CloseWalk ==
    /\ walkOpen = TRUE
    /\ walkOpen' = FALSE
    /\ walkHolds' = (Break = "walk-leak")
    /\ closedOnce' = TRUE
    /\ IF ~progKept /\ (Break /= "walk-leak")
       THEN agentLive' = (Cardinality(
              (IF Break = "strong-field" /\ fieldSeat THEN {1} ELSE {}) \union
              (IF Break = "strong-handle" /\ handleHeld THEN {1} ELSE {})) > 0)
       ELSE UNCHANGED agentLive
    /\ ClearWarm
    /\ UNCHANGED <<slot, owned, val, collision, inherited, fieldSeat,
                   handleHeld, viewHeld, progKept,
                   progLost, originForeign, sinceInvalidate>>

\* code: TopKit/fields.py:_Remove lines 404-411 / _Forget 413-418 (Rip, or the
\* weakref callback after death, removes the seat).
RemoveSeat ==
    /\ fieldSeat = TRUE
    /\ fieldSeat' = FALSE
    /\ IF ~progKept /\ ~walkHolds
       THEN agentLive' = ((Break = "strong-handle") /\ handleHeld)
       ELSE UNCHANGED agentLive
    /\ ClearWarm
    /\ UNCHANGED <<slot, owned, val, collision, inherited, agentLive, walkOpen,
                   walkHolds, handleHeld, viewHeld, progKept,
                   progLost, originForeign, sinceInvalidate, closedOnce>>

Done ==
    /\ closedOnce
    /\ sinceInvalidate
    /\ progLost \/ TRUE
    /\ UNCHANGED vars

Next ==
    \/ WarmRead \/ Publish \/ Invalidate
    \/ PlantProg \/ RemoveProg \/ PlantForeign
    \/ ToggleCollision \/ ToggleInherited
    \/ DropRoot \/ OpenWalk \/ CloseWalk \/ RemoveSeat
    \/ Done

Spec == Init /\ [][Next]_vars

\* ---- invariants (state predicates; the box is added in Spec below) ----
\* Publication never turns a program binding into a memo.
ML3_NoOverwrite == ~progLost
\* Our memo slot never serves another Tag's wrapper as ours.
ML3_NoForeign == ~originForeign
\* After invalidation, no warm read serves the retired value.
ML3_Retired == (sinceInvalidate => warm /= "memo")
\* With no program root and no open walk, the agent is gone: the Field seat,
\* a bound handle and a Tag view do not root it.
ML1_FieldWeak == (~progKept /\ ~walkHolds => ~agentLive)
\* After a walk closes with no program root, the agent is gone.
ML1_WalkReleases == (closedOnce /\ ~progKept /\ ~walkOpen => ~agentLive)

=============================================================================
