# Changelog

## Unreleased

### Specification

- STEP-SPEC-22 (Links) opened at Brief, and was revised after three
  reviews by the Director. `@Link` grants each Agent a Tag of its own,
  `charlie.Knows`, held like a Record.
  - A Link is a Tag in full: Records, Actions, promises, secrets, Bases
    and Shapes. What an ordinary Tag gives its Agent, a Link gives the
    Pair.
  - The functions it declares for the Pair take the Agent first and the
    Contact second: the Agent has the agency.
  - A Link points one way: nothing on a Contact names an Agent who links
    her.
  - Linking makes the Contact a member and writes no Record, Action or
    promise on her, except members the Relation marks `@Public`: those
    are published onto her as one line to the Pair, with no fan-out.
    `@Secret` members stay in-house, the Link's Agent's alone. Facts
    about the two live on the Pair, `charlie.Knows[ruth].since`.
- STEP-SPEC-23 (Field Filters) opened at Brief. A Projection reads one
  name across a population, `Wizard[:].level`; comparing it gives a
  Filter, a live population. Decided by the Director on 2026-10-09: the
  dot on a Tag reads only the Tag ("Wizard.level is a report"), so the
  first draft's `Wizard.level > 3` gives way and the root for the sound
  members moves to STEP-SPEC-29. Decided on 2026-10-08: a member with no
  value is like SQL's `NULL` (`== None`), and a Filter refuses `bool()`.
  - Chains fan out with "some": `Social.Knows[:] == ruth`.
  - A Filter by an Action's result follows a changing system.
  - This is the logic of classes and attributes of Boole and Carroll, in
    the language's own operators.
- STEP-SPEC-24 (Field Rip and the End of a Tag) opened at Brief.
  `del Wizard[:]` Rips the whole Field. A Tag that ceases to exist does
  the same, so its members' teardowns run. Membership holds neither side
  alive.
- The three were first drafted as STEP-SPEC-19, 20 and 21, and
  renumbered because other open work claims those numbers.
- STEP-SPEC-26 (A Shape Keeps No Base Hostage) opened at Brief, with
  the model the Director chose: tagging stays closed upward, then each
  membership stands alone. Under it, `del Human[bob]` would no longer
  be refused while bob is a Werewolf; he would keep the Shape, a
  spin-off. The kit still refuses it today. A Shape that needs its Base
  says so in a guarded Postcondition.
