---------------------------- MODULE DeletionTiers ----------------------------
(***************************************************************************
 * PROMISE (the law under test).
 *   At `del agent` + gc every teardown still due of every still-active Tag
 *   runs, in reverse order of application, and then the Agent's `__del__`
 *   Layers run (top Layer first); `At_Exit` runs every registered live
 *   Agent's due teardowns exactly once; an explicit Rip before deletion
 *   prevents a second run; arrested Agents are held by the Safehouse and
 *   their saved work is never re-run by the finalizer.
 *   (spec/SPECIFICATION.md:1662-1754, tier table :1668-1676, order
 *   :1719-1723; spec:156-159 reverse order; STEP-SPEC-18 rules 4-6;
 *   STEP-SPEC-27.)
 * HARM (if it breaks).
 *   Deletion/exit cleanup silently skipped for unrelated Tags/Agents; or
 *   custody that never ends.
 *
 * COVERS (model action -> code).
 *   TearStep / ExitStep  the teardown loop with its per-teardown outcome
 *                        (TopKit/lifecycle.py _teardown_all, lines 297-322).
 *   ExitNext / ExitDone  the registry walk (TopKit/lifecycle.py
 *                        _run_exit_protocols, lines 412-423).
 *   RunLayers            the finalizer after the teardowns
 *                        (TopKit/access.py _agent_del, lines 595-617).
 *   Init discard of due  at interpreter exit only the Layers run
 *                        (TopKit/access.py _agent_del line 595
 *                        `if not finalizing()`; STEP-SPEC-18 rule 6).
 *   Init choices         ripped = ledger already popped by an explicit Rip
 *                        (lifecycle.py lines 277-278); arrested = Safehouse
 *                        custody (TopKit/arrest.py); reg/dead = weak At_Exit
 *                        registry (lifecycle.py lines 380-409); form =
 *                        Overlay __del__ Layers (state.py line 1558,
 *                        STEP-SPEC-18 rules 1-3).
 * CONFIRMED AGAINST COMMIT 1bd5a2548a6bc8fadab9ca4c2451428dbf9b93e4.
 *
 * ASSUMPTIONS.
 * - One TLA+ action = code between two points where user code can run.
 *   The loop bookkeeping (pop the ledger entry, advance the cursor) with
 *   no user call between is one step with the teardown call itself; a
 *   teardown's outcome (return / raise / interrupted) is the adversary.
 * - Asynchronous interrupts arrive only inside user callbacks
 *   (teardowns, Layers), never inside kit bookkeeping.
 * - Single thread; `del agent` + gc runs the finalizer promptly.
 * - Every acting agent applied tags 1..NTags in increasing order; the
 *   walk is over that fixed application minus pre-ripped tags.
 * - Arrested agents carry an empty due ledger at deletion (revocation
 *   already popped it; remaining work lives in the Safehouse ledger,
 *   which the finalizer never touches).
 * - The At_Exit pass sees no new registrations mid-pass and no deaths
 *   mid-pass (deaths before the pass are `dead`; the while-loop reaching
 *   late registrations is not modelled).
 *
 * NOT MODELLED.
 * - Reference cycles at shutdown (spec:1670 "the language may not run
 *   finalizers ... inside reference cycles"); late-exit module clearing
 *   (STEP-SPEC-18 rule 10); `__del__` Layer bodies raising (reported via
 *   sys.unraisablehook, independent of teardowns); Pin-seat teardown
 *   arguments; multi-teardown ordering inside one Tag (declaration order
 *   is the saved-run engine's, a sibling area); whole-Field Rip;
 *   3-tag-per-agent walks (in real/explore.py instead).
 *
 * INVARIANTS (one line each).
 *   DT1_Complete      : deletion runs every due teardown when no
 *                       interruption hits (Exception never skips the rest).
 *   DT1_Order         : teardowns run in reverse order of application.
 *   DT2_Layers        : the __del__ Layers run as the Overlay shows them,
 *                       even after a failed/interrupted teardown.
 *   DT3_ExitComplete  : the At_Exit pass runs every live registered
 *                       Agent's due teardowns (Exception never skips others).
 *   DT3_Weak          : dead/unregistered Agents' teardowns never run.
 *   DT4_NoReplay      : an explicitly Ripped tag never runs again.
 *   DT4_Custody       : an arrested Agent is not collected and the
 *                       finalizer re-runs none of its saved work.
 *   DT5_ExitOnlyLayers: at interpreter exit only the Layers run.
 *   DT6_Isolated      : an interrupted (Ctrl-C / SystemExit) teardown
 *                       does not skip the remaining due teardowns, at
 *                       deletion or anywhere in the At_Exit pass.
 *
 * FINDING DT-6 (kept; the model of the CURRENT code violates it).
 *   Counterexample in code words: apply Due then Boom (Boom last, so its
 *   teardown runs first); Boom.Leave raises KeyboardInterrupt; `del agent`
 *   + gc runs ['boom'] only -- Due.Leave never runs. Same root in the
 *   exit tier: two At_Exit agents, the first teardown raises
 *   KeyboardInterrupt; `_run_exit_protocols()` raises and the second
 *   Agent's due teardown never runs.
 *   Classification: (a) violates a spec promise. "Deletion runs in that
 *   order: every teardown still due runs" (spec:1719-1720, unconditional),
 *   and teardowns at deletion/exit "run in reverse order of application"
 *   (spec:158-159). "Best effort" (spec:1670 tier table, STEP-SPEC-18
 *   rule 4) qualifies the tier -- the finalizer may never run at shutdown
 *   or inside reference cycles -- not a licence to abandon a walk that
 *   already started: `_teardown_all` already isolates `Exception`
 *   per teardown (lifecycle.py:319-320), and `_agent_del` deliberately
 *   keeps the Layers running after an interruption (access.py:600-601),
 *   so the missing BaseException isolation in the loop is an omission.
 *   Reproducers: repro_DT6_del.py, repro_DT6_exit.py.
 *   The `fixed` variant (Break = "fixed") passes, so the invariant is
 *   satisfiable.
 *
 * BREAK SWITCHES (CONSTANT Break; each has a _<break>.cfg that must fail).
 *   ""               current code (ki/se abandon the walk / the pass).
 *   "fixed"          ki/se are isolated like Exception (the obvious fix).
 *   "exc_abort"      Exception aborts the deletion walk (violates DT1).
 *   "order"          walk runs in application order (violates DT1_Order).
 *   "skip_layers"    Layers skipped after failure (violates DT2_Layers).
 *   "exit_abort_exc" Exception aborts the whole At_Exit pass (violates DT3).
 *   "strong"         dead Agents are still walked (violates DT3_Weak).
 *   "replay"         explicitly Ripped tags stay due (violates DT4).
 *   "recoll"         arrested Agents are collected (violates DT4_Custody).
 *   "exit_tear"      the exit finalizer also runs teardowns (violates DT5).
 *   Every non-"" switch keeps the interruption fix, so each variant
 *   violates exactly its own invariant (no cross-talk with DT6).
 ***************************************************************************)

EXTENDS Naturals, Sequences

CONSTANTS NAgents, NTags, Break

ASSUME NAgents \in 1..3 /\ NTags \in 1..3
ASSUME Break \in {"", "fixed", "exc_abort", "order", "skip_layers",
                  "exit_abort_exc", "strong", "replay", "recoll", "exit_tear"}

Outcomes == {"ok", "exc", "ki", "se"}

\* code: TopKit/lifecycle.py _teardown_all lines 310-311 (walk order)
TagsSeq == [i \in 1..NTags |-> i]
RevSeq == [i \in 1..NTags |-> NTags + 1 - i]

\* mirrors state.rips[state.active reversed] in TopKit/lifecycle.py;
\* rip_ is passed explicitly (a defined operator may not read variables)
DueFor(rip_, brk, a) == IF brk = "replay"
             THEN RevSeq
             ELSE IF brk = "order"
             THEN SelectSeq(TagsSeq, LAMBDA t : t \notin rip_[a])
             ELSE SelectSeq(RevSeq, LAMBDA t : t \notin rip_[a])

AbandonX == [a \in 1..NAgents |-> <<>>]

\* mirrors STEP-SPEC-18 rules 1-3 (host first Layer, replacer, Delete)
ExpectedLayers(f) == IF f = "host" THEN <<"host">>
                     ELSE IF f = "chain" THEN <<"LU2", "LU1", "host">>
                     ELSE IF f = "replace" THEN <<"LR">>
                     ELSE <<>>

\* code: TopKit/lifecycle.py _teardown_all lines 297-322; _run_exit_protocols 412-423
\* mirrors: tier (which protocol), phase, d (agent under deletion),
\*   due (remaining ledger entries, reversed), dueX (per-agent pass stacks),
\*   idx (pass cursor), ripped (ledger already popped by explicit Rip),
\*   arrested (Safehouse custody), form (Overlay __del__ shape),
\*   reg/dead (weak At_Exit registry)
VARIABLES tier, phase, d, due, dueX, idx, ripped, arrested, form, reg, dead,
\* history: ranTears (teardowns that ran, in order), layersRan, failed,
\*   interrupted (ki/se seen), collected (gc could take the Agent)
          ranTears, layersRan, failed, interrupted, collected

vars == <<tier, phase, d, due, dueX, idx, ripped, arrested, form, reg, dead,
          ranTears, layersRan, failed, interrupted, collected>>

RanSet == { ranTears[i] : i \in 1..Len(ranTears) }

Owed(a) == IF tier = "exit"
           THEN (IF a \in reg /\ a \notin dead
                 THEN (1..NTags) \ ripped[a] ELSE {})
           ELSE (IF a = d /\ ~arrested /\ (tier = "del" \/ Break = "exit_tear")
                 THEN (1..NTags) \ ripped[a] ELSE {})

Init ==
  \E tier_ \in {"del", "exit", "exitdel"} :
  \E d_ \in 1..NAgents :
  \E pick \in ({0} \cup (1..NTags)) :
  \E miss \in ({0} \cup (1..NAgents)) :
  \E dd \in ({0} \cup (1..NAgents)) :
  \E arr \in BOOLEAN :
  \E form_ \in {"host", "chain", "replace", "delete"} :
    LET rip_ == [a \in 1..NAgents |-> IF pick = 0 THEN {} ELSE {pick}] IN
    LET reg_ == IF tier_ = "exit"
                THEN (IF miss = 0 THEN 1..NAgents ELSE (1..NAgents) \ {miss})
                ELSE {} IN
    LET dead_ == IF tier_ = "exit" /\ dd /= 0 THEN ({dd} \cap reg_) ELSE {} IN
    /\ tier = tier_
    /\ phase = "walk"
    /\ d = d_
    /\ (tier_ = "exit" => d_ = 1)
    /\ ripped = rip_
    /\ reg = reg_
    /\ dead = dead_
    /\ arrested = arr
    /\ (tier_ = "exit" => ~arr)
    /\ form = form_
    /\ (tier_ = "exit" => form_ = "host")
    (* code: lifecycle.py 277-278: an explicit Rip pops the ledger *)
    (* code: access.py 595: at interpreter exit teardowns are At_Exit's *)
    /\ due = IF tier_ = "exit" THEN <<>>
             ELSE IF tier_ = "exitdel" /\ Break /= "exit_tear" THEN <<>>
             ELSE IF arr THEN <<>>
             ELSE DueFor(rip_, Break, d_)
    /\ dueX = IF tier_ = "exit"
              THEN [a \in 1..NAgents |->
                      IF a \in reg_ /\ (a \notin dead_ \/ Break = "strong")
                      THEN DueFor(rip_, Break, a) ELSE <<>>]
              ELSE [a \in 1..NAgents |-> <<>>]
    /\ idx = 1
    /\ ranTears = <<>>
    /\ layersRan = <<>>
    /\ failed = FALSE
    /\ interrupted = FALSE
    /\ collected = FALSE

(* code: TopKit/lifecycle.py _teardown_all lines 310-320.
   One step = one teardown call with its outcome; loop bookkeeping carries
   no user code, so pop-and-call is indivisible. The adversary picks the
   outcome where user code runs. *)
TearStep ==
  /\ (tier = "del" \/ Break = "exit_tear")
  /\ phase = "walk"
  /\ due /= <<>>
  /\ \E out \in Outcomes :
       LET t == Head(due) IN
       LET fail_ == failed \/ (out = "exc") IN
       LET intr_ == interrupted \/ (out \in {"ki", "se"}) IN
       /\ ranTears' = Append(ranTears, <<d, t>>)
       /\ interrupted' = intr_
       /\ failed' = fail_
       (* code: lifecycle.py 319-320 catches Exception only; ki/se escape.
          Break "" abandons the rest (the finding); any other Break
          isolates like Exception. exc_abort re-introduces abort-on-Error. *)
       /\ due' = IF out = "ok" THEN Tail(due)
                 ELSE IF out = "exc"
                 THEN (IF Break = "exc_abort" THEN <<>> ELSE Tail(due))
                 ELSE (IF Break = "" THEN <<>> ELSE Tail(due))
       /\ UNCHANGED <<tier, phase, d, dueX, idx, ripped, arrested, form,
                      reg, dead, layersRan, collected>>
(* code: TopKit/lifecycle.py _run_exit_protocols lines 415-423 calling
   _teardown_all per registered Agent with no per-Agent guard. *)
ExitStep ==
  /\ tier = "exit"
  /\ phase = "walk"
  /\ idx \in 1..NAgents
  /\ dueX[idx] /= <<>>
  /\ \E out \in Outcomes :
       LET t == Head(dueX[idx]) IN
       LET fail_ == failed \/ (out = "exc") IN
       LET intr_ == interrupted \/ (out \in {"ki", "se"}) IN
       /\ ranTears' = Append(ranTears, <<idx, t>>)
       /\ interrupted' = intr_
       /\ failed' = fail_
       (* ki/se abandon the whole pass on current code (the finding);
          exit_abort_exc re-introduces abort-on-Error for the pass. *)
       /\ dueX' = IF out = "ok" THEN [dueX EXCEPT ![idx] = Tail(dueX[idx])]
                  ELSE IF out = "exc"
                  THEN (IF Break = "exit_abort_exc" THEN AbandonX
                        ELSE [dueX EXCEPT ![idx] = Tail(dueX[idx])])
                  ELSE (IF Break = "" THEN AbandonX
                        ELSE [dueX EXCEPT ![idx] = Tail(dueX[idx])])
       /\ UNCHANGED <<tier, phase, d, due, idx, ripped, arrested, form,
                      reg, dead, layersRan, collected>>
(* code: TopKit/lifecycle.py _run_exit_protocols line 415: registration order *)
ExitNext ==
  /\ tier = "exit"
  /\ phase = "walk"
  /\ idx \in 1..NAgents
  /\ dueX[idx] = <<>>
  /\ idx' = idx + 1
  /\ UNCHANGED <<tier, phase, d, due, dueX, ripped, arrested, form,
                 reg, dead, ranTears, layersRan, failed, interrupted,
                 collected>>

ExitDone ==
  /\ tier = "exit"
  /\ phase = "walk"
  /\ idx = NAgents + 1
  /\ phase' = "done"
  /\ UNCHANGED <<tier, d, due, dueX, idx, ripped, arrested, form,
                 reg, dead, ranTears, layersRan, failed, interrupted,
                 collected>>

(* code: TopKit/access.py _agent_del lines 595-617. The Layers after the
   teardowns; access.py 600-601 keeps them running after an interruption.
   skip_layers re-introduces skipping them on failure. recoll re-introduces
   collecting an arrested Agent. Layer bodies are user code but their
   effects are out of scope, so running them is one step. *)
RunLayers ==
  /\ tier \in {"del", "exitdel"}
  /\ phase = "walk"
  /\ due = <<>>
  /\ layersRan' = IF Break = "skip_layers" /\ (failed \/ interrupted)
                 THEN <<>> ELSE ExpectedLayers(form)
  /\ phase' = "done"
  /\ collected' = IF Break = "recoll" THEN TRUE ELSE ~arrested
  /\ UNCHANGED <<tier, d, due, dueX, idx, ripped, arrested, form,
                 reg, dead, ranTears, failed, interrupted>>

Finished ==
  /\ phase = "done"
  /\ UNCHANGED vars

Next == TearStep \/ ExitStep \/ ExitNext \/ ExitDone \/ RunLayers \/ Finished

Spec == Init /\ [][Next]_vars

(* Every due teardown runs when nothing interrupts (Exception is isolated). *)
DT1_Complete ==
  (phase = "done" /\ tier = "del" /\ ~arrested /\ ~interrupted)
  => (\A t \in ((1..NTags) \ ripped[d]) : <<d, t>> \in RanSet)

(* Reverse order of application, per Agent, in every tier. *)
DT1_Order ==
  \A i, j \in 1..Len(ranTears) :
    ((i < j /\ ranTears[i][1] = ranTears[j][1])
     => ranTears[i][2] > ranTears[j][2])

(* The Layers run as the Overlay shows them, whatever the teardowns did. *)
DT2_Layers ==
  (phase = "done" /\ tier \in {"del", "exitdel"})
  => (layersRan = ExpectedLayers(form))

(* The pass runs every live registered Agent's due teardowns. *)
DT3_ExitComplete ==
  (phase = "done" /\ tier = "exit" /\ ~interrupted)
  => (\A a \in reg : (a \notin dead
       => (\A t \in ((1..NTags) \ ripped[a]) : <<a, t>> \in RanSet)))

(* Dead or never-registered Agents stay untouched by the pass. *)
DT3_Weak ==
  (tier = "exit")
  => (\A i \in 1..Len(ranTears) :
        (ranTears[i][1] \in reg /\ ranTears[i][1] \notin dead))

(* An explicitly Ripped tag never runs again. *)
DT4_NoReplay ==
  \A i \in 1..Len(ranTears) : ranTears[i][2] \notin ripped[ranTears[i][1]]

(* An arrested Agent is held; the finalizer re-runs nothing. *)
DT4_Custody ==
  (phase = "done" /\ tier \in {"del", "exitdel"} /\ arrested)
  => (ranTears = <<>> /\ ~collected)

(* At interpreter exit only the Layers run. *)
DT5_ExitOnlyLayers ==
  (phase = "done" /\ tier = "exitdel")
  => (ranTears = <<>> /\ layersRan = ExpectedLayers(form))

(* An interrupted teardown skips nothing due, in either tier. *)
DT6_Isolated ==
  (phase = "done" /\ interrupted)
  => (\A a \in 1..NAgents : (\A t \in Owed(a) : <<a, t>> \in RanSet))

=============================================================================
