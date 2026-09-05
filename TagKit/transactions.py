"""Applying a Tag: the tagging sequence and its call boundary.

Once for the whole call:

    1. Gate: the Preconditions visible in the composed Form of this call
       inspect the incoming Agent. A Shape's override wins over its Base's.

For each Tag in the Form (Bases first), in order:

    2. Its Records are built (each may read the value already stored).
    3. Commit: membership, Overlay, runtime type.
    4. Its Imprints run.

Once for the whole call:

    5. Every visible Postcondition is checked.

A failure in 1 or 2 rolls the whole call back: the Agent is exactly as it
was, including Bases pulled in by this call. A failure in 4 or 5 raises
but the Tags stay: the product left the line, defective, to be repaired
or Ripped.
"""

from __future__ import annotations

from typing import Any
import warnings

from .contracts import _evaluate
from .declarations import _Declarations
from .declarations import _declarations_of
from .declarations import _protocol_inputs
from .errors import TagCompositionError
from .errors import TagError
from .errors import TagImprintError
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .geometry import _form_of
from .overlay import _install
from .overlay import _materialize
from .state import STATE
from .state import Tagged
from .state import _Snapshot
from .state import _State
from .state import _bind_to
from .state import _namespace_of
from .state import _rebind_all
from .state import _runtime_type_for
from .state import _state_for
from .state import _state_of


def _apply(
        agent: object,
        tag: type,
        inputs: dict[str, Any],
        ) -> object:
    """Apply ``tag`` and its missing Bases to ``agent`` as one call."""

    entry_namespace = dict(_namespace_of(agent) or {})
    entry_state = _state_of(agent)
    entry_copy = entry_state.Copy() if entry_state is not None else None
    entry_tags = tuple(entry_state.active) if entry_state is not None else ()
    entry_class = type(agent)

    try:
        state = _state_for(agent)
        pending = [
                member
                for member in _form_of(tag)
                if member not in state.active
                ]

        if pending:
            if any(
                    _declarations_of(member).preconditions
                    for member in pending
                    ):
                _gate(
                        agent,
                        state,
                        pending,
                        inputs,
                        )

            for member in pending:
                _apply_one(
                        agent,
                        member,
                        inputs,
                        )

            _inspect(agent)
    except (TagImprintError, TagPostconditionError):
        raise
    except BaseException:
        _rollback(
                agent,
                entry_namespace,
                entry_copy,
                entry_tags,
                entry_class,
                )
        raise

    return agent


def _rollback(
        agent: object,
        entry_namespace: dict[str, Any],
        entry_copy: _State | None,
        entry_tags: tuple[type, ...],
        entry_class: type,
        ) -> None:
    current = _state_of(agent)

    if current is not None:
        for tag in current.active:
            if tag not in entry_tags:
                tag._tagkit_field.Remove(agent)

    namespace = _namespace_of(agent)

    if namespace is None:
        return

    namespace.clear()
    namespace.update(entry_namespace)

    if entry_copy is not None:
        namespace[STATE] = entry_copy
    else:
        namespace.pop(STATE, None)

    if type(agent) is not entry_class:
        agent.__class__ = entry_class


def _gate(
        agent: object,
        state: _State,
        pending: list[type],
        inputs: dict[str, Any],
        ) -> None:
    """Inspect the incoming materials once, against the Form as it will be.

    Every pending Tag is laid over a scratch copy so that a Shape's
    Precondition overrides (relaxes) its Base's, and so that declaration
    errors and collisions surface before anything changes.
    """

    scratch = state.Copy()
    names: list[str] = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        for tag in pending:
            declarations = _declarations_of(tag)

            _install(
                    scratch,
                    tag,
                    declarations,
                    )

            for name, _function in declarations.preconditions:
                if name not in names:
                    names.append(name)

    state.composing += 1

    try:
        _evaluate(
                (
                    (name, scratch.preconditions[name])
                    for name in names
                    if name in scratch.preconditions
                    ),
                agent,
                inputs,
                TagPreconditionError,
                "Precondition",
                )
    finally:
        state.composing -= 1