- STEP-SPEC-27 (The Deletion Protocol of a Tag; opened as "Emergency
  Stop") at Brief, revised on 2026-10-09 after the Director's
  correction. It reads `del Human[:]` (STEP-SPEC-24) in three phases:
  gain control (every membership ends at once), stop gently (teardowns
  run one member at a time, in join order), and then the Tag is ready
  again, "the power is still on". `del Human` stays Python's act. It
  proposes `del Human.colour` to reset one Report. The first draft's
  latch, the Pin `Stopped`, is withdrawn.
- STEP-SPEC-28 (Category Error) opened at Brief. `TagCategoryError`, a
  `TagError` and a `TypeError`, names the mistake of treating one kind of
  TOP thing as another, such as `Wizard.hp = 10` when `hp` is a Record.
- Guide: "Reading a Tag" shows Python's `all` and `any` with a question
  written inside, `all(w.level > 3 for w in Wizard)`, and why
  `all(Wizard)` alone does not ask whether there are Wizards.
- STEP-SPEC-30 (Retire `@Requirement`) opened at Brief: a claim needed
  to enter and to stay is written `@Pre` + `@Post`, stacked, as the
  Director asked.
- STEP-SPEC-29 (The Population Algebra) opened at Brief: one place for
  every population spelling, as the Director asked ("We need to unify
  all the design of sets and filters"). It records his rulings of
  2026-10-09 (`ari in Wizard` is sound membership; `if ari:` asks the
  promises; `Wizard[...]` and `Tag[...]` are the safehouse; `Rare |
  Wizard` is a category error; `del (~Wizard)[:]` Rips every broken
  Wizard). It recommends `+Wizard` for the sound part before a dot,
  `Wizard[0]` in join order, an absorbing `~` (awaiting his answer) and
  a `rounds` recipe.
- STEP-SPEC-31 (Retire `Scope`) opened at Brief, as the Director
  decided ("TOP should integrate with the language … Get it out"). A
  block that holds a Tag for a while tags the Agent before `try` and
  Rips it in `finally`. STEP-SPEC-22, 24, 26 and 28 and the catalog no
  longer lean on `Scope`. The kit keeps it until the STEP is built.
- A catalog of the Tag algebra, `steps/CATALOG-tag-algebra.md`: every
  spelling found so far that reads or acts on a Tag or a population, with
  its meaning, its result and its status on each branch.

### TopKit

- A Field no longer has public `Add` and `Remove` methods. They were the
  kit's own halves of commit and Rip, and calling them by hand skipped
  the gate or the teardowns and left the Field contradicting `in`. They
  are private now, and membership changes only by tagging and Rip.
- New failure: `TagCategoryError` (STEP-SPEC-28), for an act that treats
  one kind of TOP thing as another. It is a `TagError` and a
  `TypeError`, so code that catches `TypeError` keeps working. Nothing
  changes when it is raised, and its message names the spelling to use.
- `Wizard.hp = 10` and `del Wizard.hp` are refused when `hp` is a name
  the Tag gives its Agents: a Record, an Action, a condition, an Imprint
  or a deletion, declared on the Tag or on a Base. Before, the write
  passed in silence: before the Tag's first use it erased the
  declaration, and after it the Tag and its Agents disagreed. The message
  names the loop, `for wizard in Wizard: wizard.hp = 10`. A Report beside
  a Record of the same name, and any name the Tag does not give its
  Agents, stay writable.
- A target that cannot be an Agent is refused at tagging with a
  `TagCategoryError`: `Wizard(None)`, `Wizard(3)`, `Wizard(True)`, any
  value with no instance dictionary or no weak reference (before, a
  `TagCompositionError`), an instance of a `str` subclass, and a host
  whose class defines its own `__bool__` (both tagged before). A host
  with only `__len__` is still accepted.
- A Flag on a host that answers `in` itself (its own `__contains__` or
  `__iter__`) is refused with a `TagCategoryError` instead of a
  `TagCompositionError`. The message is unchanged. A collision with a
  Tag's Action that answers `in` stays a `TagCompositionError`.
- A Pin's population no longer combines with a Tag's: `Rare | Wizard`,
  `Wizard & Rare` and `Rare[:] - Wizard` raise a `TagCategoryError`.
  Pins combine with Pins, and Tags with Tags; `Wizard | None` is still
  Python's type union.
- A walk skips a member that an earlier turn of the same walk Ripped
  (STEP-SPEC-29, rule 7.1), on every population: a Tag, `Wizard[:]`,
  `~Wizard`, a Pin and every combination. Before, the walk visited it.
  An Agent that joins during a walk still waits for the next one, and
  each side of a combination is still read when its own walk begins.

### Project

- **Releases go out through Trusted Publishing.** A GitHub Release runs
  `.github/workflows/release.yml`: the suite on Python 3.12, 3.13 and
  3.14, the oracle at its audited size, a check that the tag names
  `pyproject.toml`'s version and the changelog has it, the build and
  `twine check`; the upload then waits for the Director's approval.
  PyPI trusts the workflow, so there is no token to keep or leak: each
  run gets one that expires within minutes. `RELEASING.md` gives the
  steps, and keeps the upload by hand for when GitHub cannot do it.

## 0.2.0a4 — 2026-10-02

### Specification

- **Deletion in Layers** (STEP-SPEC-18, §3.2): an Agent's `__del__` is a
  member of its Overlay. The host's own is the first Layer; a Tag's
  `__del__` replaces or, with `@Underlay`, extends it; `@Delete` removes
  it. Deletion runs the teardowns first, then the `__del__` Layers; a
  `__del__` never stops a teardown; at interpreter exit only the Layers
  run; `@Rip` on `__del__` is refused. Before, a tagged object's own
  `__del__` did not run at exit unless a Tag's `@Underlay __del__` sat
  over it, a host's `__del__` error was swallowed, and a Tag's `__del__`
  (or `@Delete` of it) silently stopped the teardowns. Teardowns of Agents
  collected as cyclic garbage at exit no longer run; `At_Exit` runs them.
- **Fixed with it:** an object built from an Agent's runtime type
  (`dataclasses.replace`, `type(self)(...)`) is tagged as a plain host
  (a `__del__` Layer used to recurse, and type-level gates of the other
  Agent leaked in); a host class that subclasses `Tagged` gets its
  runtime type at the first tagging (before, it kept its own class until
  a Tag brought a type-level fact, and until then had no finalizer, so no
  teardowns at deletion, no views or conditions by name, and no format
  specs; one that cannot be subclassed is now refused, as any such host
  is); teardowns run by the finalizer or the exit pass run inside the
  composition door, so they read their own `@Secret` members; the
  finalizer works late in interpreter exit, after the kit's modules are
  cleared, and reads the Agent as Python does (never through the host's
  own `__getattribute__`).
- **Fixed:** a tagging refused inside an Action, a teardown or a
  `__del__` Layer (rolled back) left the composition door open, so the
  Agent's `@Secret` members stayed readable from outside. A rollback now
  restores the state in place and keeps the counters of open doors.
- STEP-SPEC-12 **Cleared** by the Director on 2026-09-21: conditions are
  sticky; the author ends them. Deployed with the merge that carried it.
- **Field algebra** (STEP-SPEC-13, §2.5): `Wizard | Fighter`, `Wizard &
  Fighter`, `Wizard - Sworn`, on whole Fields, sound views and defective
  views alike, lazily and in application order. A Tag in an operator seat
  is its sound population. Back from the 0.2-alpha line, reviewed and
  accepted by the Director.
- **A condition is read on the Agent by its name** (STEP-SPEC-14, §2.5):
  `agent.Has_Book` is a plain boolean computed on read, never stored,
  never a proxy. A condition's name is refused to Actions, Records, host
  members and values the Agent already holds. Back from the 0.2-alpha
  line in the form the Director chose.
- **Scope Rips what it applied, and only that** (§0.7): a Tag the Agent
  already carried survives a Scope; a Tag that broke its promise at the
  Scope's door is Ripped on exit. Both found by the oracle.
- STEP-SPEC-15 (Trials, the recoverable phase the archived checkpoints
  were) and STEP-SPEC-16 (uniform access) opened at Brief with the full
  case for the Director's review.
- **STEP-SPEC-7 amended** (§1.8): one seat, one meaning. A Flag is
  refused on a host whose `in` comes from `__iter__` as well as
  `__contains__`, and a Flag and a Tag's `__contains__`/`__iter__` Action
  collide in either order. Each refusal names both sides. `__contains__
  = None` frees the seat, as Python reads it; `__getitem__` alone is not
  a seat. Before, `"alice" in party` flipped from True to False in
  silence when a Flag landed.
- **A Flag's words** (STEP-SPEC-17, §1.8): `@Flag("Wolf", "Lycanthrope")`
  makes a Tag answer to those words as well as to its name, `"Wolf" in
  howler`. A word is a keyword, never membership; many Tags may share
  one; a Shape answers its Base's words through the Base. Bare `@Flag` is
  unchanged.

### TopKit

- **Performance** (`PERFORMANCE-2026-09-24.md`; figures from an Apple
  M5 with CPython 3.14, and other machines differ: on Linux with CPython
  3.13 a reviewer measured the passing-state misuse at 248 to 363 times a
  plain attribute where the M5 gave 280 to 420, and a Record at 1.4 to 1.6
  times where the M5 gave 2.4 to 3). Three leaks fixed: a
  re-applied Tag with a `@Post` kept 808 B per turn; an applied Tag class
  was never freed; a Ripped Tag's view snapshot was kept forever. Memory
  per character falls 19 / 31 / 34 per cent for a Form of 1 / 3 / 6 Tags;
  keywords, `bool(agent)` and walking a Field run 53 to 75 per cent
  faster; re-applying an active Form 74 per cent; tagging 12 per cent;
  `bool(Tag)` 38 per cent; `At_Exit` is O(1). A Rip costs about 45 ns
  more, to free the snapshot.
- **Fixed:** a gated tagging reset every warning registry (it used
  `warnings.catch_warnings()`), so a once-per-place warning printed at
  every such tagging; and a gate in one thread silenced the kit's
  warnings in another.
- Queries asked from a finalizer during interpreter shutdown (`bool(agent)`,
  `Keyword`, a condition by name, a published Report) now answer instead of
  raising `ImportError`. (A published Report read for the first time at
  shutdown still raised it until the review follow-up: `overlay` now hands
  its membership check to `state` when it loads.)
- Review follow-up: tests for the two deliberate differences that had
  none (per-thread warning silencing, queries at shutdown); tests that
  read the kit's internals now test what a program can observe; the
  one-item-list caches became plain module variables, and an Agent's
  gathered Flag words a named tuple.
- `benchmarks/compare.py` sets TOP beside the same behaviour in plain
  OOP, in time and in memory, including the misuse of keeping a passing
  state as a Tag; `tests/test_performance.py` holds opt-in ratio budgets
  (`TOPKIT_PERF=1`); `benchmarks/bench.py` no longer times tagging under
  tracemalloc. Both time the same scenarios, from `benchmarks/scenarios.py`.
- The **differential fuzzer**: `tests/differential_fuzz.py` runs the same
  random programs on two versions of the kit (git refs or the working
  tree) and compares the transcripts line by line, output at exit
  included. Run on the kit before and after the performance work, it
  found no change in behaviour but the deliberate ones. A short run is
  in the suite.
- **Fixed:** a Flag applied to an Agent that already carried another Tag
  did not take the Agent's `in`, so `"Undead" in ghoul` raised
  `TypeError` (`Keyword()` was unaffected). The runtime type is now
  rebuilt when a Flag lands.
- **Fixed:** a name a Tag `@Delete`d and a later Layer stored again lost
  its gate whenever the runtime type was rebuilt (by a Postcondition,
  another deletion, a dunder Action, now a Flag), so a host property of
  that name came back over the Layer's Action. The gate now survives.
- A `str` subclass asked for a keyword is read as its text: matching
  stays exact, and an unhashable subclass no longer raises.
- The **oracle**: `tests/oracle_topkit.py`, an independent model of the
  paradigm checked against the kit after every transition of a random
  walk (60,000 transitions at the audited size), ported from the
  0.2-alpha line and extended with sticky conditions, published members,
  condition members, Field algebra, Pins and keywords (names, shared
  words, a word naming another Flag, words through the Form). A short
  walk runs under the suite.
- **The Fields Guide** (`TopKit/FIELDS.md`): populations, partitions and
  the algebra, with the battle loop, the roster of the missing, the
  repair queue across roles and a gate that reads a population.
- The three document smoke runners are now `tests/test_documents.py`.

### Project

- **TopKit needs Python 3.12 or later** (0.2.0a3 said 3.10). This release
  was checked on CPython 3.12 and 3.14; 3.10 and 3.11 were never run.
- STEP-SPEC-13, 14, 17 and 18 ship at Vetting, as STEP-SPEC-12 did with
  0.2.0a3. The Director's rulings of 29 September on them (a Tag answers
  `in` for its sound members, names on an Agent change kind freely, the
  deletion amendments, the Flag fixes) come in a later release.
- `RELEASING.md` now records the whole path to PyPI, from the account
  and the token to the virtual environment, as the first release ran it.
- The README, which is the PyPI page, starts with `pip install topkit`
  and links to GitHub with absolute links, so they work on PyPI; a plain
  `pip install topkit` installs the newest alpha while no final release
  exists.

## 0.2.0a3 — 2026-09-06

**Released on PyPI on 2026-09-21**: https://pypi.org/project/topkit/0.2.0a3/.
The name `topkit` is claimed. The release is main at the merge of pull
request #6, which carries STEP-SPEC-12 and the Redaction of STEP-SPEC-11.


**TagKit is now TopKit.** The distribution is `topkit`, the module is
`TopKit`; the T is the Tag in T.O.P. The name `tagkit` on PyPI belongs to
an unrelated project.

### Specification

- **Pins: Tags as Targets** (STEP-SPEC-9, §1.9). A Tag marked `@Pin`
  applies to Tags and to nothing else; the pinned Tag is its Agent. The
  receiver rule of STEP-SPEC-1 lands a Pin's Records as Reports and its
  Actions as Operations of the pinned Tag, never on the Tag's Agents.
  Every Tag-level act applies with a Tag in the Agent's seat:
  `Rare(Wizard)`, `Wizard in Rare`, `for tag in Rare`, `Rare[Wizard]`,
  `del Rare[Wizard]`, `f"{Wizard:pins}"`, `f"{Wizard:contract}"`.
  Fields never mix Agents and Tags. The pinned Tag's own Operations and
  Reports are host members to a Pin (Underlay and stored seat: a patch
  reaches every Agent at once); its Agent-scope members and protocols are
  refused at the gate. `@Secret` on a Pin member is Pin-private state on
  the Tag; `@Public` publishes it onto the Tag's Field, present and future
  Agents. A Ripped Pin is sticky; its `@Rip` teardown may take a second
  seat and receives the originals, so un-patching is `tag.Control =
  original.Control`. A Pin may be a Flag: `"Deprecated" in Wizard`.
- **Published members answer members only, and only sound ones**
  (STEP-SPEC-10, §1.5). A Rogue Agent gets a Rogue Access Failure, a TOP
  failure and nothing else; a defective Agent gets the broken promise by
  name, whichever Tag made it, and repairs it: the autofix pattern. The
  Agent's own Actions and Records are untouched.
- `@Pre` and `@Post` stacked on one function are one condition: necessary
  to enter and necessary to stay, spelled `@Requirement` in one word
  (§2.7).
- **Conditions are sticky; the author ends them** (STEP-SPEC-12, §0.7).
  Rip does not touch a Tag's gates or promises. A condition ends by a
  guard in its own body (`if agent not in Wizard: return True`) or by an
  explicit `Contract.Delete(agent, "Has_Book")` from the Tag's `@Rip`
  protocol. STEP-SPEC-11, which made Rip remove conditions and restore
  the prior one, is Redacted: "Rip protocols can be dangerous."
- **The Contracts Guide** (`TopKit/CONTRACTS.md`): gates, promises,
  membership and error control, aboard a starship; every block runs.
- Re-applying a Ripped Tag is a fresh Tagging and silent (§0.7): a Tag
  replacing its own earlier Postcondition is not a Shape weakening a Base.

### TopKit

- `Pin` mark; the tagging sequence runs unchanged on a Tag as Target
  through a small adapter over the class dictionary; the runtime type of
  a pinned Tag is a `(MetaTag, Tagged)` metaclass without descriptors;
  landed Actions bind to the Tag they are read from, landed Records are
  class attributes; secrets live in the Tag's state and answer on the
  miss path; `@Public` pinned members reach present Agents at pinning
  (checked on copies first) and future Agents through the Tag's scan;
  the Tag's own scan skips TOP-managed names.
- `Contract.Delete(agent, *names)`: end conditions explicitly; a name
  that is not a condition on the Agent is a `TagResolutionError`.
- Published Operations and Reports check sound membership at use;
  `TagRogueAccessError`, which is a `TagResolutionError` and deliberately
  not an `AttributeError`.
- `Requirement`: one mark for `@Pre` + `@Post`. It names no failure of
  its own and says which of the two to catch.
- A string in a Tag's `in` asks for a keyword; `__contains__` and
  `__bool__` follow the empty-seat rule.
- Fixed: `TagContractWarning` on re-applying a Ripped Tag that declares a
  Postcondition; `__bool__` installed over a host's own `__bool__` (the
  empty-seat rule now holds for it, as the notes said).
