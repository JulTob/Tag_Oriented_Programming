\* ActiveCheckThenAdd: one Agent tagged with the same Tag by two threads.
\*
\* PROMISE: Tagging an Agent with an already-active Tag is a no-op; Imprint /
\*   Post side effects run once and state.active holds no duplicate
\*   (TopKit/CONSTANTS.md:206: "Applying an already active Tag remains a no-op").
\* HARM: User Imprint/Post side effects run twice; state.active keeps a phantom
\*   duplicate entry, which later corrupts Rip accounting (a later `del`
\*   tears down once but leaves a stale active entry, and re-tagging is then a
\*   silent no-op while the contract still lists the Tag).
\*
\* COVERS:
\*   - TopKit/transactions.py:_apply lines 69-150 (active/training check 85-89,
\*     Form target checks 96-97, in-flight training guard 99-105)
\*   - TopKit/transactions.py:_apply_one lines 219-365 (training.add 228,
\*     Imprint 284, _enter_field call 308-314)
\*   - TopKit/transactions.py:_enter_field lines 525-567 (field._Add 539,
\*     active.append 540)
\* CONFIRMED AGAINST COMMIT 1bd5a2548a6bc8fadab9ca4c2451428dbf9b93e4
\*
\* ASSUMPTIONS (two threads, one Agent, one ordinary Tag with a user Pre and
\*   a user Imprint):
\*   - One TLA+ action = one indivisible code step. Check is set reads with no
\*     user code, so one step. Admit collapses training.add (line 228) through
\*     _imprint (line 284) to active.append (line 540) into one step: once
\*     training.add has run, a peer's line-85 check bails, so no NEW admission
\*     can start; the user code after the add (Imprint) cannot enable a peer
\*     Check that already failed. The enabling window, Check to training.add,
\*     contains _gate's user Pre code and stays fully interleaved.
\*   - state.training.add is an unconditional set-add (line 228), not a guard:
\*     it cannot refuse a peer that already passed the line-85 check. The only
\*     guard is the line-85 check (absent entirely when entry_state is None).
\*   - Thread switches happen while user code (Pre/Imprint) blocks; no switch
\*     is assumed inside one action.
\* NOT MODELLED:
\*   - The line 99-105 in-flight-training error ("whose Tagging has not
\*     finished"): a second symptom of the same window, shown on real code by
\*     repro_CA2.py output when the schedule hits it instead of doubleImprint.
\*   - Multi-member Forms and Bases (one Tag already forces the interleaving).
\*
\* INVARIANTS (each one plain sentence):
\*   - CA2_AdmitOnce: user Imprint code ran at most once and state.active
\*     holds the Tag at most once.
\*
\* Break CONSTANT (able to fail; each switch has a _<break>.cfg):
\*   - "none": the current code (check, then admit).
\*   - "noEarlyReturn": a plausible mistake removing the line-85 early-return
\*     active check (and the training guard with it); must still violate
\*     CA2_AdmitOnce (already on sequential schedules).
\*   - "locked": the obvious fix (check+admit under one lock);
\*     must satisfy CA2_AdmitOnce (ActiveCheckThenAdd_fixed.cfg).
\*
\* FINDING CA-2 (outside the documented promise):
\*   1. Thread A checks active/training: Tag absent (transactions.py:85-89).
\*   2. Thread B checks active/training: Tag absent (both inside the window;
\*      user Pre code runs between the check and training.add).
\*   3. Thread A admits: training.add, Imprint runs, active.append.
\*   4. Thread B admits: Imprint runs AGAIN, active.append AGAIN.
\*   End: Imprint ran twice; state.active holds the Tag twice
\*   (on real code: "imprints: 2, active: ['Wizard', 'Wizard']").
\*   Classification: outside the documented promise. Spec Ring 4
\*   (spec/SPECIFICATION.md:1767): "Threads. One Agent, one thread. Fields are
\*   not synchronized." TopKit/IMPLEMENTATION_NOTES.md:676-677: "One Agent,
\*   one thread. The composing counter and Fields are not synchronized."
\*   Real-code reproducer: formal/concurrent_admission/repro_CA2.py.

------------------------- MODULE ActiveCheckThenAdd -------------------------
EXTENDS Integers, TLC

CONSTANTS Break

VARIABLES
    \* code: TopKit/transactions.py:_apply_one line 228 (state.training set)
    training,
    \* mirrors state.active holding the Tag (a count: a duplicate is the finding)
    \* code: TopKit/transactions.py:_enter_field line 540
    activeCount,
    \* history: how many times user Imprint code ran
    \* code: TopKit/transactions.py:_apply_one line 284
    imprints,
    \* scheduling only: per-thread position (check/admit/done)
    pc

vars == <<training, activeCount, imprints, pc>>

Threads == {"t1", "t2"}

Init ==
    /\ training = FALSE
    /\ activeCount = 0
    /\ imprints = 0
    /\ pc = [t \in Threads |-> "check"]

\* code: TopKit/transactions.py:_apply lines 85-89 (early-return no-op when the
\*   Tag is active or training). One step: set reads with no user code.
\*   Break "noEarlyReturn" drops the guard entirely (the sketched mistake).
Check(t) ==
    /\ Break # "locked"
    /\ pc[t] = "check"
    /\ IF Break = "noEarlyReturn"
       THEN pc' = [pc EXCEPT ![t] = "admit"]
       ELSE (IF (training \/ (activeCount > 0))
             THEN pc' = [pc EXCEPT ![t] = "done"]
             ELSE pc' = [pc EXCEPT ![t] = "admit"])
    /\ UNCHANGED <<training, activeCount, imprints>>

\* code: TopKit/transactions.py:_apply_one line 228 (training.add) through line
\*   284 (_imprint runs user code) to _enter_field line 540 (active.append).
\*   One step (see header: after training.add no new admission can start).
Admit(t) ==
    /\ Break # "locked"
    /\ pc[t] = "admit"
    /\ training' = TRUE
    /\ imprints' = imprints + 1
    /\ activeCount' = activeCount + 1
    /\ pc' = [pc EXCEPT ![t] = "done"]

\* The obvious fix: check and admit under one lock (one step: the peer cannot
\*   pass the check after this thread decided to admit).
AtomicAdmit(t) ==
    /\ Break = "locked"
    /\ pc[t] = "check"
    /\ IF (training \/ (activeCount > 0))
       THEN /\ pc' = [pc EXCEPT ![t] = "done"]
            /\ UNCHANGED <<training, activeCount, imprints>>
       ELSE /\ training' = TRUE
            /\ imprints' = imprints + 1
            /\ activeCount' = activeCount + 1
            /\ pc' = [pc EXCEPT ![t] = "done"]

\* Terminal stuttering step (no deadlock: every run ends with both threads done).
Done == (\A t \in Threads: pc[t] = "done") /\ UNCHANGED vars

Next == (\E t \in Threads: Check(t) \/ Admit(t) \/ AtomicAdmit(t)) \/ Done

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ training \in BOOLEAN
    /\ activeCount \in 0..2
    /\ imprints \in 0..2
    /\ pc \in [Threads -> {"check", "admit", "done"}]

\* User Imprint code ran at most once and state.active holds the Tag at most once.
CA2_AdmitOnce == (imprints =< 1) /\ (activeCount =< 1)

=============================================================================