def _apply_one(
        agent: object,
        tag: type,
        inputs: dict[str, Any],
        ) -> None:
    # The state is laid over in place: the call boundary (_apply) holds the
    # entry copy that a Record failure rolls back to, and nothing reads the
    # new Overlay before commit binds it on the Agent.
    state = _state_for(agent)
    declarations = _declarations_of(tag)
    deleted_before = set(state.deleted)
    state.composing += 1

    try:
        _install(
                state,
                tag,
                declarations,
                )

        _materialize(
                agent,
                declarations,
                deleted_before,
                inputs,
                )

        _commit(
                agent,
                state,
                deleted_before,
                tag,
                declarations,
                )

        try:
            _imprint(
                    agent,
                    declarations,
                    inputs,
                    )
        finally:
            state.snapshots[tag] = _snapshot(
                    agent,
                    state,
                    )
    finally:
        state.composing -= 1


def _inspect(
        agent: object,
        ) -> None:
    """Quality check of the finished product: every visible Postcondition."""

    state = _state_of(agent)
    state.composing += 1

    try:
        _evaluate(
                state.postconditions.items(),
                agent,
                {},
                TagPostconditionError,
                "Postcondition",
                )
    finally:
        state.composing -= 1


def _commit(
        agent: object,
        state: _State,
        deleted_before: set[str],
        tag: type,
        declarations: _Declarations,
        ) -> None:
    namespace = _namespace_of(agent)

    for name in state.deleted - deleted_before:
        namespace.pop(name, None)

    state.active.append(tag)
    state.ever.add(tag)

    if declarations.secrets:
        # A first secret turns every bound Action into a composing one.
        _rebind_all(
                agent,
                state,
                )
    else:
        for name, _function in declarations.actions:
            if name in state.actions:
                _bind_to(
                        agent,
                        state,
                        name,
                        )

        for name, _operation, public in declarations.operations:
            if public and name in state.actions:
                _bind_to(
                        agent,
                        state,
                        name,
                        )

    if _needs_new_type(
            agent,
            declarations,
            ):
        next_type = _runtime_type_for(state)
    else:
        next_type = type(agent)

    if type(agent) is not next_type:
        try:
            agent.__class__ = next_type
        except TypeError as error:
            raise TagCompositionError(
                    f"{type(agent).__name__} cannot be actualized in place"
                    ) from error

    tag._tagkit_field.Add(agent)


def _needs_new_type(
        agent: object,
        declarations: _Declarations,
        ) -> bool:
    """Only type-level facts change the runtime type: the first tagging,
    deletions, secrets, published Reports, dunder Actions, a first Post."""

    if not isinstance(agent, Tagged):
        return True

    return bool(
            declarations.deletions
            or declarations.secrets
            or declarations.dunders
            or declarations.postconditions
            or any(public for _name, _value, public in declarations.reports)
            )


def _imprint(
        agent: object,
        declarations: _Declarations,
        inputs: dict[str, Any],
        ) -> None:
    for name, imprint in declarations.imprints:
        try:
            imprint(
                    agent,
                    **_protocol_inputs(imprint, inputs, 1),
                    )
        except TagError:
            raise
        except Exception as error:
            raise TagImprintError.Named(name)(
                    f"Imprint {imprint.__qualname__} failed:"
                    f" {type(error).__name__}: {error}"
                    ) from error


def _snapshot(
        agent: object,
        state: _State,
        ) -> _Snapshot:
    namespace = _namespace_of(agent)
    records = {
            name: namespace[name]
            for name in state.records
            if name in namespace
            }

    reports = {
            name: (origin, getattr(origin, name))
            for name, (origin, _report) in state.reports.items()
            }

    return _Snapshot(
            actions=dict(state.actions),
            records=records,
            reports=reports,
            operations=dict(state.operations),
            deleted=frozenset(state.deleted),
            secrets=frozenset(state.secrets),
            )
