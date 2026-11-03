---------------------------- MODULE RipLedger ----------------------------
(***************************************************************************
 * PROMISE (the law under test).
 *   `del Tag[x]` / `del Tag[:]` run a Tag's declared @Rip protocols as a
 *   saved run: a step that returned normally never runs again and runs only
 *   after all earlier steps did (P1); an ended application owes every step,
 *   custody ends only when all steps returned normally once, and retrying
 *   with working steps finishes everything and frees the Agent (P2); while
 *   cleanup is unfinished an ordinary act from outside the Agent's own
 *   cleanup either finishes ALL owed cleanup first or is refused with
 *   TagArrestedAccessError, while inside its own cleanup the act is allowed
 *   and another Agent's door gives no authority (P3); a fresh Tagging made
 *   while an older application has unfinished cleanup is never ended by
 *   retrying the old cleanup (P4); `del Tag[:]` ends every starting
 *   membership before ANY step callback runs (P5) and runs no further step
 *   directly after a directly-run step fails or is interrupted (P6).
 *   (spec/SPECIFICATION.md:293-340 law "Unfinished cleanup arrests the
 *   Agent"; spec:1605-1660 Rip protocols; steps/spec/STEP-SPEC-32-the-arrest
 *   decisions 1,2,5,6, lines 33-91.)
 * HARM (if it breaks).
 *   Cleanup steps run twice or are skipped; Agents walk free with unfinished
 *   work or stay arrested forever; arrested Agents answer ordinary acts; a
 *   fresh membership is silently ended by old cleanup; field members watch
 *   each other's teardowns run while still seated.
 *
 * COVERS (model action -> code).
 *   RipSelect/RipRun/RipRetry/RipDone  _rip (TopKit/lifecycle.py:47-92):
 *     saved-run lookup (_pending_run, rip_runs.py:66-76), fresh-run save
 *     (_save_run 44-63), own work first then retry-older (89-90).
 *   FieldOp push (+CbNestedField)  _rip_field snapshot+save
 *     (lifecycle.py:181-192, _pending_unrevoked_run rip_runs.py:79-99).
 *   FieldRevoke  the upfront revoke-everyone loop (lifecycle.py:194-196).
 *   FieldRun/FieldAfter/FieldDone  the member walk with post-member retry
 *     (lifecycle.py:198-201); a member failure stops the walk (no handler).
 *   SavedEnter/SavedInvoke/SavedFinish  _run_saved (rip_runs.py:169-212):
 *     re-entry guard (181-184), running flag (186,207-208), door
 *     (189, arrest.py:80-96), revoke-once (190-192), cursor-after-return
 *     (194-206), finish-one (210, _finish_run 102-123).
 *   RetryLoop  _retry_arrested drain in order with defer-running
 *     (rip_runs.py:126-166, called via lifecycle.py:204-225).
 *   ReqCheck/ReqAfter/ReqDoAct/ReqDoTag  _require_available
 *     (arrest.py:109-132) and the Tagging gate (transactions.py:80-82).
 *   CbOk/CbRaise/CbInterrupt  one @Rip step call with its outcome
 *     (_call_teardown lifecycle.py:325-377; invoke rip_runs.py:198).
 *   CbNested*  adversary ops issued from inside user code.
 *   CbSwallow/CbPropagate  user code catching or re-raising a nested
 *     failure. UnwindSaved/UnwindOther/TopClear  exception unwinding
 *     (RunSaved finally clears running; `except Exception` wraps, so
 *     interrupts keep their class).
 *   Stop/HealStep/HealAct/HealDone  end of path: retry everything with
 *     working steps, then act on each agent.
 * CONFIRMED AGAINST COMMIT 1bd5a2548a6bc8fadab9ca4c2451428dbf9b93e4.
 *
 * ATOMICITY (one TLA+ action = code between two user-code points).
 *   _revoke is one step: it runs no user callback (lifecycle.py:243-294).
 *   The field snapshot+save loop and the revoke-everyone loop are each one
 *   step (no user code between statements). Loop bookkeeping (pop ledger,
 *   advance cursor, push frame) joined with its step call is one step.
 *   Interrupts arrive only as a step's terminal outcome. Single thread.
 *
 * ASSUMPTIONS.
 * - One Tag class, NSteps = 2 steps per application; every application has
 *   steps (the _rip_empty fast path is not modelled).
 * - No Posts/Records/Overlays: _revoke keeps only the seat-preservation
 *   branch (fresh re-Tagging) and the revoked flag; held values, Post
 *   layers and runtime-type updates are not modelled.
 * - No lazy/pinned teardown calling conventions (plain step(agent) calls).
 * - Interrupts only inside user steps; revocation atomic; single thread
 *   and single context (no async); bool(agent) is derived (False exactly
 *   while the ledger is non-empty) and needs no state.
 * - Seat ids stand for both field._members and state.active; a fresh
 *   integer per Tagging, never reused. Bounds: MaxRuns = 8 run ids,
 *   MaxSeats = 6 seat ids, MaxFid = 4 field-rip frames.
 *
 * NOT MODELLED.
 * - Multi-Tag interleaving (ledgers hold same-Tag runs only; the mechanisms
 *   are tag-agnostic). Root/orphaned retry, finalizer and exit tiers
 *   (sibling area DeletionTiers). Tagging-form checks, lazy guards, async
 *   doors. KIT_FAULT-style unexpected exceptions (only documented refusals
 *   plus the adversary's Boom/Interrupt occur).
 *
 * INVARIANTS (one line each).
 *   P1_NoReplayInOrder       : an active step ran after all earlier steps
 *     of its run returned normally, never twice, never twice at once.
 *   P2_NoLossAndHeals        : every saved run is in a ledger or finished
 *     complete; no stuck running flag; Heal frees every Agent.
 *   P3_ArrestHolds           : an act succeeding outside the Agent's own
 *     cleanup leaves its ledger empty (else it was refused).
 *   P4_FreshTaggingSurvives  : a protected fresh seat stays current until
 *     an explicit Rip/field-Rip releases it.
 *   P5_FieldRipRevokesFirst  : past the revoke phase, no starting seat of
 *     a field Rip is current.
 *   P6_FieldRipStops         : no step runs directly under a failed field
 *     Rip.
 *
 * BREAK SWITCHES (CONSTANT Break; each has a _<break>.cfg that must fail).
 *   ""                       current code.
 *   "cursor_before_invoke"    cursor advances before invoke (P1).
 *   "no_running_guard"       re-entry guard deleted (P1).
 *   "finish_clears_all"      finish pops every run (P2).
 *   "door_not_agent_bound"   any open door authorises any Agent (P3).
 *   "del_ignores_saved_run"  del never selects the saved run (P4).
 *   "no_upfront_revoke"      field Rip skips the revoke-first loop (P5).
 *   "field_rip_continues"    field Rip swallows a member failure (P6).
 *   "running_stays_set"      running never cleared (P2).
 *   "retry_restarts"         failure resets the cursor (P1).
 *   "act_not_gated"          acts skip retry and refusal (P3).
 ***************************************************************************)

EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS NAgents, OpsBudget, Break

ASSUME NAgents \in 1..2 /\ OpsBudget \in 0..5
ASSUME Break \in {"", "cursor_before_invoke", "no_running_guard",
    "finish_clears_all", "door_not_agent_bound", "del_ignores_saved_run",
    "no_upfront_revoke", "field_rip_continues", "running_stays_set",
    "retry_restarts", "act_not_gated"}

NSteps == 2
MaxRuns == 8
MaxSeats == 6
MaxFid == 4

Agents == 1..NAgents
FullSteps == 0..(NSteps - 1)
AgentsSeq == [i \in 1..NAgents |-> i]

\* code: TopKit/lifecycle.py _rip/_rip_field/_run_saved/_retry_arrested;
\*   TopKit/rip_runs.py _RipRun (tag fixed: single Tag class);
\*   TopKit/arrest.py _rip_door/_may_act/_require_available.
\* mirrors: seat = current Field seat id per agent (0 = no membership,
\*   stands for field._members AND state.active); runs = run table by id
\*   (agent, saved seat, cursor, running, revoked); ledger[a] = custody
\*   sequence (_arrest_of(a).runs; arrested iff non-empty); stack = control
\*   frames with explicit pc; exc = propagating exception class.
\* history: ok (steps that returned normally, per run), protected/released
\*   (P4 fresh seats), fieldFailed (P6), finished/doneOk (P2), actLog (P3).
VARIABLES seat, nextSeat, runs, nextRun, ledger, stack, exc, ok, opsUsed,
    phase, protected, released, nextFid, fieldFailed, finished, doneOk,
    actLog, healedAct

vars == <<seat, nextSeat, runs, nextRun, ledger, stack, exc, ok, opsUsed,
    phase, protected, released, nextFid, fieldFailed, finished, doneOk,
    actLog, healedAct>>

TopFrame == stack[Len(stack)]
IsTop(k) == stack # <<>> /\ TopFrame.kind = k
PopStack == SubSeq(stack, 1, Len(stack) - 1)
NoSavedFrame == \A i \in 1..Len(stack) : stack[i].kind # "saved"

\* code: TopKit/arrest.py _may_act lines 99-106 (door open for a = a
\*   RunSaved frame inside its `with _rip_door` block, i.e. pc = "body").
DoorOpen(a) == \E i \in 1..Len(stack) :
    stack[i].kind = "saved" /\ stack[i].pc = "body" /\ stack[i].agent = a
AnyDoor == \E i \in 1..Len(stack) :
    stack[i].kind = "saved" /\ stack[i].pc = "body"
MayAct(a) == ledger[a] = <<>> \/
    (IF Break = "door_not_agent_bound" THEN AnyDoor ELSE DoorOpen(a))

InLedger(r) == \E a \in Agents : \E i \in 1..Len(ledger[a]) : ledger[a][i] = r

\* code: TopKit/lifecycle.py _revoke lines 243-294 (seat branch only: a
\*   fresh re-Tagging keeps its new membership; otherwise it ends).
RevSeat(seat_, r) ==
    LET a == runs[r].agent
    IN IF seat_[a] # 0 /\ seat_[a] # runs[r].seat THEN seat_
       ELSE [x \in Agents |-> IF x = a THEN 0 ELSE seat_[x]]

NewFrame(kind_, agent_, pc_, run_, idx_, own_, op_, defer_) ==
    [kind |-> kind_, agent |-> agent_, pc |-> pc_, run |-> run_,
     idx |-> idx_, own |-> own_, op |-> op_, defer |-> defer_,
     members |-> <<>>, mbruns |-> <<>>, starts |-> {}, fid |-> 0]

ReplaceTop(f) == [i \in 1..Len(stack) |-> IF i = Len(stack) THEN f ELSE stack[i]]

Init ==
    /\ seat = [a \in Agents |-> a]
    /\ nextSeat = NAgents + 1
    /\ runs = [r \in 1..MaxRuns |->
            [agent |-> 1, seat |-> 0, cursor |-> 0,
             running |-> FALSE, revoked |-> FALSE]]
    /\ nextRun = 1
    /\ ledger = [a \in Agents |-> <<>>]
    /\ stack = <<>>
    /\ exc = "none"
    /\ ok = [r \in 1..MaxRuns |-> {}]
    /\ opsUsed = 0
    /\ phase = "run"
    /\ protected = {}
    /\ released = {}
    /\ nextFid = 1
    /\ fieldFailed = [f \in 1..MaxFid |-> FALSE]
    /\ finished = {}
    /\ doneOk = [r \in 1..MaxRuns |-> {}]
    /\ actLog = <<>>
    /\ healedAct = {}

\* Shared snapshot+save computation for _rip_field (lifecycle.py:181-192):
\* members in join order; reuse the pending unrevoked run for the current
\* seat (rip_runs.py:79-99) else allocate a fresh run id. Helpers take the
\* state explicitly (a defined operator may not read variables, and
\* operators are not storable values, so no record of operators).
NeedNew(a, seat_, led_, runs_, nr) ==
    ~( \E r \in 1..(nr - 1) :
            (\E i \in 1..Len(led_[a]) : led_[a][i] = r)
            /\ runs_[r].seat = seat_[a] /\ ~runs_[r].revoked)

NewBefore(i, M, seat_, led_, runs_, nr) ==
    Cardinality({j \in 1..(i - 1) : NeedNew(M[j], seat_, led_, runs_, nr)})

PickOld(a, seat_, led_, runs_, nr) == CHOOSE r \in {r \in 1..(nr - 1) :
        (\E k \in 1..Len(led_[a]) : led_[a][k] = r)
        /\ runs_[r].seat = seat_[a] /\ ~runs_[r].revoked} : TRUE

FieldPush ==
    LET M == SelectSeq(AgentsSeq, LAMBDA a : seat[a] # 0) IN
    LET NT == Cardinality(
            {i \in 1..Len(M) : NeedNew(M[i], seat, ledger, runs, nextRun)}) IN
    LET R == [i \in 1..Len(M) |->
            IF NeedNew(M[i], seat, ledger, runs, nextRun)
            THEN nextRun + NewBefore(i, M, seat, ledger, runs, nextRun)
            ELSE PickOld(M[i], seat, ledger, runs, nextRun)] IN
    LET Starts == {<<a, seat[a]>> : a \in {M[i] : i \in 1..Len(M)}} IN
    LET NewAgent(rr) == M[CHOOSE i \in 1..Len(M) :
            NeedNew(M[i], seat, ledger, runs, nextRun) /\ R[i] = rr] IN
    /\ nextRun + NT <= MaxRuns + 1
    /\ nextFid <= MaxFid
    /\ runs' = [rr \in 1..MaxRuns |->
            IF rr >= nextRun /\ rr < nextRun + NT
            THEN [agent |-> NewAgent(rr), seat |-> seat[NewAgent(rr)],
                  cursor |-> 0, running |-> FALSE, revoked |-> FALSE]
            ELSE runs[rr]]
    /\ nextRun' = nextRun + NT
    /\ ledger' = [a \in Agents |->
            IF \E i \in 1..Len(M) : M[i] = a
            THEN Append(ledger[a], R[CHOOSE i \in 1..Len(M) : M[i] = a])
            ELSE ledger[a]]
    /\ released' = released \cup (protected \cap Starts)
    /\ fieldFailed' = [fieldFailed EXCEPT ![nextFid] = FALSE]
    /\ nextFid' = nextFid + 1
    /\ stack' = Append(stack,
            [kind |-> "field", agent |-> 0,
             pc |-> (IF Break = "no_upfront_revoke" THEN "run" ELSE "revoke"),
             run |-> 0, idx |-> 1, own |-> 0, op |-> "", defer |-> FALSE,
             members |-> M, mbruns |-> R, starts |-> Starts,
             fid |-> nextFid])
    /\ opsUsed' = opsUsed + 1

