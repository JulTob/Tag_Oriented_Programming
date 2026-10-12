# STEP-SPEC-37: Host Actualization

- **STEP:** SPEC-37
- **Desk:** spec
- **Title:** Host Actualization
- **Author:** Codex, recording the host-boundary review
- **Status:** Brief
- **Created:** 2026-10-12

## Summary

An implementation that needs a runtime representation of a Target must
verify that the representation was actually installed and retained TOP
state. A failure at this boundary is a Composition Failure, and must not
leave a provisional runtime type, new instance bindings or Field entries
behind. Python host immutability remains independent of this internal
representation change.

## Motivation

TopKit can actualize a Target as an Agent by changing its Python class to
a runtime subclass. A custom host may reject or silently ignore that
change, substitute another type or erase TOP state. A metaclass may also
replace the requested type or strip its required machinery. Checking only
whether assignment raised can leave an object partly actualized.

Conversely, Python's generated frozen-dataclass setter forbids every
assignment on the exact dataclass, including an internal class change.
Treating that generic binding protection as a deliberate refusal makes
previously supported frozen hosts untaggable.

## Proposed specification

1. Identity preservation includes failure to prepare an implementation's
   runtime representation: the original Target must remain the same
   object. A representation failure is a Composition Failure.
2. The implementation must verify actual installation and retained TOP
   state. A host silently ignoring the installation is a failure, rather
   than successful Tagging.
3. Failed initial actualization restores the original runtime type and
   instance bindings, and leaves no new membership or Field entries. It
   does not promise to undo arbitrary external effects or changes inside
   mutable objects performed by user code.
4. Runtime changes must preserve ordinary host behavior. A Python frozen
   dataclass's existing frozen fields stay frozen after Tagging. A custom
   host hook that deliberately refuses the runtime change remains a
   Composition Failure.
5. These requirements concern representation preparation. They do not
   decide the order of Gate, Gainings, Imprints, FieldAdding and Posts,
   nor the treatment of Gains when user training fails. Those are
   separate Tagging decisions.

## Python implementation notes

TopKit requires the real, persistent instance dictionary and checks that
the requested runtime subclass keeps its kernel machinery. Rollback
restores the original class before reading the namespace, so a rejected
provisional class cannot hide that namespace.

Only standard generated frozen-dataclass binding-protection wrappers are
skipped for the internal class write. The next host setter still runs;
custom replacements of a generated setter are respected. Ordinary Agent
writes retain the original frozen setters. This includes compatible
slotted dataclasses with inherited instance storage. Recognition relies
on the supported Python dataclass generators and must be tested on each
supported Python version.

## Backwards compatibility

Ordinary hosts and compatible frozen dataclasses continue to work.
Hosts that refuse, ignore or substitute the required representation now
fail clearly and restore their instance bindings. Objects exposing a
disposable or shadowing `__dict__` cannot pretend to provide instance
storage.

## Alternatives considered

- Bypassing every host setter would retain frozen-dataclass support, but
  would also disregard intentional host restrictions.
- Rejecting every frozen dataclass would unnecessarily remove an existing
  supported host type.
- Falling back after any `FrozenInstanceError` would bypass genuine
  custom refusal hooks using that exception.
- Promising general rollback of user code would require capabilities
  beyond restoring the runtime representation and instance bindings.

### Decision

Pending the Director's review. This STEP does not amend the Specification
until it is cleared. PR #89's previous untracked specification sentence
is removed while this proposal is reviewed.
