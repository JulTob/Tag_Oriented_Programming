# Performance: what TOP costs against plain OOP, and why

- **Date:** 2026-09-24
- **Measured:** TopKit on `main` after PR #20, against the same behaviour
  written as idiomatic Python classes, on CPython 3.14.3 (Apple silicon).
- **Why:** users reported that TopKit is slow. The Director suspected they
  kept passing states as Tags, and asked whether TOP only moves a budget
  between time and memory instead of saving it.
- **Method:** every figure below was measured. Times are the fastest of at
  least seven runs (`time.perf_counter`); memory is bytes still alive per
  object over at least 1,000 objects (`tracemalloc`, in a pass of its own).
  The machine was shared: absolute times drift, so before/after figures come
  from alternating runs of both kits and TOP/OOP figures from one run. Every
  suspected cause was confirmed by an elimination experiment on a copy of
  the kit. `benchmarks/compare.py` reproduces the comparison.

---

## 1. Verdict in one page

**The complaint is real, and it has two causes.**

1. **Tags used as Records.** A passing state (Asleep, Poisoned, Stunned)
   applied and Ripped as a Tag every turn costs **2.9 to 4.3 us per turn,
   280 to 420 times a plain attribute**, and 285 to 430 ms per 100,000
   agent-turns. Kept as a Record, as the Guide says, the same state costs
   **24 to 42 ns, 2.4 to 3 times a plain attribute**. No kit can close the
   first gap: a tagging is a transaction (gate, contributions, promise,
   rollback), and its floor is about 1 us. The remedy is the paradigm's own
   rule, *a Tag is what something is; a Record is what it is right now*.
2. **The kit, not the paradigm.** Almost everything else TOP paid, in time
   and in memory, was an implementation choice. The spec forces very little
   of it (§6).

**TOP did not trade memory for speed; it paid both.** Before this work a
TOP character held **38 to 61 times the memory** of the same OOP object
(4.3 KB with one Tag, 13.7 KB with six, against 113 to 225 B) and was also
slower at every operation. The kit spent memory on copies, closures and
eagerly allocated containers that cost time as well, so most fixes save on
both axes. Real trades exist and are named in §4 and §5: the one in this
work moves about 45 ns into each Rip to free about 2 KB per Ripped Tag.

**This PR** (§4) lands fourteen fixes: three memory leaks, the memory
layout, the tagging path and the hot path. Memory per character falls 19
to 34 per cent; keywords, `bool(agent)` and walking a Field run 53 to 75
per cent faster; re-applying an active Form 74 per cent; tagging 12 per
cent. A differential fuzzer ran 300 random programs (560,000 transcript
lines) on both kits with no difference; targeted probes found four, all
deliberate, and each fixes a defect (§4.2).

**What is left** (§5) is structural. Sharing one Overlay per composition
instead of one per Agent would cut tagging by a further 34 to 56 per cent
and a character to about 2.8 KB, but it needs a design for when shared
structure is freed. Seven items would change what programs can observe and
are the Director's to decide as STEPs (§6).

---

## 2. What the users hit: a passing state kept as a Tag

1,000 creatures, 100 turns, one state flipped every turn:

| State | Kept as | Per loop | Per turn | vs OOP |
| --- | --- | --- | --- | --- |
| Asleep | OOP attribute | 1.03 ms | 10.3 ns | 1.0x |
| | TOP Record (the Guide) | 2.43 ms | 24.3 ns | 2.4x |
| | TOP Tag, applied and Ripped | 285 ms | 2.85 us | 278x |
| Poisoned (damage 3) | OOP attribute | 1.35 ms | 13.5 ns | 1.0x |
| | TOP Record | 4.25 ms | 42.5 ns | 3.2x |
| | TOP Tag, applied and Ripped | 376 ms | 3.76 us | 279x |
| Stunned, a `@Flag` | OOP attribute | 1.03 ms | 10.3 ns | 1.0x |
| | TOP Record | 2.61 ms | 26.1 ns | 2.5x |
| | TOP Tag, applied and Ripped | 429 ms | 4.29 us | 417x |