\* code: TopKit/tags.py __delitem__ lines 503-515 (del dispatches here).
TopRip(a) ==
    /\ phase = "run" /\ stack = <<>> /\ exc = "none"
    /\ opsUsed < OpsBudget /\ a \in Agents
    /\ opsUsed' = opsUsed + 1
    /\ stack' = Append(stack, NewFrame("rip", a, "select", 0, 0, 0, "", FALSE))
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, phase,
        protected, released, nextFid, fieldFailed, finished, doneOk,
        actLog, healedAct>>

TopField ==
    /\ phase = "run" /\ stack = <<>> /\ exc = "none" /\ opsUsed < OpsBudget
    /\ FieldPush
    /\ UNCHANGED <<seat, nextSeat, exc, ok, phase, protected,
        finished, doneOk, actLog, healedAct>>

TopTag(a) ==
    /\ phase = "run" /\ stack = <<>> /\ exc = "none"
    /\ opsUsed < OpsBudget /\ a \in Agents
    /\ opsUsed' = opsUsed + 1
    /\ stack' = Append(stack, NewFrame("req", a, "check", 0, 0, 0, "tag", FALSE))
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, phase,
        protected, released, nextFid, fieldFailed, finished, doneOk,
        actLog, healedAct>>

TopAct(a) ==
    /\ phase = "run" /\ stack = <<>> /\ exc = "none"
    /\ opsUsed < OpsBudget /\ a \in Agents
    /\ opsUsed' = opsUsed + 1
    /\ stack' = Append(stack, NewFrame("req", a, "check", 0, 0, 0, "act", FALSE))
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, phase,
        protected, released, nextFid, fieldFailed, finished, doneOk,
        actLog, healedAct>>

