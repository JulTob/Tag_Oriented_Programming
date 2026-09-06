# Changelog

## 0.2.0a3 — 2026-09-06

### Specification

- **Pins: Tags as Targets** (STEP-SPEC-9, §1.9). A Tag marked `@Pin`
  applies to Tags and to nothing else; the pinned Tag is its Agent. The
  receiver rule of STEP-SPEC-1 lands a Pin's Records as Reports and its
  Actions as Operations of the pinned Tag, never on the Tag's Agents.
  Every Tag-level act applies with a Tag in the Agent's seat:
  `Rare(Wizard)`, `Wizard in Rare`, `for tag in Rare`, `Rare[Wizard]`,
  `del Rare[Wizard]`, `f"{Wizard:pins}"`, `f"{Wizard:contract}"`.
  Fields never mix Agents and Tags. A Pin adds to a Tag and never replaces
  what the Tag declares; a Pin's members are plain (no `@Secret`,
  `@Public`, `@Delete`, special methods); a Pin cannot be a Flag.
- Re-applying a Ripped Tag is a fresh Tagging and silent (§0.7): a Tag
  replacing its own earlier Postcondition is not a Shape weakening a Base.

### TagKit

- `Pin` mark; the tagging sequence runs unchanged on a Tag as Target
  through a small adapter over the class dictionary; the runtime type of
  a pinned Tag is a `(MetaTag, Tagged)` metaclass; landed Actions bind to
  the Tag they are read from, landed Records are class attributes; the
  Tag's own scan skips TOP-managed names.
- Fixed: `TagContractWarning` on re-applying a Ripped Tag that declares a
  Postcondition; `__bool__` installed over a host's own `__bool__` (the
  empty-seat rule now holds for it, as the notes said).
- Faster `agent in Tag`: the state read goes straight to the dictionary.
- 106 tests.

## 0.2.0a2 — 2026-09-04

A rewrite of TagKit on the review of 2026-09-04, and the Specification
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

### TagKit

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
  `TagDeletionError`, `Tag.Field`, `Tag.Rip(agent)`, `TagKit/TagKit.py`.

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
