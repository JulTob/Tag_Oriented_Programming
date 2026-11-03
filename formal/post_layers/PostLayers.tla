\* PostLayers: the per-name Post layer tower under Tag/Rip/Delete/reTag/
\*   failed-admission/arrest/nested-Imprint acts (STEP-SPEC-61, Deployed).
\*
\* PROMISE: An ordinary Post is a membership-bound Agent Gain: removing its
\*   Tag application from the Field ends that Post layer immediately, before
\*   its @Rip protocols run, and reveals any surviving lower layer of the
\*   same name; a Constant Post becomes a lifetime Contract term at admission
\*   and survives Rip (spec/SPECIFICATION.md:319-328; :1357-1363;
\*   steps/spec/STEP-SPEC-61-condition-lifetimes.md:65-77).
\* HARM: A safety/NDA-style promise silently stops binding while membership
\*   holds, or vanishes after an unrelated Rip, making bool(agent) and the
\*   sound/defective populations lie.
\*
\* COVERS:
\*   - TopKit/overlay.py: _rebuild_post_name (tower rebind, neutral True)
\*   - TopKit/overlay.py: _remove_post_application (app-identity removal,
\*     keep_constants, Constant-lock release)
\*   - TopKit/overlay.py: _clear_post_name (Contract.Delete physical end)
\*   - TopKit/overlay.py: _install (provisional layer push)
\*   - TopKit/overlay.py: _gainings (provisional Constant lock during attempt)
\*   - TopKit/transactions.py: _enter_field (admission owns the application)
\*   - TopKit/transactions.py: _apply_one failure path (provisional discard incl. Constant)
\*   - TopKit/lifecycle.py: _revoke (ordinary ends before teardown; fresh app kept)
\*   - TopKit/lifecycle.py: _rip/_run_one (retry of saved work)
\*   - TopKit/rip_runs.py: _run_saved/_retry (saved-run retry by identity)
\*   - TopKit/contracts.py: Contract.Delete (Constant refusal, absent no-op)
\*   - TopKit/contracts.py: _status_of/_holds/_guarded (truth reads current Posts)
\*   - TopKit/constants.py: _refuse_constant (Constant cannot be replaced/deleted)
\*   - TopKit/arrest.py: _may_act/_require_available (arrest gates truth)
\* CONFIRMED AGAINST COMMIT 1bd5a2548a6bc8fadab9ca4c2451428dbf9b93e4
\*
\* ASSUMPTIONS (single thread; no user code runs inside one action):
\*   - One TLA+ action = one indivisible code step. A Tagging attempt is split
\*     into ProvPush (provisional layer, _install/_gainings) and Admit
\*     (_enter_field: membership + lifetime term) / FailDiscard (_apply_one
\*     failure path, transactions.py:325-342). No Contract.Delete or Rip is
\*     interleaved between a push and its outcome, except through a nested
\*     Imprint (ImprintTag); the kit is single threaded and only user code
\*     (builders/Imprints/teardowns) yields control, whose outcomes are exactly
\*     the Admit/FailDiscard/Rejoin branches.
\*   - Revocation (Field leave + active pop + ordinary-layer removal) is one
\*     action TagRip/RipArrests: in _revoke no user code runs between
\*     field._Remove and _remove_post_application (lifecycle.py:267-287); the
\*     first user callback after revocation is the teardown itself (its failure
\*     is RipArrests, its reTagging power is Rejoin, its retry is RetryOld).
\*   - A nested Imprint may admit an inner same-name layer while the outer
\*     application is still provisional (ImprintTag; outer outcome stays open).
\*     The outer tag itself cannot be re-pushed while provisional.
\*   - Post bodies are boolean flags flipped by the Flip adversary act (flag
\*     flip making a Post fail/hold). A raising Post body is a flag value that
\*     makes the verdict FALSE (code: _verdict maps exceptions to False in
\*     Status/bool, contracts.py:407-415, 441-449). Flags do not affect the
\*     tower mechanics; they keep truth reads honest.
\*   - Underlay form: the top two layers compose via @Underlay (B over A);
\*     an Underlay with no surviving lower layer contributes neutral True
\*     (overlay.py:812-814). Plain-over-plain replaces visibly (latest wins
\*     with a Contract Warning); this model tracks the tower, not warnings.
\*   - Constant C admitted once survives Rip, cannot be deleted or overridden
\*     (constants.py:13-19; contracts.py:568-577). Established Constant
\*     bindings stay intact on reapplication (SPECIFICATION.md:333-335):
\*     re-Tagging the constant author adds no second layer.
\*   - While arrested, ordinary Tagging is refused (arrest.py:
\*     _require_available) EXCEPT reTagging from inside a teardown (Rejoin,
\*     inside the rip door); an explicit Rip still revokes that Tag's own
\*     ordinary layers first, then retries saved work (TagRip + RetryOld);
\*     Contract.Delete still ends removable layers while arrested (observed).
\*     Arrested truth is False without evaluating Posts (_holds,
\*     contracts.py:429-430); evaluating anyway is the evalWhileArrested bug.
\*   - Interrupts arrive only between actions (single thread, Ring 4).
\* NOT MODELLED:
\*   - Per-Tag Field membership beyond the tracked name's applications
\*     (Tag[:]/Tag/~Tag per-tag soundness follows the same verdict; the
\*     real-code probe covers it).
\*   - Warning diagnostics (TagContractWarning on weaken), Pre lifetimes,
\*     Pins, Tools/Secrets/Published gates, multi-name towers (one name only;
\*     names are independent slots), lazy/async results, GC/weakref expiry.
\*   - The double-evaluation incidentals of _holds vs Status (same verdict).
\*
\* INVARIANTS (each one plain sentence):
\*   - PL1_OrdinaryEndsBeforeTeardown: removing an application ends its
\*     ordinary layer before any teardown of that application runs.
\*   - PL2_SurvivorRevealed: ending the top layer reveals the next surviving
\*     layer (top-down read order preserved).
\*   - PL3_MiddleRebinds: ending a middle layer reconnects the upper Underlay
\*     to the nearest survivor, neutral True if none survives.
\*   - PL4_ConstantSurvives: an admitted Constant layer survives every Rip and
\*     Contract.Delete attempt still binds afterwards.
\*   - PL5_FreshKept: an old application's retry never removes a fresh
\*     application's layer of the same name.
\*   - PL6_ProvisionalDiscarded: a failed admission leaves none of that
\*     attempt's layers behind (checked per application identity, which is
\*     never reused, so later admissions cannot mask a leftover).
\*   - PL7_NestedInnerStays: when an outer Tagging fails after its Imprint
\*     admitted an inner same-name Tagging, the inner layer stays and the
\*     outer provisional layer is gone.
\*   - PL8_ArrestNoEval: while arrested, no Post is evaluated (truth is gated
\*     to False without running any check).
\*
\* Break CONSTANT (able to fail; each switch has a _<break>.cfg listing ONLY
\*   the targeted invariant):
\*   - "none": the current code.
\*   - "ordinarySurvivesRip": Rip leaves the ordinary layer in place (teardown
\*     observes the old promise); must violate PL1_OrdinaryEndsBeforeTeardown.
\*   - "topNotRevealed": ending the top layer empties the visible name;
\*     must violate PL2_SurvivorRevealed.
\*   - "noRebind": middle removal leaves the upper Underlay bound to the
\*     removed layer (stale binding); must violate PL3_MiddleRebinds.
\*   - "constantRipped": Rip removes the Constant layer too; must violate
\*     PL4_ConstantSurvives.
\*   - "retryKillsFresh": a saved-work retry removes by Tag instead of by
\*     application identity; must violate PL5_FreshKept.
\*   - "provisionalKept": a failed admission keeps its provisional layers and
\*     lock; must violate PL6_ProvisionalDiscarded.
\*   - "innerLost": an outer failure discards the inner Imprint-admitted
\*     layer too; must violate PL7_NestedInnerStays.
\*   - "evalWhileArrested": a check runs while arrested instead of gating
\*     truth to False; must violate PL8_ArrestNoEval.
\*
\* FINDING: none (pending TLC validation).