Stop ==
    /\ phase = "run" /\ stack = <<>> /\ exc = "none"
    /\ phase' = "heal"
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, stack, exc, ok,
        opsUsed, protected, released, nextFid, fieldFailed, finished,
        doneOk, actLog, healedAct>>

\* code: TopKit/lifecycle.py _rip lines 60-87 (lookup, fresh save, run).
RipSelect ==
    /\ phase = "run" /\ IsTop("rip") /\ exc = "none" /\ TopFrame.pc = "select"
    /\ LET fr == TopFrame IN LET a == fr.agent IN
       LET real == IF ledger[a] = <<>> THEN 0 ELSE Head(ledger[a]) IN
       LET sel == IF Break = "del_ignores_saved_run" THEN 0 ELSE real IN
       IF sel # 0 THEN
            /\ stack' = ReplaceTop([fr EXCEPT !.pc = "run", !.run = sel])
            /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok,
                opsUsed, phase, protected, released, nextFid, fieldFailed,
                finished, doneOk, actLog, healedAct>>
       ELSE IF seat[a] = 0 THEN
            /\ stack' = PopStack /\ exc' = "error"
            /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, ok,
                opsUsed, phase, protected, released, nextFid, fieldFailed,
                finished, doneOk, actLog, healedAct>>
       ELSE /\ nextRun <= MaxRuns
            /\ runs' = [runs EXCEPT ![nextRun] =
                    [agent |-> a, seat |-> seat[a], cursor |-> 0,
                     running |-> FALSE, revoked |-> FALSE]]
            /\ ledger' = [x \in Agents |->
                    IF x = a THEN Append(ledger[a], nextRun) ELSE ledger[x]]
            /\ nextRun' = nextRun + 1
            /\ released' = IF real = 0
                    THEN released \cup {p \in protected : p[1] = a}
                    ELSE released
            /\ stack' = ReplaceTop([fr EXCEPT !.pc = "run", !.run = nextRun])
            /\ UNCHANGED <<seat, nextSeat, exc, ok, opsUsed, phase,
                protected, nextFid, fieldFailed, finished, doneOk,
                actLog, healedAct>>

