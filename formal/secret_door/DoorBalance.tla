---- MODULE DoorBalance ----
(***************************************************************************)
(* PROMISE: Composition is the door. Inside it -- while an Action, Imprint,*)
(* Record builder, condition, or Rip protocol bound to THIS Agent is       *)
(* running -- everything of the relevant scopes resolves; outside it only *)
(* external members do. A secret handle captured inside and called outside*)
(* fails closed (spec/SPECIFICATION.md:780-784,809).                       *)
(* HARM: a leaked door leaves an Agent's @Secret members readable from     *)
(* outside forever (this exact bug happened before; CHANGELOG.md:431-434); *)
(* a wrongly closed door denies an Agent its own Secrets with the          *)
(* misleading host-miss error.                                             *)
(*                                                                         *)
(* COVERS (model of the CURRENT code):                                     *)
(*   TopKit/state.py:1041-1064 _Composing_Bound.__call__ (sync door)       *)
(*   TopKit/state.py:1086-1104 _Secret_Bound.__call__ (secret gate)        *)
(*   TopKit/state.py:203-220 _is_composing (counter OR own async door)     *)
(*   TopKit/state.py:175-194 _Async_Door (execution-local async door)      *)
(*   TopKit/state.py:1398-1443 _context_action Async_Context/Context       *)
(*   TopKit/state.py:1445-1452 _guard_dunder (dunder bodies: NO door)      *)
(*   TopKit/state.py:1002-1026 _Secret_Pinned_Operation.Secret (pin gate)  *)
(*   TopKit/arrest.py:81-100 _rip_door (rip door for exit cleanup)         *)
(*   TopKit/transactions.py:219-229,360-365 _apply_one (refused rollback)  *)
(*   TopKit/lifecycle.py:228-240 _run_one; 300-322 _revoke/_call_teardown  *)
(*   TopKit/lazy_guard.py:400-436 _guard_lazy_result (wraps, no door)      *)
(*   TopKit/access.py:651-663 _View_Call._authorize (custody check)        *)
(* CONFIRMED AGAINST COMMIT 1bd5a2548a6bc8fadab9ca4c2451428dbf9b93e4       *)
(*                                                                         *)
(* ASSUMPTIONS (single thread unless the cfg enables two):                 *)
(* - One TLA+ action = code between two points where user code can run.    *)
(*   composing += 1 is fused with pushing the frame: no user code runs     *)
(*   between them (straight-line interpreter steps, GIL-atomic enough that *)
(*   no callback, await, yield or thread switch can land between).         *)
(* - Interrupts (raise/KeyboardInterrupt/cancel) arrive only inside user   *)
(*   callbacks, i.e. as the outcome of an Exit action, never mid-guard.    *)
(* - Async-hook visibility follows the code, not the spec (the spec is     *)
(*   silent on hooks): a deliberately derived context shares the door      *)
(*   while active; a pre-existing sibling does not; closing clears every   *)
(*   view (TopKit/IMPLEMENTATION_NOTES.md:82-93). The spec rule SpecOpen   *)
(*   agrees with the code everywhere EXCEPT lazy/dunder bodies (SD-3) and  *)
(*   cross-thread reads (SD-4).                                            *)
(* - Sibling asyncio tasks of one thread are not separate executions here: *)
(*   they share the sync counter but not async doors, exactly like nested  *)
(*   sync frames in this model; the matrix stays in real/ probes.          *)
(* - Out-of-order hook close and close-from-another-context are modelled   *)
(*   by removing any matching frame, not just the head of the stack.       *)
(* - halt is history: once a break-induced leak or a mismatch is recorded, *)
(*   only Done stutters, so each cfg reports exactly one finding.          *)
(* NOT MODELLED: which member resolves (only reachability true/false);     *)
(* denial message texts; Pin receiver/authority inheritance (#98); which   *)
(* Tagging is refused and why; GC/weakref lifetimes; multi-step teardown   *)
(* order (a Rip/Teardown scope is one enter/exit pair).                     *)
(*                                                                         *)
(* FINDING SD-3 (spec promise): async/generator/async-gen Action bodies    *)
(* and non-context dunder bodies that read their own Agent's Secret are    *)
(* DENIED on the current code, although "Inside composition means: while   *)
(* an Action ... bound to this Agent is running" (SPECIFICATION.md:782-    *)
(* 784). Counterexample in code words: 1. call sync Action aro (door opens,*)
(* returns coroutine, door closes); 2. await the coroutine (body runs,     *)
(* reads agent.code); 3. AttributeError "Host has no member 'code'". The   *)
(* sync door wraps only coroutine CREATION (_Composing_Bound.__call__);    *)
(* _guard_lazy_result opens no door; _guard_dunder opens no door. The doc  *)
(* calls lazy execution a separate concern (#94, IMPLEMENTATION_NOTES.md:  *)
(* 101-102,148-149), but the spec sentence has no such exclusion, so this  *)
(* stays a finding. Reproducer: formal/secret_door/repro_SD3.py. The       *)
(* DoorBalance_fixed.cfg variant (Break="fix-lazy": resume/dunder re-opens *)
(* the door) passes SD-3, so the invariant is satisfiable.                 *)
(* FINDING SD-4 (outside the documented promise): while one thread runs    *)
(* inside hold(), another thread reads the same Agent's Secret and is      *)
(* ALLOWED: the composing counter lives on the shared _State with no lock. *)
(* Documented out of promise: "One Agent, one thread. The composing        *)
(* counter and Fields are not synchronized" (IMPLEMENTATION_NOTES.md:676-  *)
(* 677). Kept as a failing invariant; reproducer:                          *)
(* formal/secret_door/repro_SD4.py.                                        *)
(***************************************************************************)
EXTENDS Integers, Sequences, FiniteSets, TLC

CONSTANTS MaxOps, MaxDepth, MaxReads, Threads, LazyOn, DunderOn, Break

Agents == {"X", "Y"}
Cap == 2 * MaxDepth
DoorKinds == {"sync", "apply", "rip", "teardown", "shook", "ahook"}

VARIABLES
    \* mirrors state.composing in TopKit/state.py (_State.composing)
    composing,
    \* mirrors live _Async_Door count per Agent (TopKit/state.py _async_doors)
    asyncLive,
    \* mirrors per-execution visibility of those doors (ContextVar semantics)
    asyncView,
    \* mirrors live _Rip_Door count per Agent (TopKit/arrest.py _rip_doors)
    ripLive,
    \* mirrors the interpreter call stack (whose door each execution is in)
    stack,
    \* history: pending lazy body per execution (gen/coro/agen of an Agent)
    lazy,
    \* history: captured secret handles per execution (spec §1.5:809)
    cap,
    \* history: ordinary/captured/view/pin reads: [t, s, spec, code, other]
    reads,
    \* history: own-secret reads from lazy/dunder bodies: [t, s, code]
    lazyReads,
    \* history: probe reads through another execution's open door: [t, s, code]
    xreads,
    ops,
    \* history: stop after the first recorded leak/mismatch (one finding/cfg)
    halt

vars == <<composing, asyncLive, asyncView, ripLive, stack, lazy, cap,
          reads, lazyReads, xreads, ops, halt>>

AgentsIn(t) ==
    {stack[t][i].agent : i \in {j \in 1..Len(stack[t]) : stack[t][j].kind \in DoorKinds}}

MyTail(s) == [i \in 1..(Len(s) - 1) |-> s[i + 1]]

RemoveAt(s, i) == [j \in 1..(Len(s) - 1) |-> IF j < i THEN s[j] ELSE s[j + 1]]

IncView(t, A) == [p \in Threads \times Agents |-> IF p = <<t, A>> THEN asyncView[p] + 1 ELSE asyncView[p]]
DecView(t, A) == [p \in Threads \times Agents |-> IF p = <<t, A>> THEN (IF asyncView[p] > 0 THEN asyncView[p] - 1 ELSE 0) ELSE asyncView[p]]
\* nested same-agent hooks each contribute one, so inner exit leaves
\* the outer door visible (code: any() over the ContextVar tuple).
CodeAllows(t, S) == composing[S] > 0 \/ asyncView[<<t, S>>] > 0

\* spec: SPECIFICATION.md:782-784 (own door open in THIS execution)
SpecOpen(t, S) == S \in AgentsIn(t) \/ asyncView[<<t, S>>] > 0

OtherHolds(t, S) == \E u \in Threads \ {t} : S \in AgentsIn(u)

\* Break="door-shared": the gate ignores whose door is open
SharedCodeAllows(t) ==
    (\E B \in Agents : composing[B] > 0) \/ (\E B \in Agents : asyncView[<<t, B>>] > 0)

CanAct == \lnot halt /\ ops < MaxOps

Init ==
    /\ composing = [A \in Agents |-> 0]
    /\ asyncLive = [A \in Agents |-> 0]
    /\ asyncView = [p \in Threads \times Agents |-> 0]
    /\ ripLive = [A \in Agents |-> 0]
    /\ stack = [t \in Threads |-> <<>>]
    /\ lazy = [t \in Threads |-> "-"]
    /\ cap = [t \in Threads |-> {}]
    /\ reads = <<>>
    /\ lazyReads = <<>>
    /\ xreads = <<>>
    /\ ops = 0
    /\ halt = FALSE

\* code: TopKit/state.py:_Composing_Bound.__call__ lines 1053-1056
\* (increment before the body; fused: no user code between)
EnterSync(t, A) ==
    /\ CanAct /\ Len(stack[t]) < MaxDepth /\ composing[A] < Cap
    /\ composing' = [composing EXCEPT ![A] = composing[A] + 1]
    \* the stack pushes/pops at the head (LIFO): Head is the newest frame
    /\ stack' = [stack EXCEPT ![t] = <<[agent |-> A, kind |-> "sync"]>> \o stack[t]]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: TopKit/state.py:_Composing_Bound.__call__ lines 1063-1064 (finally)
ExitSyncOk(t) ==
    /\ CanAct /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "sync"
    /\ LET A == Head(stack[t]).agent IN
        /\ stack' = [stack EXCEPT ![t] = MyTail(stack[t])]
        /\ composing' = [composing EXCEPT ![A] = composing[A] - 1]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: same finally; Break="no-finally" drops the decrement on raise
ExitSyncRaise(t) ==
    /\ CanAct /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "sync"
    /\ LET A == Head(stack[t]).agent IN
        /\ stack' = [stack EXCEPT ![t] = MyTail(stack[t])]
        /\ IF Break = "no-finally"
           THEN /\ composing' = composing /\ halt' = TRUE
           ELSE /\ composing' = [composing EXCEPT ![A] = composing[A] - 1]
                /\ UNCHANGED halt
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, ripLive, lazy, cap, reads, lazyReads, xreads>>

\* code: TopKit/transactions.py:_apply_one line 229 (nested tagging door)
ApplyEnter(t, A) ==
    /\ CanAct /\ Len(stack[t]) < MaxDepth /\ composing[A] < Cap
    /\ composing' = [composing EXCEPT ![A] = composing[A] + 1]
    /\ stack' = [stack EXCEPT ![t] = <<[agent |-> A, kind |-> "apply"]>> \o stack[t]]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: TopKit/transactions.py:_apply_one lines 364-365 (balanced exit)
ApplyExitOk(t) ==
    /\ CanAct /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "apply"
    /\ LET A == Head(stack[t]).agent IN
        /\ stack' = [stack EXCEPT ![t] = MyTail(stack[t])]
        /\ composing' = [composing EXCEPT ![A] = composing[A] - 1]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: same; refused Pre/Gate, Imprint/builder failure unwind through here.
\* Break="rollback-open" is the CHANGELOG.md:431-434 bug (rollback left it open).
ApplyExitRefused(t) ==
    /\ CanAct /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "apply"
    /\ LET A == Head(stack[t]).agent IN
        /\ stack' = [stack EXCEPT ![t] = MyTail(stack[t])]
        /\ IF Break = "rollback-open"
           THEN /\ composing' = composing /\ halt' = TRUE
           ELSE /\ composing' = [composing EXCEPT ![A] = composing[A] - 1]
                /\ UNCHANGED halt
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, ripLive, lazy, cap, reads, lazyReads, xreads>>

\* code: TopKit/lifecycle.py:_run_one lines 228-240 (rip step door)
RipEnter(t, A) ==
    /\ CanAct /\ Len(stack[t]) < MaxDepth /\ composing[A] < Cap /\ ripLive[A] < 2
    /\ composing' = [composing EXCEPT ![A] = composing[A] + 1]
    /\ ripLive' = [ripLive EXCEPT ![A] = ripLive[A] + 1]
    /\ stack' = [stack EXCEPT ![t] = <<[agent |-> A, kind |-> "rip"]>> \o stack[t]]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: TopKit/lifecycle.py:_run_one lines 239-240
RipExitOk(t) ==
    /\ CanAct /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "rip"
    /\ LET A == Head(stack[t]).agent IN
        /\ stack' = [stack EXCEPT ![t] = MyTail(stack[t])]
        /\ composing' = [composing EXCEPT ![A] = composing[A] - 1]
        /\ ripLive' = [ripLive EXCEPT ![A] = ripLive[A] - 1]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: same; the rip door itself always closes (arrest.py finally)
RipExitRaise(t) ==
    /\ CanAct /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "rip"
    /\ LET A == Head(stack[t]).agent IN
        /\ stack' = [stack EXCEPT ![t] = MyTail(stack[t])]
        /\ ripLive' = [ripLive EXCEPT ![A] = ripLive[A] - 1]
        /\ IF Break = "no-finally"
           THEN /\ composing' = composing /\ halt' = TRUE
           ELSE /\ composing' = [composing EXCEPT ![A] = composing[A] - 1]
                /\ UNCHANGED halt
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, lazy, cap, reads, lazyReads, xreads>>

\* code: TopKit/lifecycle.py:_revoke/_call_teardown lines 306-322
TeardownEnter(t, A) ==
    /\ CanAct /\ Len(stack[t]) < MaxDepth /\ composing[A] < Cap /\ ripLive[A] < 2
    /\ composing' = [composing EXCEPT ![A] = composing[A] + 1]
    /\ ripLive' = [ripLive EXCEPT ![A] = ripLive[A] + 1]
    /\ stack' = [stack EXCEPT ![t] = <<[agent |-> A, kind |-> "teardown"]>> \o stack[t]]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: TopKit/lifecycle.py lines 321-322
TeardownExitOk(t) ==
    /\ CanAct /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "teardown"
    /\ LET A == Head(stack[t]).agent IN
        /\ stack' = [stack EXCEPT ![t] = MyTail(stack[t])]
        /\ composing' = [composing EXCEPT ![A] = composing[A] - 1]
        /\ ripLive' = [ripLive EXCEPT ![A] = ripLive[A] - 1]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: same; teardown errors stay best effort but must not leak the door
TeardownExitRaise(t) ==
    /\ CanAct /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "teardown"
    /\ LET A == Head(stack[t]).agent IN
        /\ stack' = [stack EXCEPT ![t] = MyTail(stack[t])]
        /\ ripLive' = [ripLive EXCEPT ![A] = ripLive[A] - 1]
        /\ IF Break = "no-finally"
           THEN /\ composing' = composing /\ halt' = TRUE
           ELSE /\ composing' = [composing EXCEPT ![A] = composing[A] - 1]
                /\ UNCHANGED halt
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, lazy, cap, reads, lazyReads, xreads>>

\* code: TopKit/state.py:_context_action/Context lines 1430-1431
SyncHookEnter(t, A) ==
    /\ CanAct /\ Len(stack[t]) < MaxDepth /\ composing[A] < Cap
    /\ composing' = [composing EXCEPT ![A] = composing[A] + 1]
    /\ stack' = [stack EXCEPT ![t] = <<[agent |-> A, kind |-> "shook"]>> \o stack[t]]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: IMPLEMENTATION_NOTES.md:81-82 (entry closes its door before the block)
SyncHookBodyEnd(t) ==
    /\ CanAct /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "shook"
    /\ LET A == Head(stack[t]).agent IN
        /\ stack' = [stack EXCEPT ![t] =
            <<[agent |-> A, kind |-> "block"]>> \o MyTail(stack[t])]
        /\ composing' = [composing EXCEPT ![A] = composing[A] - 1]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: state.py lines 1426-1441 (__exit__ body runs under the door again)
SyncHookBlockEnd(t) ==
    /\ CanAct /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "block"
    /\ LET A == Head(stack[t]).agent IN
        /\ stack' = [stack EXCEPT ![t] =
            <<[agent |-> A, kind |-> "shook"]>> \o MyTail(stack[t])]
        /\ composing' = [composing EXCEPT ![A] = composing[A] + 1]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: state.py lines 1440-1441 (any matching frame: out-of-order close)
SyncHookExitOk(t, A) ==
    /\ CanAct /\ \E i \in 1..Len(stack[t]) :
        /\ stack[t][i].agent = A /\ stack[t][i].kind = "shook"
        /\ stack' = [stack EXCEPT ![t] = RemoveAt(stack[t], i)]
        /\ composing' = [composing EXCEPT ![A] = composing[A] - 1]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: same finally on raise
SyncHookExitRaise(t, A) ==
    /\ CanAct /\ \E i \in 1..Len(stack[t]) :
        /\ stack[t][i].agent = A /\ stack[t][i].kind = "shook"
        /\ stack' = [stack EXCEPT ![t] = RemoveAt(stack[t], i)]
        /\ IF Break = "no-finally"
           THEN /\ composing' = composing /\ halt' = TRUE
           ELSE /\ composing' = [composing EXCEPT ![A] = composing[A] - 1]
                /\ UNCHANGED halt
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, ripLive, lazy, cap, reads, lazyReads, xreads>>

\* code: TopKit/state.py:_context_action/Async_Context lines 1409-1410
AsyncHookEnter(t, A) ==
    /\ CanAct /\ Len(stack[t]) < MaxDepth /\ asyncLive[A] < 2
    /\ asyncLive' = [asyncLive EXCEPT ![A] = asyncLive[A] + 1]
    /\ asyncView' = IncView(t, A)
    /\ stack' = [stack EXCEPT ![t] = <<[agent |-> A, kind |-> "ahook"]>> \o stack[t]]
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: door closes before the async with-block (probe: in-block reads denied)
AsyncHookBodyEnd(t) ==
    /\ CanAct /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "ahook"
    /\ LET A == Head(stack[t]).agent IN
        /\ stack' = [stack EXCEPT ![t] =
            <<[agent |-> A, kind |-> "block"]>> \o MyTail(stack[t])]
        /\ asyncLive' = [asyncLive EXCEPT ![A] = asyncLive[A] - 1]
        /\ asyncView' = DecView(t, A)
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: __aexit__ body re-opens (tests read agent.key inside it)
AsyncHookBlockEnd(t) ==
    /\ CanAct /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "block"
    /\ LET A == Head(stack[t]).agent IN
        /\ stack' = [stack EXCEPT ![t] =
            <<[agent |-> A, kind |-> "ahook"]>> \o MyTail(stack[t])]
        /\ asyncLive' = [asyncLive EXCEPT ![A] = asyncLive[A] + 1]
        /\ asyncView' = IncView(t, A)
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: state.py lines 1418-1420 (finally: Close + prune; any frame: cross-context)
AsyncHookExitOk(t, A) ==
    /\ CanAct /\ \E i \in 1..Len(stack[t]) :
        /\ stack[t][i].agent = A /\ stack[t][i].kind = "ahook"
        /\ stack' = [stack EXCEPT ![t] = RemoveAt(stack[t], i)]
        /\ asyncLive' = [asyncLive EXCEPT ![A] = asyncLive[A] - 1]
        /\ asyncView' = DecView(t, A)
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: same finally on raise (errors still close the hook's door)
AsyncHookExitRaise(t, A) ==
    /\ CanAct /\ \E i \in 1..Len(stack[t]) :
        /\ stack[t][i].agent = A /\ stack[t][i].kind = "ahook"
        /\ stack' = [stack EXCEPT ![t] = RemoveAt(stack[t], i)]
        /\ asyncLive' = [asyncLive EXCEPT ![A] = asyncLive[A] - 1]
        /\ asyncView' = DecView(t, A)
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, ripLive, lazy, cap, reads, lazyReads, xreads, halt>>

\* code: same finally on cancel; Break="async-survives" keeps the door
AsyncHookExitCancel(t, A) ==
    /\ CanAct /\ \E c \in Threads, i \in 1..Len(stack[t]) :
        /\ stack[t][i].agent = A /\ stack[t][i].kind = "ahook"
        /\ stack' = [stack EXCEPT ![t] = RemoveAt(stack[t], i)]
        /\ IF Break = "async-survives"
           THEN /\ UNCHANGED <<asyncLive, asyncView>> /\ halt' = TRUE
           ELSE /\ asyncLive' = [asyncLive EXCEPT ![A] = asyncLive[A] - 1]
                /\ asyncView' = DecView(t, A)
                /\ UNCHANGED halt
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, ripLive, lazy, cap, reads, lazyReads, xreads>>

\* code: state.py lines 1056-1064 (sync call returns the lazy object, door closes)
\* + lazy_guard.py:_guard_lazy_result lines 400-436 (wraps, opens no door)
StartLazy(t, A, k) ==
    /\ CanAct /\ LazyOn /\ lazy[t] = "-"
    /\ stack[t] /= <<>> /\ Head(stack[t]).kind = "sync" /\ Head(stack[t]).agent = A
    /\ stack' = [stack EXCEPT ![t] = MyTail(stack[t])]
    /\ composing' = [composing EXCEPT ![A] = composing[A] - 1]
    /\ lazy' = [lazy EXCEPT ![t] = <<A, k>>]
    /\ ops' = ops + 1
    /\ UNCHANGED <<asyncLive, asyncView, ripLive, cap, reads, lazyReads, xreads, halt>>

\* The lazy body runs with NO sync door (finding SD-3), but sees an open
\* async-hook door of the awaiting execution (probe: nested-gen ALLOWED).
\* Break="fix-lazy" re-opens the own door around the resume.
ResumeLazy(t) ==
    /\ CanAct /\ lazy[t] /= "-"
    /\ LET A == lazy[t][1] IN
        /\ Len(lazyReads) < MaxReads
        /\ LET code == (Break = "fix-lazy") \/ asyncView[<<t, A>>] > 0 \/ composing[A] > 0 IN
            /\ lazyReads' = Append(lazyReads, [t |-> t, s |-> A, code |-> code])
            /\ halt' = \lnot code
        /\ lazy' = [lazy EXCEPT ![t] = "-"]
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, asyncLive, asyncView, ripLive, stack, cap, reads, xreads>>

\* code truth: closing a generator / cancelling a coroutine holds no door
AbandonLazy(t) ==
    /\ CanAct /\ lazy[t] /= "-"
    /\ lazy' = [lazy EXCEPT ![t] = "-"]
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, asyncLive, asyncView, ripLive, stack, cap, reads, lazyReads, xreads, halt>>

\* code: state.py:_guard_dunder lines 1445-1452 (no composing increment).
\* spec: a dunder Action IS an Action bound to this Agent (finding SD-3).
DunderCall(t, S) ==
    /\ CanAct /\ DunderOn /\ Len(lazyReads) < MaxReads
    /\ LET code == (Break = "fix-lazy") IN
        /\ lazyReads' = Append(lazyReads, [t |-> t, s |-> S, code |-> code])
        /\ halt' = \lnot code
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, asyncLive, asyncView, ripLive, stack, lazy, cap, reads, xreads>>

\* code: access.py:_agent_getattr + state.py:1098 (_Secret_Bound gate)
ReadSecret(t, S) ==
    /\ CanAct /\ Len(reads) < MaxReads
    /\ LET spec == SpecOpen(t, S)
          code == IF Break = "door-shared" THEN SharedCodeAllows(t) ELSE CodeAllows(t, S)
          oth == OtherHolds(t, S) IN
        /\ reads' = Append(reads, [t |-> t, s |-> S, spec |-> spec, code |-> code, other |-> oth])
        /\ halt' = (\lnot oth /\ code /= spec)
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, asyncLive, asyncView, ripLive, stack, lazy, cap, lazyReads, xreads>>

\* code: TopKit/access.py:_View_Call._authorize lines 650-663 (check line 658).
\* Break="view-skips" drops the custody check.
ViewInvoke(t, S) ==
    /\ CanAct /\ Len(reads) < MaxReads
    /\ LET spec == SpecOpen(t, S)
          code == IF Break = "view-skips" THEN TRUE ELSE CodeAllows(t, S)
          oth == OtherHolds(t, S) IN
        /\ reads' = Append(reads, [t |-> t, s |-> S, spec |-> spec, code |-> code, other |-> oth])
        /\ halt' = (\lnot oth /\ code /= spec)
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, asyncLive, asyncView, ripLive, stack, lazy, cap, lazyReads, xreads>>

\* code: TopKit/state.py:_Secret_Pinned_Operation.Secret lines 1016-1026
PinInvoke(t, S) ==
    /\ CanAct /\ Len(reads) < MaxReads
    /\ LET spec == SpecOpen(t, S)
          code == CodeAllows(t, S)
          oth == OtherHolds(t, S) IN
        /\ reads' = Append(reads, [t |-> t, s |-> S, spec |-> spec, code |-> code, other |-> oth])
        /\ halt' = (\lnot oth /\ code /= spec)
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, asyncLive, asyncView, ripLive, stack, lazy, cap, lazyReads, xreads>>

\* Capturing the handle is itself a read (must resolve now).
Capture(t, S) ==
    /\ CanAct /\ CodeAllows(t, S)
    /\ cap' = [cap EXCEPT ![t] = cap[t] \cup {S}]
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, asyncLive, asyncView, ripLive, stack, lazy, reads, lazyReads, xreads, halt>>

\* code: SPECIFICATION.md:809 (captured handle called outside fails closed)
InvokeCaptured(t, S) ==
    /\ CanAct /\ S \in cap[t] /\ Len(reads) < MaxReads
    /\ LET spec == SpecOpen(t, S)
          code == CodeAllows(t, S)
          oth == OtherHolds(t, S) IN
        /\ reads' = Append(reads, [t |-> t, s |-> S, spec |-> spec, code |-> code, other |-> oth])
        /\ halt' = (\lnot oth /\ code /= spec)
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, asyncLive, asyncView, ripLive, stack, lazy, cap, lazyReads, xreads>>

\* Probe action for SD-4: read through another execution's open door.
CrossThreadRead(t, S) ==
    /\ CanAct /\ OtherHolds(t, S) /\ CodeAllows(t, S) /\ Len(xreads) < MaxReads
    /\ xreads' = Append(xreads, [t |-> t, s |-> S, code |-> CodeAllows(t, S)])
    /\ halt' = TRUE
    /\ ops' = ops + 1
    /\ UNCHANGED <<composing, asyncLive, asyncView, ripLive, stack, lazy, cap, reads, lazyReads>>

Done == ops >= MaxOps /\ UNCHANGED vars

Next ==
    \/ \E t \in Threads, A \in Agents :
        EnterSync(t, A) \/ ApplyEnter(t, A) \/ RipEnter(t, A) \/ TeardownEnter(t, A)
        \/ SyncHookEnter(t, A) \/ AsyncHookEnter(t, A)
        \/ SyncHookExitOk(t, A) \/ SyncHookExitRaise(t, A)
        \/ AsyncHookExitOk(t, A) \/ AsyncHookExitRaise(t, A) \/ AsyncHookExitCancel(t, A)
    \/ \E t \in Threads :
        ExitSyncOk(t) \/ ExitSyncRaise(t)
        \/ ApplyExitOk(t) \/ ApplyExitRefused(t)
        \/ RipExitOk(t) \/ RipExitRaise(t)
        \/ TeardownExitOk(t) \/ TeardownExitRaise(t)
        \/ SyncHookBodyEnd(t) \/ SyncHookBlockEnd(t)
        \/ AsyncHookBodyEnd(t) \/ AsyncHookBlockEnd(t)
        \/ ResumeLazy(t) \/ AbandonLazy(t)
    \/ \E t \in Threads, A \in Agents, k \in {"gen", "coro", "agen"} : StartLazy(t, A, k)
    \/ \E t \in Threads, S \in Agents :
        DunderCall(t, S) \/ ReadSecret(t, S) \/ ViewInvoke(t, S) \/ PinInvoke(t, S)
        \/ Capture(t, S) \/ InvokeCaptured(t, S) \/ CrossThreadRead(t, S)
    \/ Done

Spec == Init /\ [][Next]_vars

Quiescent == \A t \in Threads : stack[t] = <<>>

(* SD1: every exit path closes the door: at quiescence the counter is 0, *)
(* no async door and no rip door remains, no view survives.               *)
SD1_DoorBalance ==
    Quiescent => (\A A \in Agents :
        /\ composing[A] = 0 /\ asyncLive[A] = 0 /\ ripLive[A] = 0
        /\ \A t \in Threads : asyncView[<<t, A>>] = 0)

(* SD2: in one execution, a read is allowed iff the OWN door is open.     *)
(* (Reads racing another execution's open door belong to SD-4.)           *)
SD2_FailClosed ==
    \A i \in 1..Len(reads) : \lnot reads[i].other => (reads[i].code = reads[i].spec)

(* SD3: a lazy/dunder body reads its OWN Agent's Secret (spec 782-784).   *)
SD3_LazyOwnSecret ==
    \A i \in 1..Len(lazyReads) : lazyReads[i].code = TRUE

(* SD4: another execution's open door grants nothing here.                *)
SD4_NoCrossThreadLeak ==
    \A i \in 1..Len(xreads) : xreads[i].code = FALSE

====