------------------------------ MODULE PostLayers ------------------------------
EXTENDS Integers, Sequences, TLC

CONSTANTS MaxOps, Break

VARIABLES
    \* code: TopKit/state.py:_Post_Layer lines 67-82 + _State.post_layers lines 94-95
    \* mirrors the tower for the one tracked name, oldest first; each layer is
    \* [tag |-> "A"/"B"/"C", app |-> application id, const |-> BOOLEAN]
    layers,
    \* code: TopKit/state.py:_State.post_applications lines 96-101 (live
    \* application per Tag for the tracked name); mirrors admitted membership.
    \* apps[t] = 0 means t holds no admitted application of the tracked name.
    apps,
    \* code: TopKit/state.py:_State.constants line 112 (Constant lock for the
    \* tracked name); mirrors the admitted-Constant binding protection.
    \* Monotonic here: an admitted lock is never released because admitted
    \* Constant layers are never removed (kept on Rip, Delete refused).
    clock,
    \* code: TopKit/arrest.py:_safehouse (custody); mirrors whether the agent
    \* is arrested with saved Rip work outstanding
    arrested,
    \* code: TopKit/rip_runs.py:_RipRun (saved old run); mirrors the saved
    \* application the retry must remove by identity
    savedTag, savedApp,
    \* code: TopKit/transactions.py:_apply_one line 227 (opaque application
    \* identity); mirrors the next fresh application id (never reused)
    nextApp,
    \* code: TopKit/overlay.py:_install (provisional push during Gainings);
    \* mirrors the outstanding provisional application: prov = 0 means none.
    \* provTag is its author, provConst whether it declares a Constant.
    prov, provTag, provConst,
    \* code: TopKit/transactions.py:_apply_one lines 325-342; mirrors the set
    \* of application ids whose admission failed (discarded, never reused)
    failedApps,
    \* history: records that a teardown ran while an ordinary layer of the
    \* removed application was still present (PL1 witness)
    sawStaleTeardown,
    \* history: records that a retry removed a live fresh layer (PL5 witness)
    killedFresh,
    \* history: the visible top tag right after each top removal (PL2 oracle):
    \* revealCheck is what the tower actually shows, revealWant what the
    \* nearest-survivor rule demands; "" means no removal observed yet
    revealCheck, revealWant,
    \* history: which lower tag the visible compiled check currently calls
    \* ("" = neutral True); correct code rebinds it on every tower change
    \* (overlay.py:_rebuild_post_name); PL3 compares it against ExpLower
    boundLower,
    \* history: records that a Post was evaluated while arrested (PL8 witness)
    sawArrestEval,
    \* history: records that an outer failure discarded an admitted inner
    \* layer (PL7 witness)
    lostInner,
    \* history: records that a failed admission kept a provisional layer/lock
    \* (PL6 backup witness; PL6 itself is checked via failedApps)
    provKept,
    \* history: counts steps taken (bounds the search)
    ops,
    \* code: the Post bodies (one boolean verdict each, read by Status/bool)
    flags