RipRun ==
    /\ phase = "run" /\ IsTop("rip") /\ exc = "none" /\ TopFrame.pc = "run"
    /\ LET fr == TopFrame IN
       stack' = Append(ReplaceTop([fr EXCEPT !.pc = "retry"]),
            NewFrame("saved", fr.agent, "enter", fr.run, 0, 0, "", FALSE))
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, opsUsed,
        phase, protected, released, nextFid, fieldFailed, finished,
        doneOk, actLog, healedAct>>

\* code: TopKit/lifecycle.py _rip lines 89-90 (retry older saved work).
RipRetry ==
    /\ phase = "run" /\ IsTop("rip") /\ exc = "none" /\ TopFrame.pc = "retry"
    /\ LET fr == TopFrame IN LET a == fr.agent IN
       /\ stack' = IF ledger[a] # <<>> /\ ~MayAct(a)
            THEN Append(ReplaceTop([fr EXCEPT !.pc = "done"]),
                    NewFrame("retry", a, "", 0, 0, 0, "", MayAct(a)))
            ELSE ReplaceTop([fr EXCEPT !.pc = "done"])
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, opsUsed,
        phase, protected, released, nextFid, fieldFailed, finished,
        doneOk, actLog, healedAct>>

RipDone ==
    /\ phase = "run" /\ IsTop("rip") /\ exc = "none" /\ TopFrame.pc = "done"
    /\ stack' = PopStack
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, opsUsed,
        phase, protected, released, nextFid, fieldFailed, finished,
        doneOk, actLog, healedAct>>

\* code: TopKit/lifecycle.py _rip_field lines 194-196 (one step, no user code).
FieldRevoke ==
    /\ phase = "run" /\ IsTop("field") /\ exc = "none"
    /\ TopFrame.pc = "revoke"
    /\ LET fr == TopFrame IN
       /\ seat' = [a \in Agents |->
            IF \E i \in 1..Len(fr.members) : fr.members[i] = a
            THEN LET r == fr.mbruns[
                        CHOOSE i \in 1..Len(fr.members) : fr.members[i] = a]
                 IN IF seat[a] # 0 /\ seat[a] # runs[r].seat THEN seat[a] ELSE 0
            ELSE seat[a]]
       /\ runs' = [r \in 1..MaxRuns |->
            IF \E i \in 1..Len(fr.mbruns) : fr.mbruns[i] = r
            THEN [runs[r] EXCEPT !.revoked = TRUE]
            ELSE runs[r]]
       /\ stack' = ReplaceTop([fr EXCEPT !.pc = "run"])
    /\ UNCHANGED <<nextSeat, nextRun, ledger, exc, ok, opsUsed, phase,
        protected, released, nextFid, fieldFailed, finished, doneOk,
        actLog, healedAct>>

\* code: TopKit/lifecycle.py _rip_field lines 198-199 (member walk).
FieldRun ==
    /\ phase = "run" /\ IsTop("field") /\ exc = "none"
    /\ TopFrame.pc = "run" /\ TopFrame.idx <= Len(TopFrame.members)
    /\ LET fr == TopFrame IN
       stack' = Append(
            ReplaceTop([fr EXCEPT !.pc = "after", !.idx = fr.idx + 1]),
            NewFrame("saved", fr.members[fr.idx], "enter",
                fr.mbruns[fr.idx], 0, fr.fid, "", FALSE))
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, opsUsed,
        phase, protected, released, nextFid, fieldFailed, finished,
        doneOk, actLog, healedAct>>