- Faster `agent in Tag`: the state read goes straight to the dictionary.

### Project

- STEP-SPEC-9 and STEP-SPEC-10 **Cleared** by the Director on 2026-09-16.
- Two examples of design patterns, each self-checking and run by the test
  suite (`tests/test_examples.py`): `examples/fleet_patching.py` (Pins: a
  hot-fix across a fleet with rollback, a catalog of facts and keywords
  read by a Tag's own gate, a registry that validates its entries, a
  policy published onto a Field) and `examples/crew_access.py`
  (published members: roles as membership, a repair table keyed by named
  promises, quarantine through holistic soundness, stale handles refused
  at run time, `@Requirement`, and the author's own guard: a condition
  that follows another Tag's membership, a keyword on a Tag, or the Tag
  under its Underlay, in one line of flow control). The Contracts Guide
  gains the same guards as §8.
- [`RELEASING.md`](RELEASING.md): what a release checks and how `topkit`
  is claimed on PyPI. The name is free; the first upload reserves it.
- 127 tests.

## 0.2.0a2 — 2026-09-04

A rewrite of TopKit on the review of 2026-09-04, and the Specification
rewritten in rings. Every change below is either a fix of a defect the
review reproduced, or a decision recorded in a STEP.

### Specification

- Rewritten in rings (kernel → contributions → contracts → lifecycle →
  edges); duplicated sections merged; identity defined (STEP-SPEC-6).