vars == <<layers, apps, clock, arrested, savedTag, savedApp, nextApp,
          prov, provTag, provConst, failedApps,
          sawStaleTeardown, killedFresh, revealCheck, revealWant, boundLower,
          sawArrestEval, lostInner, provKept, ops, flags>>

Tags == {"A", "B", "C"}
\* B is the @Underlay layer, C is the Constant author in this model.
IsUnderlay(t) == t = "B"
IsConstantAuthor(t) == t = "C"

\* code: TopKit/overlay.py:_rebuild_post_name lines 789-819: the lower tag an
\* upper Underlay must call ("" = neutral True when none survives).
ExpLower(s) ==
    LET n == Len(s) IN
    IF n < 2 THEN ""
    ELSE IF s[n].tag = "B" THEN s[n-1].tag
    ELSE ""

VisibleTop(s) == IF s = <<>> THEN "" ELSE s[Len(s)].tag

Init ==
    /\ layers = <<>>
    /\ apps = [t \in Tags |-> 0]
    /\ clock = FALSE
    /\ arrested = FALSE
    /\ savedTag = ""
    /\ savedApp = 0
    /\ nextApp = 1
    /\ prov = 0
    /\ provTag = ""
    /\ provConst = FALSE
    /\ failedApps = {}
    /\ sawStaleTeardown = FALSE
    /\ killedFresh = FALSE
    /\ revealCheck = ""
    /\ revealWant = ""
    /\ boundLower = ""
    /\ sawArrestEval = FALSE
    /\ lostInner = FALSE
    /\ provKept = FALSE
    /\ ops = 0
    /\ flags = [t \in Tags |-> TRUE]

