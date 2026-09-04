# Changelog

TagKit follows semantic versioning while its Python surface evolves.

## 0.2.0a1 — 2026-08-05

This alpha establishes the modular TagKit runtime and the current Python
profile of TOP.

### Added

- [`TagKit/PYTHON_PROFILE.md`](TagKit/PYTHON_PROFILE.md) — TagKit utilities beside the
  normative Specification.
- STEP-SPEC-2 draft: Tag members composition-internal at runtime (Brief).
- Procedural `Apply`, `Has`, and `Tags` queries.
- Tag Fields through `Tag[:]` and Agent-bound views through `Tag[agent]`.
- Geometry, Forms, Overlays, and explicit Underlays.
- Pins for applying Tags to Tags.
- Atomic Tagging with rollback of TOP state and supported host mutations.
- Recoverable multi-Tag design phases through `Tag.Checkpoint(target)`.
- `Scope` and `At_Exit` lifecycle helpers.
- Typed contribution decorators and a `py.typed` marker.
- Deterministic state-machine and capacity stress suites.
- Manifesto, technical Specification, TagKit Guide, and Pin Guide.

### Changed

- Merge STEP-SPEC-1 into the Specification: contribution scope follows the
  receiver, access law, contract phases, central Actions, and no implicit
  Operation projection.
- The implementation is divided into cohesive internal modules. Application
  imports remain rooted at `TagKit`.
- Active reapplication is a strict no-op.
- Reports are ordinary public data declared by the program on a Tag.
- Python naming and documentation use `__name__`, `__doc__`, `str`, and
  `repr`.
- Structural runtime protocols are reserved for TagKit and the host object.
- Nested Tagging of the same Target is allowed from an Imprint. Those Tags
  are ordinary later calls after the outer Tag has applied. A nested
  Precondition rolls back only the nested Tag. An Imprint failure raises
  `ImprintingError` and leaves the outer Tag in place. A Postcondition
  failure raises `TagPostconditionError` and leaves the Tag as a defective
  result. Rip remains forbidden while an Imprint is running. Preconditions
  and Records still cannot Tag or Rip the Target while Tagging is
  provisional.
- A Shape may Overlay a Base Action with a Record, or a Base Record with
  an Action. Independent Tags still cannot share one Agent name as both
  kinds.
- Agent Actions and Records share both access spellings. `agent.hp` and
  `agent.hp()` read the same Record. A nullary Action may be read without
  `()`. An Action that needs inputs remains a handle until it is called.
- `Tag[:]` iterates sound Field members whose visible Postconditions hold.
  `~Tag[:]` is the defective complement. `Tag[:] | ~Tag[:]` is the U-set for
  that Tag.
- Preconditions gate only the layers applied in the current call. Visible
  Postconditions re-check at every Tagging boundary.
- Visible Preconditions and Postconditions are binary Agent members
  (``agent.Has_Spellbook`` / ``agent.Has_Spellbook()``). ``TagPreconditionError``
  and ``TagPostconditionError`` expose ``.condition`` and named subtypes such as
  ``TagPostconditionError.Has_Spellbook``. Conditions cannot share an Agent name
  with an Action or Record. ``f"{agent:Contract}"`` / ``f"{agent:Display}"``
  render the contract mini menu.

### Removed

- Built-in application Reports such as `NAME`, `DESCRIPTION`, and `ABSTRACT`.
- Tag convenience methods `Label()` and `Describe()`.
- Implicit Underlays inferred from a parameter named `underlay`.

### Migration from 0.1

- Replace `tag.Label()` with `tag.__name__` for Python identity, or declare an
  explicit domain Report for a display label.
- Replace Tag-contributed `__contains__` string probes with Tag membership and
  `Has( agent, ... )`.
- Replace application reads of TagKit private state with `Tags`, `Has`,
  Fields, or Agent-bound Tag views.
- Apply optional or later layers from an Imprint. Express required, more
  general meaning through Bases and Shapes. Preconditions, Records, and
  Postconditions still must not apply Tags; perform those after the current
  Tagging commits, or from an Imprint.
- Define cloning and serialization in the application domain. Do not copy
  `_TAGKIT_STATE`.

The complete Python behavior is documented in
[`TagKit/GUIDE.md`](TagKit/GUIDE.md). Observable paradigm semantics remain
defined by [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md).