\* code: TopKit/lifecycle.py _rip_field lines 200-201 (post-member retry).
FieldAfter ==
    /\ phase = "run" /\ IsTop("field") /\ exc = "none"
    /\ TopFrame.pc = "after"
    /\ LET fr == TopFrame IN LET a == fr.members[fr.idx - 1] IN
       stack' = IF ledger[a] # <<>> /\ ~MayAct(a)
            THEN Append(ReplaceTop([fr EXCEPT !.pc = "run"]),
                    NewFrame("retry", a, "", 0, 0, 0, "", MayAct(a)))
            ELSE ReplaceTop([fr EXCEPT !.pc = "run"])
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, opsUsed,
        phase, protected, released, nextFid, fieldFailed, finished,
        doneOk, actLog, healedAct>>

FieldAfterErr ==
    /\ phase = "run" /\ IsTop("field") /\ TopFrame.pc = "after"
    /\ exc = "error" /\ Break = "field_rip_continues"
    /\ exc' = "none"
    /\ stack' = ReplaceTop([TopFrame EXCEPT !.pc = "run"])
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, ok, opsUsed,
        phase, protected, released, nextFid, fieldFailed, finished,
        doneOk, actLog, healedAct>>

FieldDone ==
    /\ phase = "run" /\ IsTop("field") /\ exc = "none"
    /\ TopFrame.pc = "run" /\ TopFrame.idx > Len(TopFrame.members)
    /\ stack' = PopStack
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, opsUsed,
        phase, protected, released, nextFid, fieldFailed, finished,
        doneOk, actLog, healedAct>>

\* code: TopKit/rip_runs.py _run_saved lines 181-193 (guard, flag, door,
\*   revoke-once). The door opens as pc becomes "body".
SavedEnter ==
    /\ phase = "run" /\ IsTop("saved") /\ exc = "none"
    /\ TopFrame.pc = "enter"
    /\ LET fr == TopFrame IN LET r == fr.run IN
       IF runs[r].running /\ Break # "no_running_guard" THEN
            /\ stack' = PopStack /\ exc' = "error"
            /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, ok,
                opsUsed, phase, protected, released, nextFid, fieldFailed,
                finished, doneOk, actLog, healedAct>>
       ELSE /\ runs' = [runs EXCEPT ![r].running = TRUE,
                                        ![r].revoked = TRUE]
            /\ seat' = RevSeat(seat, r)
            /\ stack' = ReplaceTop([fr EXCEPT !.pc = "body"])
            /\ UNCHANGED <<nextSeat, nextRun, ledger, exc, ok, opsUsed,
                phase, protected, released, nextFid, fieldFailed,
                finished, doneOk, actLog, healedAct>>

\* code: TopKit/rip_runs.py _run_saved lines 194-206 (invoke; cursor moves
\*   only after a normal return).
SavedInvoke ==
    /\ phase = "run" /\ IsTop("saved") /\ exc = "none"
    /\ TopFrame.pc = "body"
    /\ LET fr == TopFrame IN LET r == fr.run IN
       LET c == runs[r].cursor IN
       IF c < NSteps THEN
            /\ stack' = Append(stack,
                    NewFrame("cb", fr.agent, "", r, c, fr.own, "", FALSE))
            /\ runs' = IF Break = "cursor_before_invoke"
                    THEN [runs EXCEPT ![r].cursor = c + 1]
                    ELSE runs
            /\ UNCHANGED <<seat, nextSeat, nextRun, ledger, exc, ok,
                opsUsed, phase, protected, released, nextFid, fieldFailed,
                finished, doneOk, actLog, healedAct>>
       ELSE /\ stack' = ReplaceTop([fr EXCEPT !.pc = "finish"])
            /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok,
                opsUsed, phase, protected, released, nextFid, fieldFailed,
                finished, doneOk, actLog, healedAct>>

\* code: TopKit/rip_runs.py _finish_run lines 102-123 (release only this run).
SavedFinish ==
    /\ phase = "run" /\ IsTop("saved") /\ exc = "none"
    /\ TopFrame.pc = "finish"
    /\ LET fr == TopFrame IN LET r == fr.run IN LET a == fr.agent IN
       /\ runs' = [runs EXCEPT ![r].running = FALSE]
       /\ finished' = finished \cup {r}
       /\ doneOk' = [doneOk EXCEPT ![r] = ok[r]]
       /\ ledger' = IF Break = "finish_clears_all"
            THEN [x \in Agents |-> IF x = a THEN <<>> ELSE ledger[x]]
            ELSE [x \in Agents |-> IF x = a
                    THEN SelectSeq(ledger[x], LAMBDA q : q # r)
                    ELSE ledger[x]]
       /\ stack' = PopStack
    /\ UNCHANGED <<seat, nextSeat, nextRun, exc, ok, opsUsed, phase,
        protected, released, nextFid, fieldFailed, actLog, healedAct>>

\* code: TopKit/rip_runs.py _run_saved lines 199-208 (`except Exception`
\*   wraps; `finally` clears running; interrupts keep their class).
UnwindSaved ==
    /\ IsTop("saved") /\ exc # "none"
    /\ LET fr == TopFrame IN LET r == fr.run IN
       /\ runs' = [x \in 1..MaxRuns |->
            IF x = r
            THEN [agent |-> runs[r].agent, seat |-> runs[r].seat,
                  cursor |-> (IF Break = "retry_restarts" /\ exc = "error"
                        THEN 0 ELSE runs[r].cursor),
                  running |-> (Break = "running_stays_set"),
                  revoked |-> runs[r].revoked]
            ELSE runs[x]]
       /\ fieldFailed' = IF fr.own # 0
            THEN [fieldFailed EXCEPT ![fr.own] = TRUE]
            ELSE fieldFailed
       /\ stack' = PopStack
    /\ UNCHANGED <<seat, nextSeat, nextRun, ledger, exc, ok, opsUsed,
        phase, protected, released, nextFid, finished, doneOk,
        actLog, healedAct>>