WithinBudget == ops < MaxOps
Tick == ops' = ops + 1

\* code: TopKit/overlay.py:_install lines 415-455 (provisional layer push
\* during Gainings, incl. a provisional Constant) + _gainings (provisional
\* Constant lock, kept in provConst until admission owns or discards it).
ProvPush(t) ==
    /\ WithinBudget
    /\ ~arrested
    /\ prov = 0
    /\ apps[t] = 0
    /\ Len(layers) < 3
    /\ nextApp <= 4
    /\ LET new == Append(layers,
                         [tag |-> t, app |-> nextApp,
                          const |-> IsConstantAuthor(t)]) IN
       /\ layers' = new
       /\ boundLower' = ExpLower(new)
    /\ prov' = nextApp
    /\ provTag' = t
    /\ provConst' = IsConstantAuthor(t)
    /\ nextApp' = nextApp + 1
    /\ Tick
    /\ UNCHANGED <<apps, clock, arrested, savedTag, savedApp, failedApps,
                   sawStaleTeardown, killedFresh, revealCheck, revealWant,
                   sawArrestEval, lostInner, provKept, flags>>

\* code: TopKit/transactions.py:_enter_field lines 525-552 (admission owns the
\* application) + TopKit/constants.py:_constant_overlay (identical Constant
\* reapplication adds no second layer; ordinary over a surviving Constant is
\* refused with TagCompositionError, leaving no layer and no membership).
Admit ==
    /\ WithinBudget
    /\ prov # 0
    /\ prov' = 0
    /\ provTag' = ""
    /\ provConst' = FALSE
    /\ IF clock /\ ~IsConstantAuthor(provTag)
       THEN \* refused ordinary over a surviving Constant
            /\ LET kept == SelectSeq(layers, LAMBDA l : l.app /= prov) IN
               /\ layers' = kept
               /\ boundLower' = ExpLower(kept)
            /\ UNCHANGED <<apps, clock>>
       ELSE IF IsConstantAuthor(provTag) /\ clock
            THEN \* reapplication preserves the same declaration's Constants:
                 \* the provisional layer goes, membership resumes, no 2nd layer
                 /\ LET kept == SelectSeq(layers, LAMBDA l : l.app /= prov) IN
                    /\ layers' = kept
                    /\ boundLower' = ExpLower(kept)
                 /\ apps' = [apps EXCEPT ![provTag] = prov]
                 /\ UNCHANGED <<clock>>
            ELSE \* success: the provisional layer becomes the admitted one
                 /\ apps' = [apps EXCEPT ![provTag] = prov]
                 /\ clock' = (clock \/ provConst)
                 /\ UNCHANGED <<layers>>
                 /\ boundLower' = ExpLower(layers)
    /\ Tick
    /\ UNCHANGED <<arrested, savedTag, savedApp, nextApp, failedApps,
                   sawStaleTeardown, killedFresh, revealCheck, revealWant,
                   sawArrestEval, lostInner, provKept, flags>>

\* code: TopKit/transactions.py:_apply_one lines 325-342 (pre-admission
\* failure discards every provisional Post incl. Constant + its lock).
FailDiscard ==
    /\ WithinBudget
    /\ prov # 0
    /\ failedApps' = failedApps \cup {prov}
    /\ prov' = 0
    /\ provTag' = ""
    /\ provConst' = FALSE
    /\ \/ /\ Break = "provisionalKept"
          \* BUG: the failed admission keeps its provisional layers + lock
          /\ UNCHANGED <<layers, boundLower>>
          /\ clock' = (clock \/ provConst)
          /\ provKept' = TRUE
          /\ UNCHANGED <<lostInner>>
       \/ /\ Break = "innerLost"
          \* BUG: the outer failure discards inner Imprint-admitted layers too
          /\ LET kept == SelectSeq(layers, LAMBDA l : l.app < prov) IN
             /\ layers' = kept
             /\ boundLower' = ExpLower(kept)
          /\ lostInner' = (lostInner
                           \/ (\E i \in 1..Len(layers) : layers[i].app > prov))
          /\ UNCHANGED <<clock, provKept>>
       \/ /\ Break \notin {"provisionalKept", "innerLost"}
          /\ LET kept == SelectSeq(layers, LAMBDA l : l.app /= prov) IN
             /\ layers' = kept
             /\ boundLower' = ExpLower(kept)
          /\ UNCHANGED <<clock, provKept, lostInner>>
    /\ Tick
    /\ UNCHANGED <<apps, arrested, savedTag, savedApp, nextApp,
                   sawStaleTeardown, killedFresh, revealCheck, revealWant,
                   sawArrestEval, flags>>

