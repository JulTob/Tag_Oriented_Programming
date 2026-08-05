# Changelog

TagKit follows semantic versioning while its Python surface evolves.

## 0.2.0a1 — 2026-08-05

This alpha establishes the modular TagKit runtime and the current Python
profile of TOP.

### Added

- Stable public imports through `TagKit`.
- Procedural `Apply`, `Has`, and `Tags` queries.
- Tag Fields through `Tag[:]` and Agent-bound views through `Tag[agent]`.
- Geometry, Forms, Overlays, and explicit Underlays.
- Pins for applying Tags to Tags.
- Atomic Tagging with rollback of TOP state and supported host mutations.
- `Scope` and `At_Exit` lifecycle helpers.
- Typed contribution decorators and a `py.typed` marker.
- Deterministic state-machine and capacity stress suites.
- Manifesto, technical Specification, TagKit Guide, and Pin Guide.

### Changed

- The implementation is divided into cohesive internal modules. Application
  imports remain rooted at `TagKit`.
- Active reapplication is a strict no-op.
- Reports are ordinary public data declared by the program on a Tag.
- Python naming and documentation use `__name__`, `__doc__`, `str`, and
  `repr`.
- Structural runtime protocols are reserved for TagKit and the host object.
- Nested Tagging or Ripping of the same Target during one protocol is rejected
  so the outer transaction remains atomic.

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
- Move nested Tag applications out of Preconditions, Imprints, Records, and
  Postconditions. Express inherent relationships through Bases and Shapes;
  perform independent application after the current Tagging commits.
- Define cloning and serialization in the application domain. Do not copy
  `_TAGKIT_STATE`.

The complete Python behavior is documented in
[`TagKit/GUIDE.md`](TagKit/GUIDE.md). Observable paradigm semantics remain
defined by [`spec/SPECIFICATION.md`](spec/SPECIFICATION.md).
