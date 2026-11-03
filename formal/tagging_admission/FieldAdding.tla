\* FieldAdding: the Tagging admission sequence and its failure boundaries.
\*
\* PROMISE (spec/SPECIFICATION.md:208-209, step 4 of section 0.6):
\*   "After its Imprints finish, the Agent enters the Tag's Field. Membership
\*   and history are established together."
\* HARM: an interrupted Tagging leaves a Field member without history: `Tag[:]`,
\*   `in Tag` and Field iteration include an Agent that `isinstance` denies;
\*   `del Tag[agent]` refuses with TagResolutionError and `del Tag[:]` aborts,
\*   poisoning whole-Field Rip for healthy members.
\*
\* PROMISE TA-1 (spec/SPECIFICATION.md:219-246, the outcome table):
\*   Gate refusal installs nothing of that turn; Gainings/Imprints failure keeps
\*   acquired non-Post Gains, discards provisional Posts, admits nothing of the
\*   unfinished turn, and keeps earlier completed turns; Post failure preserves
\*   membership (defective, not expelled); retry starts a fresh attempt
\*   (spec:239-241: "Calling `Tag(agent)` again after unfinished training starts
\*   a fresh attempt").
\*
\* COVERS:
\*   - TopKit/transactions.py: _apply (Form loop + retry boundary), _gate,
\*     _apply_one (actualize/rollback paths), _imprint, _inspect (Posts),
\*     _enter_field (FieldAdding)
\*   - TopKit/overlay.py: _gainings (acquired Gains stay), _remove_post_application
\*     (provisional Posts discarded)
\*   - TopKit/fields.py: _Field._Add / _Remove (Field entry), _Field.__contains__
\*     / __iter__ (Field membership reads)
\*   - TopKit/state.py: _State.active / .ever (membership vs history),
\*     _host_bindings_of / _restore_host_bindings (STEP-SPEC-37 preparation
\*     restore, assumed succeeding here; covered by real/ layer)
\*   - TopKit/tags.py: MetaTag.__instancecheck__ (history => isinstance),
\*     MetaTag.__contains__ (sound membership)
\* CONFIRMED AGAINST COMMIT 1bd5a2548a6bc8fadab9ca4c2451428dbf9b93e4
\*
\* ASSUMPTIONS (single thread; one Agent; one Tagging call of NTurns turns):
\*   - One TLA+ action = one indivisible code step: the code between two points
\*     where USER code can run (a Precondition, Record builder, Imprint, or Post
\*     callback; a host __setattr__/__init_subclass__ hook). Between such points
\*     there is no user callback, no await/yield, no thread switch, so no
\*     KeyboardInterrupt is assumed there -- EXCEPT between the three FieldAdding
\*     statements (field._Add / state.active.append / state.ever.add), which the
\*     model splits into separate actions precisely because an asynchronous
\*     interrupt can land there (this is the TA-2 finding, confirmed on the real
\*     code with sys.settrace injection; see FINDING below).
\*   - Host-actualization preparation always succeeds in this model. Rationale:
\*     STEP-SPEC-37 restore (class/dict/slots) has no interleaving question; it
\*     is covered by the real-code probes in real/ and by
\*     tests/test_host_actualization.py.
\*   - Single-Agent revocation (Rip of one member) is one indivisible step; the
\*     model does not interleave Rip with Tagging (Rip interplay belongs to the
\*     RipLedger model).
\*   - Retry of the same Tag is a fresh attempt at the failed turn's Gate
\*     (spec:239-241); the Retry action models exactly that.
\* NOT MODELLED:
\*   - Pin publication (_publish_to_field), Flag query-syntax words, secret
\*     rebinding, Constant protection details: orthogonal mechanisms with no
\*     additional interrupt window (guarded by `state.pinned is not None`,
\*     absent for ordinary Agents).
\*   - Arbitrary user-code side effects inside builders/Imprints (spec:284-286:
\*     "These authoring rules are not a Python sandbox"); the model records only
\*     their outcome (return / raise / interrupt).
\*   - Deletion tiers, At_Exit, GC/weakref expiry (DeletionTiers model).
\*
\* INVARIANTS (each one plain sentence):
\*   - TA1_GateRefuseClean: a Gate refusal installs nothing new of that turn\n\*     (prior-attempt Gains may already be present; spec:239-241).
\*   - TA1_RogueKeepsGains: a Gain/Imprint/interrupt failure keeps acquired Gains.
\*   - TA1_RogueNoMember: a Gain/Imprint/interrupt failure admits nothing of
\*     the unfinished turn.
\*   - TA1_RogueNoPosts: a Gain/Imprint/interrupt failure keeps no provisional
\*     Post of the unfinished turn.
\*   - TA1_EarlierTurnsStay: completed earlier turns stay admitted after a failure.
\*   - TA1_PostKeepsMember: Post failure preserves membership of every turn.
\*   - TA2_AtomicAdmission: Field entry, active membership and history are
\*     established together, in every reachable state.
\*
\* Break CONSTANT (able to fail; each switch has a matching _<break>.cfg that
\* lists ONLY the invariant it targets):
\*   - "none": the current code.
\*   - "gate-skip": the Gate check is skipped (turn proceeds as if it passed).
\*   - "keep-posts": a failed turn keeps its provisional Post.
\*   - "early-member": a raising Imprint still admits the turn (membership
\*     installed although Imprints did not finish).
\*   - "split-field": FieldAdding skips the history add (active without ever).
\*
\* FINDING TA-2 (kept; the model of the CURRENT code violates TA2_AtomicAdmission):
\*   Counterexample in code words: 1. Tag a fresh Host with a one-Record Tag:
\*   Gate passes, Gainings complete, Imprints finish. 2. FieldAdding runs
\*   field._Add(agent) (TopKit/fields.py:_Field._Add) and a KeyboardInterrupt
\*   lands before state.active.append(tag) (TopKit/transactions.py:_enter_field:540).
\*   3. Afterwards `agent in Tag[:]` is True and `agent in Tag` is True, but
\*   `isinstance(agent, Tag)` is False and `Tags(agent)` is empty; `del
\*   Tag[agent]` refuses with TagResolutionError ("is not active on this Agent",
\*   TopKit/lifecycle.py:148) so the phantom can never be Ripped; `del Tag[:]`
\*   aborts with the same error, leaving healthy members unripped.
\*   A later interrupt window (between state.active.append at :540 and
\*   state.ever.add at :552) leaves field+active without history: also
\*   `isinstance`-False while a member, though still rippable.
\*   Classification: violates a spec promise. spec/SPECIFICATION.md:208-209:
\*   "Membership and history are established together." spec:127-130: "Rip does
\*   not erase history: an Agent that has ever been in a Tag's Field remains an
\*   instance of that Tag." spec:305: "Rip is the only exit from a Field" (here
\*   Rip cannot end it). Reproducer: formal/tagging_admission/repro_TA2.py.
\*   Real-code injection points confirmed with sys.settrace over every executed
\*   line event of _enter_field plus the return event of _Field._Add, for first
\*   Tagging and reTagging (see real/explore.py).

