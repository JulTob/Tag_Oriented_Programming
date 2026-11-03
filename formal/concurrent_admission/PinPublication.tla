\* PinPublication: a concrete Pin applied while another thread is mid-Tagging.
\*
\* PROMISE: A Pin's @Public Gain published onto the pinned Tag's Field reaches
\*   every present Agent at pinning (spec/SPECIFICATION.md:1165: "every present
\*   Agent receives it at pinning", full sentence 1164-1169: "@Public publishes
\*   it onto the pinned Tag's Field: every present Agent receives it at pinning
\*   and every future Agent through the Tag").
\*
\* COVERS:
\*   - TopKit/transactions.py:_enter_field lines 525-567 (plans 534-536,
\*     field._Add 539, active.append 540, publish call 562-567)
\*   - TopKit/transactions.py:_publication_plans lines 570-605 (snapshot 581:
\*     agents = list(pinned[:]); per-agent copy preflight, touches none)
\*   - TopKit/transactions.py:_publish_to_field lines 608-639 (publish loop
\*     over the snapshot only, 618-639)
\* CONFIRMED AGAINST COMMIT 1bd5a2548a6bc8fadab9ca4c2451428dbf9b93e4
\*
\* ASSUMPTIONS (one Tagging thread admitting agent X to Field F of ordinary
\*   Tag W, one pin thread applying a concrete Pin with one @Public member):
\*   - One TLA+ action = one indivisible code step. GateX is W's Gate+Imprint
\*     for X (user code ran: the switch point). JoinX is field._Add + active
\*     bookkeeping with no user code, so one step. Plan is the snapshotncopy
\*     preflight, which touches no recipient, so one step. Publish is the
\*     snapshot loop, so one step.
\*   - The invariant is judged at terminal states only (both procedures done):
\*     mid-run an agent may transiently await publication; only the end state
\*     must have every Field member holding the member.
\*   - No collision (the preflight passes); the present member P is idle.
\* NOT MODELLED:
\*   - Future Agents (they receive the member through the Tag: covered by
\*     existing single-thread tests, e.g. the "future" case in
\*     tests/test_constants.py).
\*   - Pin refusal / collision paths (touch none: orthogonal).
\*
\* INVARIANTS (each one plain sentence):
\*   - CA3_PublishAll: when both procedures are done, every Agent of the
\*     Field holds the published member.
\*
\* Break CONSTANT (able to fail; each switch has a _<break>.cfg):
\*   - "none": the current code (snapshot plans, publish to the snapshot).
\*   - "skipPresent": a plausible mistake dropping the _publish_to_field loop
\*     (publish to future Agents only); must still violate CA3_PublishAll.
\*   - "locked": the obvious fix (Plan..Publish under one lock; joining while
\*     the pin is done takes the through-Tag path at join);
\*     must satisfy CA3_PublishAll (PinPublication_fixed.cfg).
\*
\* FINDING CA-3 (outside the documented promise):
\*   1. Thread A starts Held(ari); W's Gate passes, user Imprint blocks.
\*   2. Pin thread applies Rare(Held): plans snapshot the Field (without ari;
\*      transactions.py:581), then publishes to the snapshot only (608-639).
\*   3. Thread A resumes: ari joins the Field (539-540) with gains prepared
\*      before the publication: ari never receives the member.
\*   End: ari in Held, Held.rarity == 'rare', but ari.rarity raises
\*   AttributeError; a later Agent gets 'rare'.
\*   Classification: outside the documented promise. Spec Ring 4
\*   (spec/SPECIFICATION.md:1767): "Threads. One Agent, one thread. Fields are
\*   not synchronized." TopKit/IMPLEMENTATION_NOTES.md:676-677: "One Agent,
\*   one thread. The composing counter and Fields are not synchronized."
\*   Real-code reproducer: formal/concurrent_admission/repro_CA3.py.

---------------------------- MODULE PinPublication ----------------------------
EXTENDS Integers, TLC

CONSTANTS Break

VARIABLES
    \* mirrors Field membership of the pinned Tag's Field
    \* code: TopKit/transactions.py:_enter_field line 539 (field._Add)
    field,
    \* mirrors which Field members hold the published Gain
    has,
    \* code: TopKit/transactions.py:_publication_plans lines 570-605 (snapshot)
    plans,
    \* mirrors whether X passed W's Gate (user Imprint returned)
    xGated,
    \* scheduling only: Tagging-thread position (gate/join/done)
    pcTag,
    \* scheduling only: pin-thread position (plan/publish/done)
    pcPin,
    \* mirrors that the Pin's publish ran (joiners then take the through-Tag path)
    pinDone,
    \* the obvious fix's lock (held from Plan to Publish)
    lock

vars == <<field, has, plans, xGated, pcTag, pcPin, pinDone, lock>>

Agents == {"P", "X"}

Init ==
    /\ field = {"P"}
    /\ has = {}
    /\ plans = {}
    /\ xGated = FALSE
    /\ pcTag = "gate"
    /\ pcPin = "plan"
    /\ pinDone = FALSE
    /\ lock = FALSE

\* code: TopKit/transactions.py:_apply_one lines 266-284 (W's gains + user
\*   Imprint for X run: the switch point; X has not joined the Field yet).
GateX ==
    /\ pcTag = "gate"
    /\ xGated' = TRUE
    /\ pcTag' = "join"
    /\ UNCHANGED <<field, has, plans, pcPin, pinDone, lock>>

\* code: TopKit/transactions.py:_enter_field line 539 (field._Add) + line 540
\*   (active.append). One step: no user code. The fix takes the through-Tag
\*   path at join when the pin is already done; the fix's lock forbids joining
\*   mid-publication.
JoinX ==
    /\ pcTag = "join"
    /\ (Break # "locked") \/ (~lock)
    /\ field' = (field \cup {"X"})
    /\ has' = IF (Break = "locked") /\ pinDone THEN (has \cup {"X"}) ELSE has
    /\ pcTag' = "done"
    /\ UNCHANGED <<plans, xGated, pcPin, pinDone, lock>>

\* code: TopKit/transactions.py:_enter_field lines 534-536 + _publication_plans
\*   lines 570-605 (snapshot the Field; the copy preflight touches none).
\*   One step. The fix holds the lock from here to Publish.
Plan ==
    /\ pcPin = "plan"
    /\ (Break # "locked") \/ (~lock)
    /\ plans' = field
    /\ lock' = IF Break = "locked" THEN TRUE ELSE lock
    /\ pcPin' = "publish"
    /\ UNCHANGED <<field, has, xGated, pcTag, pinDone>>

\* code: TopKit/transactions.py:_enter_field lines 562-567 + _publish_to_field
\*   lines 608-639 (loop over the snapshot only). One step.
\*   Break "skipPresent" drops the loop (future Agents only). The fix publishes
\*   to the live Field and releases the lock.
Publish ==
    /\ pcPin = "publish"
    /\ has' = IF Break = "skipPresent" THEN has
              ELSE (IF Break = "locked" THEN (has \cup field) ELSE (has \cup plans))
    /\ pinDone' = TRUE
    /\ lock' = IF Break = "locked" THEN FALSE ELSE lock
    /\ pcPin' = "done"
    /\ UNCHANGED <<field, plans, xGated, pcTag>>

\* Terminal stuttering step (no deadlock: every run ends with both threads done).
Done == (pcTag = "done") /\ (pcPin = "done") /\ UNCHANGED vars

Next == GateX \/ JoinX \/ Plan \/ Publish \/ Done

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ field \subseteq Agents
    /\ has \subseteq Agents
    /\ plans \subseteq Agents
    /\ xGated \in BOOLEAN
    /\ pcTag \in {"gate", "join", "done"}
    /\ pcPin \in {"plan", "publish", "done"}
    /\ pinDone \in BOOLEAN
    /\ lock \in BOOLEAN

\* When both procedures are done, every Agent of the Field holds the member.
CA3_PublishAll ==
    (((pcTag = "done") /\ (pcPin = "done")) => (\A a \in field: a \in has))

=============================================================================