- Rip never cascades; three deletion tiers; Preconditions gate only the
  current call; host behaviour preserved (STEP-SPEC-6).
- Two scopes and one slot per `(scope, name)` (STEP-SPEC-1, Deployed).
- Publication: `@Secret`, `Public(...)`, the composition door (STEP-SPEC-3).
- Defective taggings: Postconditions once per call after the whole Form;
  failed Post or Imprint leaves the Tags; the plain loop is the sound
  population, `~Tag` the defective one, `Tag[:]` everyone; `bool(agent)`
  (STEP-SPEC-4).
- Native spellings for every Tag-level act; the Tag's dotted namespace
  belongs to the program (§0.8): `del Tag[agent]` Rips, `Form(Tag)` is a
  function, `if Tag:` asks for a sound member, and format specs are the
  display door (`f"{Tag:form}"`,
  `f"{agent:tags}"`, `f"{agent:outline}"`, `f"{agent:contract}"`).
- Records receive the stored value and pile up (STEP-SPEC-5).
- A failed check raises a failure that carries the check's name, as a
  subclass: `except Precondition.Is_A_Caster:` (§2.6, STEP-SPEC-8).
- Record builders receive application inputs by name after the Agent and
  the stored value: `def code(agent, *, code)` keeps the input; a stored
  parameter named like an input is refused loudly (STEP-SPEC-5 §6).
