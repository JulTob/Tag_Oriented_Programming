# Changelog

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
  function, `if Tag:` asks for a sound member, `Tag in agent` and
  `"Tag" in agent` read membership from the Agent's side on the empty-seat
  rule, and format specs are the display door (`f"{Tag:form}"`,
  `f"{agent:tags}"`, `f"{agent:outline}"`, `f"{agent:contract}"`).
- Records receive the stored value and pile up (STEP-SPEC-5).

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
  `del Tag[agent]`, `len(Tag)`, `bool(Tag)`, `Tag in agent`,
  `"Tag" in agent`, `Has` with names, format specs, `Form`, `Contract.Holds`, `Apply`, `Has`, `Tags`, `Outline`,
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
  `agent.Has(X)` → `Has(agent, X)`; `agent.Outline()` → `Outline(agent)`.
- `Tag.Lineage()` → `Form(Tag)`; `Tag.Rip(agent)` → `del Tag[agent]`;
  `Tag.Field` → `Tag[:]`; `for a in Tag` now yields sound members only.