--------------------------- MODULE FieldAdding ---------------------------
EXTENDS Integers, FiniteSets, TLC

CONSTANTS NTurns,        \* number of Form turns in the call (Base first); bound
          AllowInterrupt,\* whether KeyboardInterrupt may strike at modelled points
          Break          \* "none" | "gate-skip" | "keep-posts" | "early-member" | "split-field"

VARIABLES
    \* mirrors state.active in TopKit/state.py (admitted Tags)
    active,
    \* mirrors state.ever in TopKit/state.py (history: admitted at least once)
    ever,
    \* mirrors the Tag's _Field._members in TopKit/fields.py (Field entry)
    field,
    \* mirrors acquired non-Post bindings (state.records/actions in TopKit/state.py)
    gains,
    \* mirrors visible Postconditions (state.postconditions in TopKit/state.py)
    posts,
    \* history: which Form turn is being admitted (1..NTurns+1 = Posts phase)
    turn,
    \* history: Gate | Gainings | Imprints | FieldAdding | AddDone | EverDone | Done | Failed
    phase,
    \* history: "" | "Gate" | "Gain" | "Imprint" | "Post" | "Interrupt"
    failedKind,
    \* history: gains snapshot when the current turn's Gate was entered, so the
    \* refusal cleanliness is an action property (a refusal installs nothing NEW;
    \* prior-attempt Gains may already stand, spec:239-241)
    gateGains