(Before this PR. After it the Tag rows fall 3 to 8 per cent, the Record
rows do not move: see §4.)

A tagging is the paradigm's transaction: the Form is resolved, the gate
reads the incoming Agent, every contribution is laid, Records are built,
the promise is re-checked, and the whole call rolls back if anything
refuses. That is what a role change should cost. A state that flips every
turn is not a role change.

**What would help users** (§6, item 7): a one-time diagnostic when the same
Tag is applied and Ripped on one Agent many times, pointing at the Record.
It was measured at no memory per Agent and at most 1 per cent of a cycle.

---

## 3. Memory: where a TOP character's bytes go

Bytes still alive per character (1,000 characters):

| Character | OOP | TOP before | TOP after this PR | Floor with shared structure (§5.1) |
| --- | --- | --- | --- | --- |
| 1 layer / Form of 1 Tag | 113 B | 4,345 B (38x) | 3,513 B (31x) | about 2.1 KB |
| 3 layers / Form of 3 | 129 B | 7,803 B (61x) | 5,403 B (42x) | about 2.8 KB |
| 6 layers / Form of 6 | 225 B | 13,725 B (61x) | 8,973 B (40x) | about 3.8 KB |

For reference, OOP with one `WeakSet` registry per role (what a Field
does) costs 236 / 517 / 947 B.

Where the 13.7 KB of a Form-of-6 character went, before this PR:

| Component | Bytes | Share | Paradigm or kit |
| --- | --- | --- | --- |
| Tag-bound view snapshots (a copy of the whole Overlay per Tag) | 6,120 | 42% | the Record values are paradigm (§1.7); the copies are kit |
| Field entries (a weak reference and a new closure per Tag) | 3,264 | 22% | kit |
| History-derived dicts and sets, per Agent | 1,662 | 11% | kit (identical for every Agent with the same history) |
| Empty `_State` containers, allocated eagerly | 1,032 | 7% | kit |
| One condition closure per `@Post` per Agent | 808 | 6% | kit |
| Bound Actions and instance-dict growth | about 770 | 5% | kit |

Snapshots grow with the **square** of the number of Tags (each copies
everything visible so far): 1.2 / 4.8 / 11.0 / 27.4 KB at 1 / 5 / 10 / 20
Tags.

Memory is also time. A Form-of-6 character carried 104 objects the garbage
collector tracks (OOP: 2). With 40,000 such characters alive, one full
collection took 18.4 us per character; the ambient collection at 20,000
characters took 89 ms. Fewer containers shorten every full pass in the
whole program, not only TOP's.

**Three leaks** (fixed here):

- A Tag with any `@Post`, applied and Ripped repeatedly, kept **808 B per
  turn forever** (7.9 MB after 10,000 turns): each re-binding kept the
  previous binding alive though it never called it.
- A Tag class, once applied, was **never freed** (about 5 KB each): the
  Form cache was a `WeakKeyDictionary` whose value held its own key.
- A Ripped Tag's view snapshot was **kept forever**, though a view needs
  membership and can never read it again: about 2.2 KB per Ripped Tag on
  an Agent with a long history.

---

## 4. What this PR changes

### 4.1 The fourteen changes

Checked by the spec, 216 tests (13 of them the opt-in budgets), the oracle over 60,000 transitions, the
examples, and a differential fuzzer: 300 random programs run on the old
and the new kit, transcripts compared line by line (values, errors,
warnings with file and line, output at exit), with no difference.

