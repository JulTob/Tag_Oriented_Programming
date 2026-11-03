\* RuntimeTypeCache: two threads racing in state._runtime_type_for.
\*
\* PROMISE: Two Agents of one host whose type-level facts match share ONE
\*   runtime type, and type(...) construction runs once for one key
\*   (TopKit/IMPLEMENTATION_NOTES.md:60-65: "Runtime types are shared across
\*   every Agent whose host and type-level facts match").
\* HARM: Two runtime types for one key; host __init_subclass__ / metaclass
\*   side effects run twice; the second construction can spuriously fail with
\*   TagCompositionError ("cannot be actualized as an Agent").
\*
\* COVERS:
\*   - TopKit/state.py:_type_cache (line 1347; the shared lock-free cache)
\*   - TopKit/state.py:_type_key_of (lines 1470-1493; assumed equal here)
\*   - TopKit/state.py:_runtime_type_for (lines 1496-1642: read 1502-1506,
\*     create 1595-1600, store 1642)
\* CONFIRMED AGAINST COMMIT 1bd5a2548a6bc8fadab9ca4c2451428dbf9b93e4
\*
\* ASSUMPTIONS (two threads, two distinct Agents of one host, one key):
\*   - Both threads compute the same key (same host class, same facts); key
\*     computation is pure (no user code) and is not modelled.
\*   - One TLA+ action = one indivisible code step. Check is a single dict
\*     get with no user code between the read and the branch, so one step.
\*     Create is type(...), which runs host/metaclass code, so the peer may
\*     act before AND after it (its own action). Store is the dict set plus
\*     installing the type on the Agent, with no user code between, so one step.
\*   - The constructed type's identity is the building thread (types built
\*     from equal keys are interchangeable except for identity).
\*   - Thread switches happen while user/host code blocks (the GIL is enabled
\*     but blocking hooks yield); no switch is assumed inside one action.
\* NOT MODELLED:
\*   - WeakValueDictionary expiry / GC of cache entries.
\*   - A metaclass refusing the second construction (a further harm of the
\*     same race, shown on real code by repro_CA1.py variant output).
\*   - More than two threads (two already force the interleaving).
\*
\* INVARIANTS (each one plain sentence):
\*   - CA1_SingleType: type(...) ran at most once, and every finished Agent
\*     holds the cached type.
\*
\* Break CONSTANT (able to fail; each switch has a _<break>.cfg):
\*   - "none": the current code (check, then create, then store).
\*   - "recheck": a plausible incomplete fix (re-read the cache after create
\*     but adopt-or-store without un-building); must still violate CA1_SingleType.
\*   - "locked": the obvious fix (check+create+store under one lock);
\*     must satisfy CA1_SingleType (RuntimeTypeCache_fixed.cfg).
\*
\* FINDING CA-1 (outside the documented promise):
\*   1. Thread A checks the cache: miss (state.py:1503-1506).
\*   2. Thread B checks the cache: miss.
\*   3. Thread A runs type(...) (host __init_subclass__ runs), stores A-type.
\*   4. Thread B runs type(...) again, stores B-type (last writer wins).
\*   End: two runtime types for one key; A's Agent holds a type the cache no
\*   longer names (on real code: "cache is a0: True; cache is a1: False").
\*   Classification: outside the documented promise. Spec Ring 4
\*   (spec/SPECIFICATION.md:1767): "Threads. One Agent, one thread. Fields are
\*   not synchronized." TopKit/IMPLEMENTATION_NOTES.md:676-677: "One Agent,
\*   one thread. The composing counter and Fields are not synchronized."
\*   Real-code reproducer: formal/concurrent_admission/repro_CA1.py.

-------------------------- MODULE RuntimeTypeCache --------------------------
EXTENDS Integers, TLC

CONSTANTS Break

VARIABLES
    \* code: TopKit/state.py:_type_cache line 1347; "none" = no entry
    cache,
    \* history: how many times type(...) ran
    \* code: TopKit/state.py:_runtime_type_for lines 1595-1600
    created,
    \* mirrors type(agent) once installed on the Agent; "none" = not yet
    inst,
    \* scheduling only: per-thread position (check/create/store/done)
    pc

vars == <<cache, created, inst, pc>>

Threads == {"t1", "t2"}

Init ==
    /\ cache = "none"
    /\ created = 0
    /\ inst = [t \in Threads |-> "none"]
    /\ pc = [t \in Threads |-> "check"]

\* code: TopKit/state.py:_runtime_type_for lines 1502-1506 (cache read + return).
\*   One step: a dict get with no user code between the read and the branch.
Check(t) ==
    /\ Break # "locked"
    /\ pc[t] = "check"
    /\ IF cache = "none"
       THEN /\ pc' = [pc EXCEPT ![t] = "create"]
            /\ UNCHANGED inst
       ELSE /\ inst' = [inst EXCEPT ![t] = cache]
            /\ pc' = [pc EXCEPT ![t] = "done"]
    /\ UNCHANGED <<cache, created>>

\* code: TopKit/state.py:_runtime_type_for lines 1595-1600 (type(...) runs host
\*   and metaclass code: the peer may act before and after this action).
Create(t) ==
    /\ Break # "locked"
    /\ pc[t] = "create"
    /\ created' = created + 1
    /\ pc' = [pc EXCEPT ![t] = "store"]
    /\ UNCHANGED <<cache, inst>>

\* code: TopKit/state.py:_runtime_type_for line 1642 (store) + installing the
\*   type on the Agent. One step: no user code between the set and the install.
\*   Break "recheck" re-reads the cache after create (the incomplete fix) but,
\*   like the sketched patch, stores anyway when still a miss and merely adopts
\*   (without un-building) on a hit.
Store(t) ==
    /\ Break # "locked"
    /\ pc[t] = "store"
    /\ IF (Break = "recheck") /\ (cache # "none")
       THEN /\ inst' = [inst EXCEPT ![t] = cache]
            /\ UNCHANGED cache
       ELSE /\ cache' = t
            /\ inst' = [inst EXCEPT ![t] = t]
    /\ pc' = [pc EXCEPT ![t] = "done"]
    /\ UNCHANGED created

\* The obvious fix: check, create and store under one lock (one step: the peer
\*   cannot act between the check and the store).
AtomicAdmit(t) ==
    /\ Break = "locked"
    /\ pc[t] = "check"
    /\ IF cache = "none"
       THEN /\ created' = created + 1
            /\ cache' = t
            /\ inst' = [inst EXCEPT ![t] = t]
       ELSE /\ inst' = [inst EXCEPT ![t] = cache]
            /\ UNCHANGED <<cache, created>>
    /\ pc' = [pc EXCEPT ![t] = "done"]

\* Terminal stuttering step (no deadlock: every run ends with both threads done).
Done == (\A t \in Threads: pc[t] = "done") /\ UNCHANGED vars

Next == (\E t \in Threads: Check(t) \/ Create(t) \/ Store(t) \/ AtomicAdmit(t)) \/ Done

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ cache \in ({"none"} \cup Threads)
    /\ created \in 0..2
    /\ inst \in [Threads -> ({"none"} \cup Threads)]
    /\ pc \in [Threads -> {"check", "create", "store", "done"}]

\* type(...) ran at most once, and every finished Agent holds the cached type.
CA1_SingleType ==
    /\ created =< 1
    /\ (\A t \in Threads: (pc[t] = "done" => ((inst[t] # "none") /\ (inst[t] = cache))))

=============================================================================