\* code: TopKit/rip_runs.py _retry_arrested lines 152-166 (ledger order,
\*   defer a running step to its outer call).
RetryLoop ==
    /\ phase = "run" /\ IsTop("retry") /\ exc = "none"
    /\ LET fr == TopFrame IN LET a == fr.agent IN
       IF ledger[a] = <<>> THEN
            /\ stack' = PopStack
            /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok,
                opsUsed, phase, protected, released, nextFid, fieldFailed,
                finished, doneOk, actLog, healedAct>>
       ELSE LET r == Head(ledger[a]) IN
            IF fr.defer /\ runs[r].running THEN
                /\ stack' = PopStack
                /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc,
                    ok, opsUsed, phase, protected, released, nextFid,
                    fieldFailed, finished, doneOk, actLog, healedAct>>
            ELSE /\ stack' = Append(stack,
                        NewFrame("saved", a, "enter", r, 0, 0, "", FALSE))
                 /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc,
                     ok, opsUsed, phase, protected, released, nextFid,
                     fieldFailed, finished, doneOk, actLog, healedAct>>

\* code: TopKit/arrest.py _require_available lines 109-119 (retry first).
ReqCheck ==
    /\ phase = "run" /\ IsTop("req") /\ exc = "none"
    /\ TopFrame.pc = "check"
    /\ LET fr == TopFrame IN LET a == fr.agent IN
       IF Break = "act_not_gated" \/ MayAct(a) THEN
            /\ stack' = ReplaceTop([fr EXCEPT !.pc = "do"])
            /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok,
                opsUsed, phase, protected, released, nextFid, fieldFailed,
                finished, doneOk, actLog, healedAct>>
       ELSE /\ stack' = Append(ReplaceTop([fr EXCEPT !.pc = "after"]),
                    NewFrame("retry", a, "", 0, 0, 0, "", MayAct(a)))
            /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok,
                opsUsed, phase, protected, released, nextFid, fieldFailed,
                finished, doneOk, actLog, healedAct>>

\* code: TopKit/arrest.py _require_available lines 129-132 (refusal).
ReqAfter ==
    /\ phase = "run" /\ IsTop("req") /\ exc = "none"
    /\ TopFrame.pc = "after"
    /\ LET fr == TopFrame IN LET a == fr.agent IN
       IF ledger[a] = <<>> THEN
            /\ stack' = ReplaceTop([fr EXCEPT !.pc = "do"])
            /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok,
                opsUsed, phase, protected, released, nextFid, fieldFailed,
                finished, doneOk, actLog, healedAct>>
       ELSE /\ stack' = PopStack
            /\ exc' = "error"
            /\ actLog' = IF fr.op = "act"
                THEN Append(actLog, [agent |-> a, ownDoor |-> DoorOpen(a),
                        emptyAfter |-> FALSE, outcome |-> "refused"])
                ELSE actLog
            /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, ok,
                opsUsed, phase, protected, released, nextFid, fieldFailed,
                finished, doneOk, healedAct>>

ReqDoAct ==
    /\ phase = "run" /\ IsTop("req") /\ exc = "none"
    /\ TopFrame.pc = "do" /\ TopFrame.op = "act"
    /\ actLog' = Append(actLog, [agent |-> TopFrame.agent,
            ownDoor |-> DoorOpen(TopFrame.agent),
            emptyAfter |-> (ledger[TopFrame.agent] = <<>>),
            outcome |-> "ok"])
    /\ stack' = PopStack
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, opsUsed,
        phase, protected, released, nextFid, fieldFailed, finished,
        doneOk, healedAct>>

\* code: TopKit/transactions.py _apply lines 80-89 (gate, then fresh seat;
\*   tagging the active seat is a no-op).
ReqDoTag ==
    /\ phase = "run" /\ IsTop("req") /\ exc = "none"
    /\ TopFrame.pc = "do" /\ TopFrame.op = "tag"
    /\ LET a == TopFrame.agent IN
       IF seat[a] # 0 THEN
            /\ stack' = PopStack
            /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok,
                opsUsed, phase, protected, released, nextFid, fieldFailed,
                finished, doneOk, actLog, healedAct>>
       ELSE /\ nextSeat <= MaxSeats
            /\ seat' = [seat EXCEPT ![a] = nextSeat]
            /\ protected' = protected \cup
                (IF (\E r \in 1..(nextRun - 1) :
                        \E i \in 1..Len(ledger[a]) : ledger[a][i] = r)
                    \/ (\E i \in 1..Len(stack) :
                        stack[i].kind = "cb" /\ stack[i].agent = a)
                 THEN {<<a, nextSeat>>} ELSE {})
            /\ nextSeat' = nextSeat + 1
            /\ stack' = PopStack
            /\ UNCHANGED <<runs, nextRun, ledger, exc, ok, opsUsed, phase,
                released, nextFid, fieldFailed, finished, doneOk,
                actLog, healedAct>>