| # | Change | Effect (alternating runs, before -> after) |
| --- | --- | --- |
| 1 | A condition without `@Underlay` keeps no prior binding, and without inputs is a plain call | the 808 B/turn leak -> 0.5 B; part of 9 |
| 2 | The Form cache holds a Tag's Bases, never the Tag itself | dropped Tag classes are freed |
| 3 | A Rip drops the Tag's view snapshot | about -2.2 KB per Ripped Tag; **the one trade: +45 ns per Rip** (`del Tag[agent]` 473 -> 520 ns) |
| 4 | `_State` and `_Snapshot` are slotted; snapshots share one empty set | memory per character -19% / -31% / -34% (with 5) |
| 5 | A Field entry is a slotted weak reference carrying its key, one callback per Field | 461 B -> 149 B per entry, for every Tag of every character's Form |
| 6 | Re-applying an active Form returns before the rollback copies | 1.90 us -> 0.49 us (-74%) |
| 7 | `in`-seat collision checks run only when a Flag or an `in` method arrives | tagging a Form of 3: 18.3 -> 16.1 us (-12%, with 8, 10, 11) |
| 8 | The gate's scratch pass silences warnings with a per-context counter, not `catch_warnings()` | also **fixes a bug** (§4.2) |
| 9 | `bool(agent)` runs the Postcondition loop directly | 1 Post: 582 -> 244 ns (-58%) |
| 10 | Postcondition inspection is skipped when nothing is promised | part of 7 |
| 11 | Function-level imports on hot paths moved to module level (three that would cycle are cached) | part of 7 and 9 |
| 12 | Each Agent keeps its active Flags and their aliases until its Tags change; names are read live | `"Undead" in agent`: 557 -> 139 ns (-75%) |
| 13 | `bool(Tag)` / `while Enemy:` hold the members once and stop at the first sound one | 1,000 members: 21.2 -> 13.1 us (-38%) |
| 14 | `Tags(agent)` / `Outline` find leaves through the Forms, not a pairwise scan; `At_Exit` drops dead registrations as they die | `Tags` -33%, `Outline` -22% at 6 Tags; `At_Exit` O(1) instead of O(n) per call |

Walking a Field of 1,000 falls from 234 to 111 us (-53%), through 5, 9
and 11. Against OOP (one run each, TOP/OOP): keyword 55x -> 14x,
`bool(agent)` 38x -> 16x, walking a Field 29x -> 15x (a `WeakSet`: 9.4x ->
4.6x), a `@Pre` gate 146x -> 120x, building a Form of 6 102x -> 87x, a
Form-of-6 character's memory 61x -> 40x.

### 4.2 The four deliberate differences

Each fixes a defect of the old kit; each has a test.

- **A warning given once is not repeated.** The gate used
  `warnings.catch_warnings()` for its scratch pass, which resets every
  warning registry, so a once-per-place warning (the default) printed at
  every gated tagging.
- **Silencing is per thread.** Under `catch_warnings()`, a gate in one
  thread dropped the kit's warnings in another (about 15 per cent of them
  in the verification run).
- **A dropped Tag class is freed** (the leak of §3).
- **Queries asked from a finalizer at interpreter shutdown answer.**
  `bool(agent)`, `Keyword`, a condition read by name, a published Report:
  the old kit raised `ImportError` there, because they imported at call
  time. The finalizer itself still imports at call time, so teardowns at
  shutdown behave exactly as before (see §5.6).

### 4.3 Tried and taken back

The verification found three prototypes that changed what a program can
observe, and they were removed:

- **Rebuilding an Agent's dictionary after its class swap** made writes as
  fast as a plain attribute (-57%), but it can skip entries in a live loop
  over `vars(agent)`, leaves the dictionary empty for an instant (an
  interrupt there breaks a rollback), and costs time in proportion to the
  host's attributes (+135 per cent at 500).
- **Passing a bound method as an `@Underlay` base** on calls without
  arguments (-46% on a 3-layer chain) changed the base's type and name,
  its frames, and where a `stacklevel` warning is attributed.
- **A lazy `bool(Tag)`** (-90%) could disagree with `len(Tag)` when a
  Postcondition frees another member while the question runs.