vars == <<active, ever, field, gains, posts, turn, phase, failedKind, gateGains>>

TypeOK ==
    /\ active \in SUBSET (1..NTurns)
    /\ ever \in SUBSET (1..NTurns)
    /\ field \in SUBSET (1..NTurns)
    /\ gains \in SUBSET (1..NTurns)
    /\ posts \in SUBSET (1..NTurns)
    /\ turn \in 1..(NTurns+1)
    /\ phase \in {"Gate", "Gainings", "Imprints", "FieldAdding",
                  "AddDone", "EverDone", "Done", "Failed"}
    /\ failedKind \in {"", "Gate", "Gain", "Imprint", "Post", "Interrupt"}
    /\ gateGains \in SUBSET (1..NTurns)

Init ==
    /\ active = {}
    /\ ever = {}
    /\ field = {}
    /\ gains = {}
    /\ posts = {}
    /\ turn = 1
    /\ phase = "Gate"
    /\ failedKind = ""
    /\ gateGains = {}

\* code: TopKit/transactions.py:_gate lines 153-216. The Gate evaluates the
\* Tag's declarations plus its Precondition callbacks and refuses the turn
\* before any builder runs. One step: the callbacks' verdict is the
\* nondeterminism; nothing is installed on the live state either way.
GateRefuse ==
    /\ phase = "Gate"
    /\ turn <= NTurns
    /\ IF Break = "gate-skip"
       THEN \* BUG: the refused turn's gain leaks onto the live state (e.g. the
            \* scratch-composition _install writes through instead of to scratch).
            \* code: TopKit/transactions.py:_gate lines 186-196 with `scratch =
            \* state.Copy()` replaced by scratch = state.
            /\ gains' = gains \union {turn}
       ELSE /\ UNCHANGED gains
    /\ phase' = "Failed"
    /\ failedKind' = "Gate"
    /\ UNCHANGED <<active, ever, field, posts, turn, gateGains>>

\* code: TopKit/transactions.py:_gate lines 153-216 (same Gate as GateRefuse;
\* the passing verdict lets the turn proceed to Gainings). One step: nothing
\* is installed on the live state by the Gate itself.
GatePass ==
    /\ phase = "Gate"
    /\ turn <= NTurns
    /\ phase' = "Gainings"
    /\ UNCHANGED <<active, ever, field, gains, posts, turn, failedKind, gateGains>>