- Reports are declared like Records: `@Report def hit_die(tag): ...`, built
  once per Tag on first read, with an optional second parameter receiving
  the Bases' value. `@Secret` / `@Public` are modifiers that stack in either
  order; redundant modifiers are accepted, contradictory ones rejected
  (STEP-SPEC-3 §6).
- Flags: `@Flag` marks a Tag as a keyword, searchable from the Agent's
  side by name or class, `"Undead" in ghoul`; `Keyword(agent, ...)` is the
  function form; refused on container hosts (STEP-SPEC-7).

### TopKit

- Split into eleven modules, one idea each.
- Attribute reads and Action calls at plain-object cost: no
  `__getattribute__` override, bound Actions in the instance dictionary,
  neutral runtime types shared across compositions.
- Fixed: host `__contains__` / `__bool__` / `__or__` / `__getattr__`
  shadowed after tagging; Reports, Operations and Tag helpers leaking onto
  the Agent; Preconditions with inputs re-running on later taggings;
  `@Rip @Underlay` teardown crashing; raw `AttributeError` / `TypeError`
  from Record failures; O(n²) Field registration; unbounded `At_Exit`
  registry; stale runtime type after Rip.
- Added: `Secret`, `Public`, `~Tag`, `Tag[:]`, `Tag[agent]`,
  `del Tag[agent]`, `len(Tag)`, `bool(Tag)`, `Flag`, `Keyword`, format
  specs, `Form`, `Contract.Holds`, `Apply`, `Tags`, `Outline`,
  named failures (`Precondition.X`, `Postcondition.X`, `Imprint.X`,
  `error.name`),
  `TagDeclarationError`, teardown failure reporting, explicit refusal of
  `copy.copy`, protocol parameter defaults honoured.
- Removed: Agent sugar (`With`, `As`, `|`, `ApplyTags`, `agent.Tag(...)`,
  `Has`/`Tags` methods, `TagPaths`, `TagTree`, `Outline` method), `NAME`,
  `DESCRIPTION`, `ABSTRACT`, `Label`, `Describe`, `Lineage`, `Path`,
  `TagDeletionError`, `Tag.Field`, `Tag.Rip(agent)`, `TopKit/TopKit.py`.

### Migration from 0.1

- `@Record @Underlay def r(agent, underlay): underlay()` →
  `def r(agent, stored): stored` (a value, `None` when nothing is stored).
- A failed Postcondition no longer rolls back: check `bool(agent)` or Rip.
- `agent.Tag(X)` → `X[agent]`; `agent.Tags()` → `Tags(agent)`;
  `agent.Has(X)` → `agent in X`; `"X" in agent` → mark `X` with `@Flag`;
  `agent.Outline()` → `Outline(agent)`.
- `name = Report(value)` → `@Report def name(tag): return value`.
- `Tag.Lineage()` → `Form(Tag)`; `Tag.Rip(agent)` → `del Tag[agent]`;
  `Tag.Field` → `Tag[:]`; `for a in Tag` now yields sound members only.