Two first versions were also corrected: `At_Exit` briefly kept one entry
per Agent (the old kit runs each registration, and reaches registrations
made while the exit pass runs), and the words cache briefly held names
(now read live, so a renamed Tag answers to its new name).

---

## 5. What is left in the kit (no STEP needed; needs design)

Each was prototyped on a copy of the kit, passes the 200-test suite, and
keeps the observable semantics. They are not in this PR because they
overlap, some conflict, and the shared ones need a policy for freeing.

### 5.1 One Overlay per composition, not per Agent (the big one)

Every Agent recomputes and stores an Overlay that is identical for every
Agent with the same history. Sharing it (copy-on-write Layouts with cached
Layout x Tag transitions) measured:

| | Before | Prototype |
| --- | --- | --- |
| Tag a fresh empty Tag | 5.8 us | 2.6 us |
| Form of 3 / Form of 6 | 19.5 / 44.2 us | 9.1 / 20.8 us |
| Onto an already-tagged Agent | 7.4 us | 4.1 us |
| A `@Pre` gate that passes / refuses | 12.4 / 8.0 us | 5.2 / 3.5 us |
| Memory, Form of 3 | 8.4 KB | 2.8 KB |

**The budget it moves:** each distinct history costs about 13 to 16 KB and
about 20 us once, repaid by the second or third Agent that shares it. It
loses when histories are unique and short-lived (+13 to 23 per cent), and a
naive memo is never evicted (69.7 MB after 16,000 dead unique-history
Agents in one prototype). A bounded, weakly held design kept retention flat
(about 200 KB). **Needs:** a freeing policy and a decision on how diverse
real compositions are; the examples are too small to tell.

### 5.2 A compiled plan per (composition, Tag)

The declarations are interpreted at every tagging. Compiled once, a Form of
6 builds in 9 us (OOP: 0.43 us). About 1.5 us per Tag is the floor the
transaction allows.

### 5.3 Rollback by undo log, not by copying the whole state

Every tagging copies the whole state and namespace in case it must roll
back: 1.25 to 1.58 us per call. An undo record costs 0.25 to 0.31 us. What
the call boundary itself forces is 0.49 to 0.65 us.

### 5.4 The hot path: Actions and attribute reads

- **`@Underlay` chain: 7x `super()`.** Each layer builds a forwarding
  closure on every call. An exact cheaper form must still be a Python
  function (a bound method changes frames and warning attribution, §4.3).
- **Action call: 8x a method.** A bound Action is a Python object with a
  `__call__`, stored in every Agent's dictionary, holding the Agent weakly
  (so Fields stay honest). A shim per Action function measured 116 -> 31
  ns, but was generated with `exec` and retained memory under churn. Putting
  Actions on the shared runtime type would make them ordinary methods, and
  depends on 5.1.
- **Record read: 2.7x an attribute; writes equal.** After an Agent's class is swapped,
  CPython 3.14 stops specializing reads on it (16 ns even with no hooks on
  the type; an instance born in the type reads in 8 ns). Priming the type's
  shared keys with a probe instance recovered 7.5 ns, but it relies on
  CPython internals and returns at call sites that see several runtime
  types. Not for a reference kit; worth knowing.
- **A finalizer on every Agent** (about 560 ns at each death) is needed only
  when a teardown waits or the host has its own; it is part of the type key.

### 5.5 Fields

One weak reference per Agent for all its Fields (82 B per membership instead
of about 470); a Field whose population collapsed keeps its peak table
(5.25 MB after 100,000 deaths, a 10-member walk at 26 us instead of 2.5):
compact when it shrinks.

### 5.6 Smaller items

A dunder Action with `@Underlay` creates a runtime type per Agent (3.35 us,
1.57 KB each); a Record's input binding is re-derived per Agent (-0.16 us
per Record); the `@Secret` door costs about 225 ns per Action call that
reads a secret; the runtime-type key is recomputed when no type-level fact
changed (-0.4 to -0.96 us); defining a Tag costs 5.0 us against 2.3 us for
a plain class; importing TopKit takes 8 to 13 ms, 4 of them in
`dataclasses`, `inspect` and `typing`.