\* code: TopKit/overlay.py:_gainings lines 548-640. Each Record builder runs and
\* its value is installed; a builder that raises ends the turn keeping gains
\* acquired so far (modelled as the turn's gain acquired) without membership.
\* One step per outcome: no user code runs between a builder's return and its
\* install.
GainFail ==
    /\ phase = "Gainings"
    /\ turn <= NTurns
    /\ gains' = gains \union {turn}
    /\ IF Break = "keep-posts"
       THEN \* BUG: provisional Post of the failed turn is kept.
            /\ posts' = posts \union {turn}
       ELSE /\ UNCHANGED posts
    /\ phase' = "Failed"
    /\ failedKind' = "Gain"
    /\ UNCHANGED <<active, ever, field, turn, gateGains>>

GainOK ==
    /\ phase = "Gainings"
    /\ turn <= NTurns
    /\ gains' = gains \union {turn}
    /\ phase' = "Imprints"
    /\ UNCHANGED <<active, ever, field, posts, turn, failedKind, gateGains>>

\* code: TopKit/transactions.py:_imprint lines 673-698 (_imprint helper) called
\* from _apply_one. Imprints run with acquired Gains but no membership yet; a
\* raising Imprint ends the turn keeping Gains, admitting nothing. One step per
\* outcome: the callbacks are the nondeterminism.
ImprintFail ==
    /\ phase = "Imprints"
    /\ turn <= NTurns
    /\ IF Break = "early-member"
       THEN \* BUG: membership added although the Imprint raised (admission
            \* before Imprints finish): the failed turn stands admitted.
            /\ active' = active \union {turn}
            /\ ever' = ever \union {turn}
            /\ field' = field \union {turn}
       ELSE /\ UNCHANGED <<active, ever, field>>
    /\ phase' = "Failed"
    /\ failedKind' = "Imprint"
    /\ UNCHANGED <<gains, posts, turn, gateGains>>

ImprintOK ==
    /\ phase = "Imprints"
    /\ turn <= NTurns
    /\ UNCHANGED <<active, ever, field>>
    /\ phase' = "FieldAdding"
    /\ UNCHANGED <<gains, posts, turn, failedKind, gateGains>>

\* code: TopKit/transactions.py:_apply_one (the except-BaseException path) with
\* spec/SPECIFICATION.md:257-260 ("Python interruptions follow the same boundary
\* and propagate unchanged. Before FieldAdding they leave acquired Gains without
\* membership"). An interrupt inside a builder or Imprint keeps Gains, admits
\* nothing, and keeps its type (failedKind "Interrupt" is terminal for Retry
\* only in that it restarts the same way a failure does).
InterruptInTraining ==
    /\ AllowInterrupt = TRUE
    /\ phase \in {"Gainings", "Imprints"}
    /\ turn <= NTurns
    /\ gains' = gains \union {turn}
    /\ UNCHANGED posts
    /\ phase' = "Failed"
    /\ failedKind' = "Interrupt"
    /\ UNCHANGED <<active, ever, field, turn, gateGains>>

\* --- FieldAdding: the three real statements as separate steps ---
\* code: TopKit/transactions.py:_enter_field lines 538-552. The function runs
\*   field._Add(agent) (:539), state.active.append(tag) (:540),
\*   state.ever.add(tag) (:552); the post_names/words bookkeeping between them
\*   installs no Gains and admits nothing, so it is folded into AddActive. An
\*   asynchronous interrupt may land between any two statements (the TA-2
\*   finding, confirmed on the real code), so each statement is its own action.
FieldAdd ==
    \* code: TopKit/fields.py:_Field._Add lines 378-411 + transactions.py:_enter_field:539
    /\ phase = "FieldAdding"
    /\ turn <= NTurns
    /\ field' = field \union {turn}
    /\ phase' = "AddDone"
    /\ UNCHANGED <<active, ever, gains, posts, turn, failedKind, gateGains>>

InterruptAfterAdd ==
    \* interrupt between field._Add (:539) and state.active.append (:540)
    /\ AllowInterrupt = TRUE
    /\ phase = "AddDone"
    /\ turn <= NTurns
    /\ turn \notin active
    /\ phase' = "Failed"
    /\ failedKind' = "Interrupt"
    /\ UNCHANGED <<active, ever, field, gains, posts, turn, gateGains>>

AddActive ==
    \* code: TopKit/transactions.py:_enter_field:540 (state.active.append(tag))
    /\ phase = "AddDone"
    /\ turn <= NTurns
    /\ active' = active \union {turn}
    /\ phase' = "EverDone"
    /\ UNCHANGED <<ever, field, gains, posts, turn, failedKind, gateGains>>

InterruptAfterActive ==
    \* interrupt between state.active.append (:540) and state.ever.add (:552)
    /\ AllowInterrupt = TRUE
    /\ phase = "EverDone"
    /\ turn <= NTurns
    /\ turn \notin ever
    /\ phase' = "Failed"
    /\ failedKind' = "Interrupt"
    /\ UNCHANGED <<active, ever, field, gains, posts, turn, gateGains>>

AddEver ==
    \* code: TopKit/transactions.py:_enter_field:552 (state.ever.add(tag))
    /\ phase = "EverDone"
    /\ turn <= NTurns
    /\ IF Break = "split-field"
       THEN \* BUG: history add skipped -> active without ever.
            /\ UNCHANGED ever
       ELSE /\ ever' = ever \union {turn}
    /\ phase' = "Gate"
    /\ turn' = turn + 1
    /\ failedKind' = ""
    /\ gateGains' = gains
    /\ UNCHANGED <<active, field, gains, posts>>

\* --- Posts: once for the whole call ---
\* code: TopKit/transactions.py:_inspect lines 424-446. Every visible
\* Postcondition checks the finished Agent; a Post failure preserves
\* membership (spec:229-230: "A failure in step 5 raises, but membership
\* stays"). One step per outcome.
PostsPass ==
    /\ turn = NTurns + 1
    /\ phase = "Gate"
    /\ phase' = "Done"
    /\ UNCHANGED <<active, ever, field, gains, posts, turn, failedKind, gateGains>>

PostsFail ==
    /\ turn = NTurns + 1
    /\ phase = "Gate"
    /\ posts' = posts \union {1..NTurns}
    /\ phase' = "Failed"
    /\ failedKind' = "Post"
    /\ UNCHANGED <<active, ever, field, gains, turn, gateGains>>

\* code: TopKit/transactions.py:_apply (the for-member loop re-invokes the
\* turn's Gate on retry) with spec:239-241 ("starts a fresh attempt ... It does
\* not resume at the failed instruction"). Retry restarts the failed turn at
\* its Gate; completed earlier turns are untouched.
Retry ==
    /\ phase = "Failed"
    /\ failedKind \in {"Gain", "Imprint", "Interrupt"}
    /\ phase' = "Gate"
    /\ failedKind' = ""
    /\ gateGains' = gains
    /\ UNCHANGED <<active, ever, field, gains, posts, turn>>

\* Terminal stuttering step so deadlock checking is meaningful.
Done == phase \in {"Done", "Failed"} /\ UNCHANGED vars

Next ==
    \/ GateRefuse
    \/ GatePass
    \/ GainFail
    \/ GainOK
    \/ ImprintFail
    \/ ImprintOK
    \/ InterruptInTraining
    \/ FieldAdd
    \/ InterruptAfterAdd
    \/ AddActive
    \/ InterruptAfterActive
    \/ AddEver
    \/ PostsPass
    \/ PostsFail
    \/ Retry
    \/ Done

Spec == Init /\ [][Next]_vars

\* TA1_GateRefuseClean: a Gate refusal installs nothing new of that turn. Failed
\* attempts keep acquired Gains and the Gate judges the Agent's current state
\* (spec:239-241), so the turn's gain may already be present from an earlier
\* attempt; the clean case (no prior gain) must install nothing.
TA1_GateRefuseClean == (failedKind = "Gate" => (gains = gateGains /\ turn \notin active /\ turn \notin field /\ turn \notin ever))
\* TA1_RogueKeepsGains: a Gain/Imprint/interrupt failure keeps acquired Gains.
TA1_RogueKeepsGains == (failedKind \in {"Gain", "Imprint", "Interrupt"} => turn \in gains)
\* TA1_RogueNoMember: a Gain/Imprint/interrupt failure admits nothing of the unfinished turn.
TA1_RogueNoMember == (failedKind \in {"Gain", "Imprint", "Interrupt"} => (turn \notin active /\ turn \notin field /\ turn \notin ever))
\* TA1_RogueNoPosts: a Gain/Imprint/interrupt failure keeps no provisional Post of the unfinished turn.
TA1_RogueNoPosts == (failedKind \in {"Gain", "Imprint", "Interrupt"} => turn \notin posts)
\* TA1_EarlierTurnsStay: completed earlier turns stay admitted after a failure.
TA1_EarlierTurnsStay == (failedKind \in {"Gate", "Gain", "Imprint", "Interrupt"} => (\A t \in 1..(turn-1) : t \in active /\ t \in field /\ t \in ever))
\* TA1_PostKeepsMember: Post failure preserves membership of every turn.
TA1_PostKeepsMember == (failedKind = "Post" => (\A t \in 1..NTurns : t \in active /\ t \in field /\ t \in ever))
\* TA2_AtomicAdmission: Field entry, active membership and history are established together.
TA2_AtomicAdmission == (active = field /\ active = ever)

=============================================================================