\* code: TopKit/rip_runs.py line 206 (normal return advances the cursor).
CbOk ==
    /\ phase = "run" /\ IsTop("cb") /\ exc = "none"
    /\ LET fr == TopFrame IN LET r == fr.run IN
       /\ ok' = [ok EXCEPT ![r] = @ \cup {fr.idx}]
       /\ runs' = IF Break = "cursor_before_invoke" THEN runs
            ELSE [runs EXCEPT ![r].cursor = fr.idx + 1]
       /\ stack' = PopStack
    /\ UNCHANGED <<seat, nextSeat, nextRun, ledger, exc, opsUsed, phase,
        protected, released, nextFid, fieldFailed, finished, doneOk,
        actLog, healedAct>>

CbRaise ==
    /\ phase = "run" /\ IsTop("cb") /\ exc = "none"
    /\ exc' = "error" /\ stack' = PopStack
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, ok, opsUsed,
        phase, protected, released, nextFid, fieldFailed, finished,
        doneOk, actLog, healedAct>>

CbInterrupt ==
    /\ phase = "run" /\ IsTop("cb") /\ exc = "none"
    /\ exc' = "interrupt" /\ stack' = PopStack
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, ok, opsUsed,
        phase, protected, released, nextFid, fieldFailed, finished,
        doneOk, actLog, healedAct>>

\* User code catches a nested failure and carries on.
CbSwallow ==
    /\ IsTop("cb") /\ exc # "none"
    /\ exc' = "none"
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, stack, ok,
        opsUsed, phase, protected, released, nextFid, fieldFailed,
        finished, doneOk, actLog, healedAct>>

\* User code lets a nested failure propagate.
CbPropagate ==
    /\ IsTop("cb") /\ exc # "none"
    /\ stack' = PopStack
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok,
        opsUsed, phase, protected, released, nextFid, fieldFailed,
        finished, doneOk, actLog, healedAct>>

CbNestedRip(a) ==
    /\ phase = "run" /\ IsTop("cb") /\ exc = "none"
    /\ opsUsed < OpsBudget /\ a \in Agents
    /\ opsUsed' = opsUsed + 1
    /\ stack' = Append(stack, NewFrame("rip", a, "select", 0, 0, 0, "", FALSE))
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, phase,
        protected, released, nextFid, fieldFailed, finished, doneOk,
        actLog, healedAct>>

CbNestedField ==
    /\ phase = "run" /\ IsTop("cb") /\ exc = "none" /\ opsUsed < OpsBudget
    /\ FieldPush
    /\ UNCHANGED <<seat, nextSeat, exc, ok, phase, protected,
        finished, doneOk, actLog, healedAct>>

CbNestedTag(a) ==
    /\ phase = "run" /\ IsTop("cb") /\ exc = "none"
    /\ opsUsed < OpsBudget /\ a \in Agents
    /\ opsUsed' = opsUsed + 1
    /\ stack' = Append(stack, NewFrame("req", a, "check", 0, 0, 0, "tag", FALSE))
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, phase,
        protected, released, nextFid, fieldFailed, finished, doneOk,
        actLog, healedAct>>

CbNestedAct(a) ==
    /\ phase = "run" /\ IsTop("cb") /\ exc = "none"
    /\ opsUsed < OpsBudget /\ a \in Agents
    /\ opsUsed' = opsUsed + 1
    /\ stack' = Append(stack, NewFrame("req", a, "check", 0, 0, 0, "act", FALSE))
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, phase,
        protected, released, nextFid, fieldFailed, finished, doneOk,
        actLog, healedAct>>

\* Frames with no handler (rip, field, retry, require) just unwind.
UnwindOther ==
    /\ (IsTop("rip") \/ IsTop("field") \/ IsTop("retry") \/ IsTop("req"))
    /\ exc # "none"
    /\ stack' = PopStack
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, exc, ok, opsUsed,
        phase, protected, released, nextFid, fieldFailed, finished,
        doneOk, actLog, healedAct>>

\* A top-level failure is observed by the caller.
TopClear ==
    /\ stack = <<>> /\ exc # "none"
    /\ exc' = "none"
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, stack, ok,
        opsUsed, phase, protected, released, nextFid, fieldFailed,
        finished, doneOk, actLog, healedAct>>

\* HEAL: retry everything with working steps, then act on each agent.
HealStep ==
    /\ phase = "heal" /\ stack = <<>> /\ exc = "none"
    /\ \E a \in Agents :
        /\ ledger[a] # <<>>
        /\ LET r == Head(ledger[a]) IN
           /\ ~runs[r].running
           /\ LET c == runs[r].cursor IN
              /\ seat' = RevSeat(seat, r)
              /\ runs' = [x \in 1..MaxRuns |->
                    IF x = r
                    THEN [agent |-> runs[r].agent, seat |-> runs[r].seat,
                          cursor |-> (IF c < NSteps THEN c + 1 ELSE c),
                          running |-> FALSE, revoked |-> TRUE]
                    ELSE runs[x]]
              /\ ok' = [ok EXCEPT ![r] =
                    IF c < NSteps THEN @ \cup {c} ELSE @]
              /\ IF c + 1 >= NSteps THEN
                    /\ ledger' = [x \in Agents |->
                            IF x = a THEN Tail(ledger[x]) ELSE ledger[x]]
                    /\ finished' = finished \cup {r}
                    /\ doneOk' = [doneOk EXCEPT ![r] =
                            (IF c < NSteps THEN ok[r] \cup {c} ELSE ok[r])]
                 ELSE /\ UNCHANGED <<ledger, finished, doneOk>>
    /\ UNCHANGED <<nextSeat, nextRun, stack, exc, opsUsed, phase, protected,
        released, nextFid, fieldFailed, actLog, healedAct>>