\* code: TopKit/transactions.py:_imprint (a nested Imprint admits an inner
\* same-name Tagging while the outer application is still provisional).
ImprintTag(t) ==
    /\ WithinBudget
    /\ ~arrested
    /\ prov # 0
    /\ t # provTag
    /\ apps[t] = 0
    /\ Len(layers) < 3
    /\ nextApp <= 4
    /\ IF clock /\ ~IsConstantAuthor(t)
       THEN \* refused inner ordinary over a surviving Constant
            /\ clock' = clock
            /\ Tick
            /\ UNCHANGED <<layers, apps, nextApp, boundLower>>
       ELSE /\ LET new == Append(layers,
                                 [tag |-> t, app |-> nextApp,
                                  const |-> IsConstantAuthor(t)]) IN
               /\ layers' = new
               /\ boundLower' = ExpLower(new)
            /\ apps' = [apps EXCEPT ![t] = nextApp]
            /\ clock' = (clock \/ IsConstantAuthor(t))
            /\ nextApp' = nextApp + 1
            /\ Tick
    /\ UNCHANGED <<arrested, savedTag, savedApp, prov, provTag, provConst,
                   failedApps, sawStaleTeardown, killedFresh,
                   revealCheck, revealWant,
                   sawArrestEval, lostInner, provKept, flags>>

\* code: TopKit/lifecycle.py:_revoke lines 243-294 (Field leaves, active pops,
\* ordinary layers of THAT application end, all before any teardown runs) +
\* TopKit/overlay.py:_remove_post_application with keep_constants=TRUE.
TagRip(t) ==
    /\ WithinBudget
    /\ prov = 0
    /\ apps[t] # 0
    /\ LET app == apps[t] IN
       LET topGone == /\ layers # <<>>
                      /\ layers[Len(layers)].app = app
                      /\ ((Break = "constantRipped")
                          \/ ~layers[Len(layers)].const) IN
       LET new == IF Break = "constantRipped"
                  THEN SelectSeq(layers, LAMBDA l : l.app /= app)
                  ELSE SelectSeq(layers,
                                 LAMBDA l : ~(l.app = app /\ ~l.const)) IN
       LET shown == IF Break = "topNotRevealed" /\ topGone
                    THEN <<>>
                    ELSE new IN
       /\ apps' = [apps EXCEPT ![t] = 0]
       /\ layers' = IF Break = "ordinarySurvivesRip" THEN layers ELSE shown
       /\ IF Break = "ordinarySurvivesRip"
          THEN \* BUG: teardown observes the still-bound old promise
               /\ sawStaleTeardown' = TRUE
               /\ UNCHANGED <<boundLower>>
          ELSE /\ UNCHANGED <<sawStaleTeardown>>
               /\ boundLower' = IF Break = "noRebind"
                                \* BUG: upper Underlay stays bound to the
                                \* removed layer (stale binding)
                                THEN boundLower
                                ELSE ExpLower(shown)
       /\ IF topGone /\ Break /= "ordinarySurvivesRip"
          THEN /\ revealWant' = VisibleTop(new)
               /\ revealCheck' = VisibleTop(shown)
          ELSE UNCHANGED <<revealCheck, revealWant>>
    /\ Tick
    /\ UNCHANGED <<clock, arrested, savedTag, savedApp, nextApp, prov, provTag,
                   provConst, failedApps, killedFresh,
                   sawArrestEval, lostInner, provKept, flags>>