**Found, not changed:** at interpreter shutdown, an Agent's finalizer
cannot import the teardown runner, so neither its `@Rip` teardowns nor the
host's own `__del__` run (Agents registered with `At_Exit` are torn down
by the exit pass). The spec does not promise finalizers at shutdown, but
suppressing the host's own `__del__` is a host-preservation question. It
was kept exactly as it was.

---

## 6. What only a STEP can change (the Director's decisions)

The spec forces these costs. Each could shrink only by changing what a
program can observe.

| # | Cost the spec forces | Measured | Option | Verdict of the analysis |
| --- | --- | --- | --- | --- |
| 1 | **Re-applying a Tag after a Rip stacks its `@Underlay` on its own sticky Layer**, without bound | after 200 cycles a call takes 66 us; each cycle keeps 0.5 to 0.8 KB | re-application replaces its own earlier Layer | **the one to decide first**: it reads as a defect, and it also makes the misuse of §2 grow |
| 2 | Tag-bound views capture Record values at every Tag (§1.7) | 1.27 KB per Form-6 character; 0.3 to 0.85 us per Tag | views capture which contributions were visible, and read current values | a real simplification if views are rarely used |
| 3 | Every earlier promise is re-checked at each tagging boundary (§2.4) | about 300 ns per visible Post per tagging | check only the arriving Tag's promises | the contract model depends on it; keep |
| 4 | The class swap that the native spellings need (§0.8) | reads 2.7x, method calls 3x on every Agent | Agents that need no hook keep their class | large win, large change |
| 5 | Caching a Post's verdict | not exact: moves 22 -> 99 ns onto every write | none | reject |
| 6 | `Apply(agent, A, B, C)` is three call boundaries | about -1.8 us for 3 Tags | one boundary for the whole call | small |
| 7 | Nothing warns about Tags used as Records | the misuse of §2 | a one-time diagnostic after many apply/Rip cycles on one Agent | cheap and aimed at the actual complaint |

A "no-rollback fast apply" was also measured: it would buy about 10 per
cent of a cycle, not worth a STEP.

---

## 7. Floors: what TOP will always cost

- A tagging is a transaction: about 1 to 1.5 us per Tag after every kit
  fix, against 55 to 85 ns per class layer in OOP. Build once, play long.
- A passing state kept as a Tag: about 1 us per flip at best, against about
  25 ns as a Record.
- A Field that never keeps an Agent alive walks slower than a list (weak
  references); after this PR it is 14.5x a list and 4.9x a `WeakSet`.

---

## 8. Suggested order of work

1. **Merge this PR** (§4): leaks fixed, four defects fixed, no other
   behaviour changed, the benchmark and opt-in budgets in place.
2. **Decide §6 item 1** (Underlay growth on re-application) and **item 7**
   (the diagnostic): both are cheap, and together they answer the reported
   complaint directly.
3. **Design §5.1** (shared Overlay per composition) with a freeing policy,
   then §5.2 and §5.3 on top of it; that is where the remaining factor of
   two in tagging and memory is.
4. Revisit §6 items 2 and 4 with usage data: how often programs read
   Tag-bound views, and how many Agents need no hook at all.

---

## Reproducing

- `PYTHONPATH=. python3 benchmarks/compare.py`: every scenario written as
  OOP and as TOP, checked equal before timing, then timed; memory in a
  separate traced pass.
- `TOPKIT_PERF=1 PYTHONPATH=. python3 -m unittest tests.test_performance`:
  ratio budgets against the OOP equivalent (opt-in; timing depends on the
  machine).
- `PYTHONPATH=. python3 benchmarks/bench.py`: the kit's own hot path and
  population figures.