HealAct ==
    /\ phase = "heal" /\ stack = <<>> /\ exc = "none"
    /\ \A a \in Agents : ledger[a] = <<>>
    /\ \E a \in Agents :
        /\ a \notin healedAct
        /\ healedAct' = healedAct \cup {a}
        /\ actLog' = Append(actLog, [agent |-> a,
                ownDoor |-> DoorOpen(a), emptyAfter |-> TRUE,
                outcome |-> "ok"])
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, stack, exc, ok,
        opsUsed, phase, protected, released, nextFid, fieldFailed,
        finished, doneOk>>

HealDone ==
    /\ phase = "heal" /\ stack = <<>> /\ exc = "none"
    /\ \A a \in Agents : ledger[a] = <<>>
    /\ healedAct = Agents
    /\ phase' = "done"
    /\ UNCHANGED <<seat, nextSeat, runs, nextRun, ledger, stack, exc, ok,
        opsUsed, protected, released, nextFid, fieldFailed, finished,
        doneOk, actLog, healedAct>>

Done ==
    /\ phase = "done"
    /\ UNCHANGED vars

Next ==
    \/ (\E a \in Agents : TopRip(a))
    \/ TopField
    \/ (\E a \in Agents : TopTag(a))
    \/ (\E a \in Agents : TopAct(a))
    \/ Stop
    \/ RipSelect \/ RipRun \/ RipRetry \/ RipDone
    \/ FieldRevoke \/ FieldRun \/ FieldAfter \/ FieldAfterErr \/ FieldDone
    \/ SavedEnter \/ SavedInvoke \/ SavedFinish \/ UnwindSaved
    \/ RetryLoop
    \/ ReqCheck \/ ReqAfter \/ ReqDoAct \/ ReqDoTag
    \/ CbOk \/ CbRaise \/ CbInterrupt \/ CbSwallow \/ CbPropagate
    \/ (\E a \in Agents : CbNestedRip(a))
    \/ CbNestedField
    \/ (\E a \in Agents : CbNestedTag(a))
    \/ (\E a \in Agents : CbNestedAct(a))
    \/ UnwindOther \/ TopClear
    \/ HealStep \/ HealAct \/ HealDone
    \/ Done

Spec == Init /\ [][Next]_vars

\* P1: an active step runs only after all earlier steps of its run returned
\*   normally, never twice, never twice at once (spec:1636-1639 "starting at
\*   the failed protocol; successful earlier protocols are not replayed. The
\*   cursor advances only when a declared protocol returns normally").
P1_NoReplayInOrder ==
    /\ \A i \in 1..Len(stack) :
        IF stack[i].kind = "cb" THEN
            /\ stack[i].idx \notin ok[stack[i].run]
            /\ \A k \in 0..(stack[i].idx - 1) : k \in ok[stack[i].run]
        ELSE TRUE
    /\ \A i \in 1..Len(stack) : \A j \in 1..Len(stack) :
        IF i # j /\ stack[i].kind = "cb" /\ stack[j].kind = "cb" THEN
            ~(stack[i].run = stack[j].run /\ stack[i].idx = stack[j].idx)
        ELSE TRUE

\* P2: custody ends only when every step returned normally once; nothing is
\*   dropped; no stuck running flag; Heal frees every Agent (spec:1631-1634,
\*   1651-1656 "Completing one run releases only that run; custody ends
\*   after all saved work succeeds").
P2_NoLossAndHeals ==
    /\ \A r \in 1..(nextRun - 1) : InLedger(r) \/ r \in finished
    /\ \A r \in 1..(nextRun - 1) : r \in finished => doneOk[r] = FullSteps
    /\ (NoSavedFrame => \A r \in 1..(nextRun - 1) : ~runs[r].running)
    /\ (phase = "done" => \A a \in Agents : ledger[a] = <<>>)

\* P3: outside the Agent's own cleanup an act either drains everything first
\*   or is refused (spec:1651-1653 "first retries its saved Rip work ... If
\*   it still fails, TagArrestedAccessError"; STEP-SPEC-32 decision 5).
P3_ArrestHolds ==
    \A i \in 1..Len(actLog) :
        actLog[i].outcome = "refused" \/ actLog[i].ownDoor
            \/ actLog[i].emptyAfter

\* P4: a fresh seat survives old cleanup until an explicit Rip targets it
\*   (spec:1658-1660 "keeps its new membership"; STEP-SPEC-32 decision 1).
P4_FreshTaggingSurvives ==
    \A p \in protected : p \in released \/ seat[p[1]] = p[2]

\* P5: field Rip revokes every starting member before any step runs
\*   (spec:1643-1644 "first removes every starting member ... before the
\*   first Rip callback").
P5_FieldRipRevokesFirst ==
    \A i \in 1..Len(stack) :
        IF stack[i].kind = "field" /\ stack[i].pc # "revoke" THEN
            \A s \in stack[i].starts : seat[s[1]] # s[2]
        ELSE TRUE

\* P6: a field Rip stops at the first failure or interruption (spec:1645
\*   "stops on the first failure or interruption"; STEP-SPEC-32 decision 2).
P6_FieldRipStops ==
    \A i \in 1..Len(stack) :
        IF stack[i].kind = "cb" THEN
            IF stack[i].own = 0 THEN TRUE ELSE ~fieldFailed[stack[i].own]
        ELSE TRUE

=============================================================================