\* code: TopKit/lifecycle.py:_revoke + _run_saved with a failing teardown:
\* revocation ends the ordinary layers, the teardown fails, the agent is
\* arrested with the saved run outstanding.
RipArrests(t) ==
    /\ WithinBudget
    /\ ~arrested
    /\ prov = 0
    /\ apps[t] # 0
    /\ LET app == apps[t] IN
       LET new == SelectSeq(layers,
                            LAMBDA l : ~(l.app = app /\ ~l.const)) IN
       /\ apps' = [apps EXCEPT ![t] = 0]
       /\ layers' = new
       /\ boundLower' = ExpLower(new)
       /\ arrested' = TRUE
       /\ savedTag' = t
       /\ savedApp' = app
    /\ Tick
    /\ UNCHANGED <<clock, nextApp, prov, provTag, provConst, failedApps,
                   sawStaleTeardown, killedFresh, revealCheck, revealWant,
                   sawArrestEval, lostInner, provKept, flags>>

\* code: a teardown that deliberately reTags the agent (inside the rip door,
\* so arrest does not refuse it); the fresh application gets its own layers.
Rejoin(t) ==
    /\ WithinBudget
    /\ arrested
    /\ prov = 0
    /\ apps[t] = 0
    /\ Len(layers) < 3
    /\ nextApp <= 4
    /\ ~(clock /\ ~IsConstantAuthor(t))
    /\ \/ /\ IsConstantAuthor(t) /\ clock
          /\ apps' = [apps EXCEPT ![t] = nextApp]
          /\ nextApp' = nextApp + 1
          /\ UNCHANGED <<layers, clock, boundLower>>
       \/ /\ ~(IsConstantAuthor(t) /\ clock)
          /\ LET new == Append(layers,
                               [tag |-> t, app |-> nextApp,
                                const |-> IsConstantAuthor(t)]) IN
             /\ layers' = new
             /\ boundLower' = ExpLower(new)
          /\ apps' = [apps EXCEPT ![t] = nextApp]
          /\ clock' = (clock \/ IsConstantAuthor(t))
          /\ nextApp' = nextApp + 1
    /\ Tick
    /\ UNCHANGED <<arrested, savedTag, savedApp, prov, provTag, provConst,
                   failedApps, sawStaleTeardown, killedFresh,
                   revealCheck, revealWant,
                   sawArrestEval, lostInner, provKept, flags>>

\* code: TopKit/rip_runs.py:_run_saved retry + lifecycle.py:_revoke (the retry
\* removes by opaque application identity, never by Tag).
RetryOld ==
    /\ WithinBudget
    /\ arrested
    /\ prov = 0
    /\ savedApp # 0
    /\ arrested' = FALSE
    /\ savedApp' = 0
    /\ savedTag' = ""
    /\ IF Break = "retryKillsFresh"
       THEN \* BUG: the retry removes by Tag, killing the fresh application
            /\ LET kept == SelectSeq(layers,
                                     LAMBDA l : l.tag /= savedTag) IN
               /\ layers' = kept
               /\ boundLower' = ExpLower(kept)
            /\ killedFresh' = (killedFresh
               \/ (\E i \in 1..Len(layers) :
                      /\ layers[i].tag = savedTag
                      /\ layers[i].app /= savedApp
                      /\ apps[layers[i].tag] = layers[i].app))
       ELSE /\ LET kept == SelectSeq(layers,
                                     LAMBDA l : l.app /= savedApp \/ l.const) IN
               /\ layers' = kept
               /\ boundLower' = ExpLower(kept)
            /\ UNCHANGED <<killedFresh>>
    /\ Tick
    /\ UNCHANGED <<apps, clock, nextApp, prov, provTag, provConst, failedApps,
                   sawStaleTeardown, revealCheck, revealWant,
                   sawArrestEval, lostInner, provKept, flags>>

\* code: TopKit/contracts.py:Contract.Delete lines 554-586 (_refuse_constant
\* raises before anything is removed; _clear_post_name ends every removable
\* layer; still available while arrested, observed real behaviour).
ContractDelete ==
    /\ WithinBudget
    /\ prov = 0
    /\ layers # <<>>
    /\ IF clock
       THEN \* refusal: a Constant binding cannot be deleted; tower unchanged
            UNCHANGED <<layers, boundLower, revealCheck, revealWant>>
       ELSE /\ layers' = <<>>
            /\ boundLower' = ""
            /\ revealWant' = ""
            /\ revealCheck' = ""
    /\ Tick
    /\ UNCHANGED <<apps, clock, arrested, savedTag, savedApp, nextApp,
                   prov, provTag, provConst, failedApps,
                   sawStaleTeardown, killedFresh,
                   sawArrestEval, lostInner, provKept, flags>>

\* BUG (Break = "evalWhileArrested" only): a check runs while arrested
\* instead of gating truth to False without evaluating (contracts.py:429).
EvalWhileArrested ==
    /\ WithinBudget
    /\ arrested
    /\ Break = "evalWhileArrested"
    /\ sawArrestEval' = TRUE
    /\ Tick
    /\ UNCHANGED <<layers, apps, clock, arrested, savedTag, savedApp, nextApp,
                   prov, provTag, provConst, failedApps,
                   sawStaleTeardown, killedFresh, revealCheck, revealWant,
                   boundLower, lostInner, provKept, flags>>

\* Adversary: a Post body starts failing/holding (drives truth reads).
Flip(t) ==
    /\ WithinBudget
    /\ flags' = [flags EXCEPT ![t] = ~flags[t]]
    /\ Tick
    /\ UNCHANGED <<layers, apps, clock, arrested, savedTag, savedApp, nextApp,
                   prov, provTag, provConst, failedApps,
                   sawStaleTeardown, killedFresh, revealCheck, revealWant,
                   boundLower, sawArrestEval, lostInner, provKept>>

Done == ops >= MaxOps /\ UNCHANGED vars

Next ==
    \/ \E t \in Tags : ProvPush(t)
    \/ Admit
    \/ FailDiscard
    \/ \E t \in Tags : ImprintTag(t)
    \/ \E t \in Tags : TagRip(t)
    \/ \E t \in Tags : RipArrests(t)
    \/ \E t \in Tags : Rejoin(t)
    \/ RetryOld
    \/ ContractDelete
    \/ EvalWhileArrested
    \/ \E t \in Tags : Flip(t)
    \/ Done

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ layers \in Seq([tag : Tags, app : 0..6, const : BOOLEAN])
    /\ apps \in [Tags -> 0..6]
    /\ clock \in BOOLEAN
    /\ arrested \in BOOLEAN
    /\ savedTag \in Tags \cup {""}
    /\ savedApp \in 0..6
    /\ nextApp \in 1..7
    /\ prov \in 0..6
    /\ provTag \in Tags \cup {""}
    /\ provConst \in BOOLEAN
    /\ failedApps \in SUBSET (0..6)
    /\ sawStaleTeardown \in BOOLEAN
    /\ killedFresh \in BOOLEAN
    /\ revealCheck \in Tags \cup {""}
    /\ revealWant \in Tags \cup {""}
    /\ boundLower \in Tags \cup {""}
    /\ sawArrestEval \in BOOLEAN
    /\ lostInner \in BOOLEAN
    /\ provKept \in BOOLEAN
    /\ ops \in 0..MaxOps
    /\ flags \in [Tags -> BOOLEAN]

\* PL1: removing an application ends its ordinary layer before any teardown
\* of that application runs.
PL1_OrdinaryEndsBeforeTeardown == ~sawStaleTeardown
PL2_SurvivorRevealed == (revealWant = "" \/ revealCheck = revealWant)
\* PL3: ending a middle layer reconnects the upper Underlay to the nearest
\* survivor (neutral True if none survives).
PL3_MiddleRebinds == boundLower = ExpLower(layers)
\* PL4: an admitted Constant layer survives every Rip and Contract.Delete.
PL4_ConstantSurvives == (clock => (\E i \in 1..Len(layers) : layers[i].const))
\* PL5: an old application's retry never removes a fresh layer.
PL5_FreshKept == ~killedFresh
\* PL6: a failed admission leaves none of that attempt's layers behind.
PL6_ProvisionalDiscarded ==
    \A a \in failedApps : ~(\E i \in 1..Len(layers) : layers[i].app = a)
\* PL7: an outer failure keeps the inner Imprint-admitted layer.
PL7_NestedInnerStays == ~lostInner
\* PL8: while arrested, no Post is evaluated.
PL8_ArrestNoEval == ~sawArrestEval

=============================================================================
