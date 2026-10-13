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
but the committed Tags stay. Their current Postconditions determine
soundness; the failure itself is not a permanent defect. Python
interruptions keep their original type and follow the same phase boundary.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Callable
import weakref

from .contracts import _evaluate
from .declarations import _is_link
from .declarations import _Declarations
from .declarations import _declarations_of
from .declarations import _is_flag
from .declarations import _protocol_inputs
from .errors import TagCompositionError
from .errors import TagImprintError
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .geometry import _form_of
from .overlay import _install
from .overlay import _quiet
from .overlay import _refuse_in_collisions_of_the_form
from .overlay import _materialize
from .state import STATE
from .state import _Snapshot
from .state import _State
from .state import _bind_to
from .state import _name_of
from .state import _namespace_of
from .state import _rebind_all
from .state import _restore_namespace
from .state import _runtime_type_for
from .state import _state_for
from .state import _state_of
from .state import _set_runtime_type


@dataclass(slots=True)
class _Call_Boundary:
    """The failure phase of this call, independent of any nested tagging.

    ``undo`` and ``writes`` belong to this call alone: steps on other
    Targets that are part of it (a Link's Contacts and Pairs, STEP-SPEC-22
    rules 4.6 and 5.6). ``undo`` runs, latest first, when the call rolls
    back; a call that does not roll back hands its ``undo`` to the call
    around it, so a linking made anywhere inside a call that later rolls
    back is undone with it. ``writes`` run after the call's Tags are
    committed, before its Quality check."""

    after_commit: bool = False
    undo: list["_Undo_Step"] = field(default_factory=list)
    writes: list[Callable[[], None]] = field(default_factory=list)
    open: bool = True   # False once its call has returned: a task that copied the context takes no steps here
    agent: object | None = None   # the call's Agent; None for a linking's own boundary


@dataclass(slots=True)
class _Undo_Step:
    """One step a call took on other Targets, and the Agents it belongs
    to. A linking belongs to the Link's Agent and to the Contact; a Link
    granted or extended belongs to its Agent. A call that rolls back
    undoes the steps its own Agent owns; the others belong to taggings of
    other Agents, which stay independent (§0.6), and go to the call
    around it (STEP-SPEC-22 rule 5.6)."""

    owners: tuple[object, ...]
    run: Callable[[], None]


_current_boundary: ContextVar[_Call_Boundary | None] = ContextVar(
        "TopKit_call_boundary",
        default=None,
        )


@dataclass(slots=True)
class _Entry:
    """An Agent as it was when a call began: what a rollback restores."""

    namespace: dict[str, Any]
    state: _State | None
    tags: tuple[type, ...]
    host_class: type


def _capture(
        agent: object,
        ) -> _Entry:
    state = _state_of(agent)

    return _Entry(
            namespace=dict(_namespace_of(agent) or {}),
            state=state.Copy() if state is not None else None,
            tags=tuple(state.active) if state is not None else (),
            host_class=type(agent),
            )


def _rollback_to(
        agent: object,
        entry: _Entry,
        ) -> None:
    _rollback(
            agent,
            entry.namespace,
            entry.state,
            entry.tags,
            entry.host_class,
            )


def _open_boundary(
        ) -> _Call_Boundary | None:
    """The call this code runs inside, if it is still running. An asyncio
    task or callback started inside a call copies its context, and with
    it a boundary whose call may have returned long ago."""

    boundary = _current_boundary.get()

    if boundary is None or not boundary.open:
        return None

    return boundary


def _close(
        boundary: _Call_Boundary,
        ) -> None:
    """The call has returned: its boundary takes no more steps and holds
    nothing (a copied context may keep the object itself)."""

    boundary.open = False
    boundary.agent = None
    boundary.undo.clear()
    boundary.writes.clear()


def _undo(
        boundary: _Call_Boundary,
        ) -> None:
    """Undo every step taken inside this boundary, latest first: a refused
    linking changes nothing (STEP-SPEC-22 rule 5.1)."""

    for step in reversed(boundary.undo):
        step.run()


def _undo_owned(
        boundary: _Call_Boundary,
        agent: object,
        ) -> list[_Undo_Step]:
    """Undo, latest first, the steps this call's Agent owns; return the
    others, which belong to other Agents."""

    owned = [
            step
            for step in boundary.undo
            if _owns(agent, step)
            ]
    others = [
            step
            for step in boundary.undo
            if not _owns(agent, step)
            ]

    for step in reversed(owned):
        step.run()

    return others


def _owns(
        agent: object,
        step: _Undo_Step,
        ) -> bool:
    return any(
            owner is agent
            for owner in step.owners
            )


def _hand_over(
        boundary: _Call_Boundary,
        outer: _Call_Boundary | None,
        ) -> None:
    """This call will not roll back: the call around it, if any, takes
    its undo steps, and runs the ones it owns if it rolls back itself
    (STEP-SPEC-22 rule 5.6)."""

    _hand_over_steps(
            boundary.undo,
            outer,
            )


def _hand_over_steps(
        steps: list[_Undo_Step],
        outer: _Call_Boundary | None,
        ) -> None:
    if outer is not None:
        outer.undo.extend(steps)


def _apply(
        agent: object,
        tag: type,
        inputs: dict[str, Any],
        ) -> object:
    """Apply ``tag`` and its missing Bases to ``agent`` as one call."""

    return _apply_form(
            agent,
            _form_of(tag),
            inputs,
            )


def _apply_form(
        agent: object,
        form: tuple[type, ...] | list[type],
        inputs: dict[str, Any],
        deferred: list[_Declarations] | None = None,
        gated: bool = False,
        ) -> object:
    """Apply every Tag of ``form`` the Agent lacks, Bases first, as one call.

    With ``deferred`` (a list), the call stops after Commit: the Imprints
    of each applied Tag are appended to it instead of running, and the
    Quality check is left to the caller. A Link uses this to put a
    Contact's entry between its Pair's Parts and its Pair's Imprints
    (STEP-SPEC-22 rule 5.1). With ``gated``, the caller has already run
    the gate (``_gate_form``), so it is not run twice."""

    entry_state = _state_of(agent)

    if entry_state is not None and all(
            member in entry_state.active
            for member in form
            ):
        return agent   # the whole Form is active: nothing to apply, nothing to undo

    entry = _capture(agent)
    outer = _open_boundary()
    boundary = _Call_Boundary(agent=agent)
    token = _current_boundary.set(boundary)

    try:
        state = _state_for(agent)
        pending = [
                member
                for member in form
                if member not in state.active
                ]

        if pending:
            if len(pending) > 1:
                _refuse_in_collisions_of_the_form(
                        state,
                        pending,
                        )

            if not gated and any(
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
                        boundary,
                        deferred,
                        )

            boundary.after_commit = True   # Quality follows the completed Form

            for write in boundary.writes:
                write()

            if deferred is None:
                _inspect(agent)
    except BaseException:
        if boundary.after_commit:
            _hand_over(
                    boundary,
                    outer,
                    )   # the failure raises and what was done stays (§0.6)
        else:
            others: list[_Undo_Step] = []

            try:
                others = _undo_owned(
                        boundary,
                        agent,
                        )   # its own steps first, on other Targets ...
            finally:
                _rollback_to(
                        agent,
                        entry,
                        )   # ... then the Agent itself, exactly as it was at the call

            _hand_over_steps(
                    others,
                    outer,
                    )   # the rest belongs to other Agents: the call around decides
        raise
    else:
        _hand_over(
                boundary,
                outer,
                )
    finally:
        _current_boundary.reset(token)
        _close(boundary)

    return agent


def _gate_form(
        agent: object,
        form: tuple[type, ...] | list[type],
        inputs: dict[str, Any],
        ) -> None:
    """The gate a call over ``form`` would run, and nothing else. A Shape
    that extends a held Link runs every Pair's gate this way before any
    Pair's Parts (STEP-SPEC-22 rule 4.6)."""

    state = _state_of(agent)

    if state is None:
        return

    pending = [
            member
            for member in form
            if member not in state.active
            ]

    if not pending:
        return

    if len(pending) > 1:
        _refuse_in_collisions_of_the_form(
                state,
                pending,
                )

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
                tag._topkit_field._Remove(agent)

    _restore_namespace(
            agent,
            entry_namespace,
            )
    namespace = _namespace_of(agent)

    if namespace is None:
        return

    if entry_copy is not None:
        live = namespace.get(STATE)

        if live is None:
            namespace[STATE] = entry_copy
        else:
            live.Restore(entry_copy)   # in place: a door opened before this call closes on it
    else:
        namespace.pop(STATE, None)

    if type(agent) is not entry_class:
        _set_runtime_type(agent, entry_class)


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
    quiet = _quiet.set(_quiet.get() + 1)   # the real pass warns; catch_warnings() would reset every registry

    try:
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
    finally:
        _quiet.reset(quiet)

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
        boundary: _Call_Boundary,
        deferred: list[_Declarations] | None = None,
        ) -> None:
    # The state is laid over in place: the call boundary (_apply) holds the
    # entry copy that a Record failure rolls back to, and nothing reads the
    # new Overlay before commit binds it on the Agent.
    boundary.after_commit = False   # this Tag's Parts can still refuse the whole call
    state = _state_for(agent)
    declarations = _declarations_of(tag)
    retained_constants = frozenset(state.constants)
    deleted_before = set(state.deleted)
    _refuse_conditions_shadowed_by_the_agent(
            agent,
            state,
            tag,
            declarations,
            )
    _refuse_links_shadowed_by_the_agent(
            agent,
            state,
            tag,
            declarations,
            )
    state.composing += 1
    primary_failure: BaseException | None = None

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
                retained_constants,
                )

        if declarations.links:
            from .links import _grant   # links builds on this module

            _grant(
                    agent,
                    state,
                    declarations,
                    )

        _commit(
                agent,
                state,
                deleted_before,
                tag,
                declarations,
                )

        boundary.after_commit = True

        try:
            if deferred is None:
                _imprint(
                        agent,
                        declarations,
                        inputs,
                        )
            else:
                deferred.append(declarations)   # the caller runs them, after its other Commits
        except BaseException as error:
            primary_failure = error
            raise
        finally:
            try:
                state.snapshots[tag] = _snapshot(
                        agent,
                        state,
                        )
            except BaseException as closing_error:
                if primary_failure is None:
                    raise

                # Diagnostics must never replace the primary failure. Custom
                # exceptions can make even adding a note fail.
                try:
                    BaseException.add_note(
                            primary_failure,
                            f"The {tag.__name__} view could not be captured after Write:"
                            f" {type(closing_error).__name__}",
                            )
                except BaseException:
                    pass
    finally:
        primary_failure = None   # do not keep the Agent alive through an exception traceback
        state.composing -= 1


def _refuse_conditions_shadowed_by_the_agent(
        agent: object,
        state: _State,
        tag: type,
        declarations: Any,
        ) -> None:
    """A condition is read on the Agent by its name (STEP-SPEC-14). A value
    the Agent itself already holds under that name would shadow it in
    silence, so the tagging is refused at the door."""

    namespace = _namespace_of(agent) or {}

    for name, _function in (
            *declarations.preconditions,
            *declarations.postconditions,
            ):
        if (
                name in namespace
                and name not in state.records
                and name not in state.actions
                and name != STATE
                ):
            raise TagCompositionError(
                    f"{tag.__name__}.{name} is a condition, but"
                    f" {_name_of(agent)} already holds a value called"
                    f" {name!r}; a condition is read by its name and cannot"
                    " share it"
                    )


def _refuse_links_shadowed_by_the_agent(
        agent: object,
        state: _State,
        tag: type,
        declarations: Any,
        ) -> None:
    """A Link never arrives where something is (STEP-SPEC-22 rule 4.4):
    a value the Agent itself already holds under the Link's name would be
    lost under a read-only slot, so the tagging is refused."""

    if not declarations.links:
        return

    namespace = _namespace_of(agent) or {}

    for name, _relation in declarations.links:
        if name not in namespace:
            continue

        held = state.links.get(name)

        if held is not None and namespace[name] is held[0]:
            continue   # the Agent's own Link: reapplied, or extended

        if name in state.records or name in state.actions:
            continue   # a Contribution: the closed slot names it (overlay._install_link)

        raise TagCompositionError(
                f"{tag.__name__}.{name} is a Link, but"
                f" {_name_of(agent)} already holds a value called {name!r};"
                " a Link never arrives where something is"
                )


def _inspect(
        agent: object,
        ) -> None:
    """Quality check of the finished product: every visible Postcondition."""

    state = _state_of(agent)

    if not state.postconditions:
        return   # nothing promised: nothing to inspect

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
    state.words = None

    if _is_link(tag):
        if state.ever_links is None:
            state.ever_links = weakref.WeakSet()

        state.ever_links.add(tag)   # weakly: a living Contact never keeps a dead Agent's Link (STEP-SPEC-22)
    else:
        state.ever.add(tag)

    if declarations.secrets:
        # A first secret turns every bound Action into a composing one.
        _rebind_all(
                agent,
                state,
                )
    else:
        for name, _function in declarations.actions:
            if name in state.actions and name != "__del__":   # __del__ stays Python's: the finalizer
                _bind_to(
                        agent,
                        state,
                        name,
                        )

        for name, _operation, public in declarations.operations:
            if public and name in state.actions and name != "__del__":
                _bind_to(
                        agent,
                        state,
                        name,
                        )

    if _needs_new_type(
            agent,
            tag,
            declarations,
            ):
        next_type = _runtime_type_for(state)
    else:
        next_type = type(agent)

    if type(agent) is not next_type:
        try:
            _set_runtime_type(agent, next_type)
        except TypeError as error:
            raise TagCompositionError(
                    f"{type(agent).__name__} cannot be actualized in place"
                    ) from error

    tag._topkit_field._Add(agent)

    if state.pinned is not None and declarations.published:
        _publish_to_field(
                state.pinned,
                declarations.published,
                )


def _publish_to_field(
        pinned: type,
        names: frozenset[str],
        ) -> None:
    """A Pin's @Public members reach the pinned Tag's Field: every present
    Agent receives them now as the Tag's own published Reports and
    Operations; every future Agent through the Tag's declarations. The
    whole Field is checked on copies first, so no Agent is touched unless
    all can be."""

    from .declarations import _scan_cache
    from .overlay import _adapter

    state = _state_of(pinned)
    _scan_cache.pop(pinned, None)   # the Tag's declarations grew
    agents = list(pinned[:])
    plans: list[tuple[object, _State]] = []

    quiet = _quiet.set(_quiet.get() + 1)   # the real pass warns once

    try:
        for agent in agents:
            candidate = _state_of(agent).Copy()
            _publish_into(
                    candidate,
                    pinned,
                    state,
                    names,
                    _adapter,
                    )
            plans.append(
                    (
                        agent,
                        candidate,
                        )
                    )
    finally:
        _quiet.reset(quiet)

    for agent, candidate in plans:
        agent_state = _state_of(agent)
        _publish_into(
                agent_state,
                pinned,
                state,
                names,
                _adapter,
                )

        for name in names:
            if name in agent_state.actions:
                _bind_to(
                        agent,
                        agent_state,
                        name,
                        )

        next_type = _runtime_type_for(agent_state)

        if type(agent) is not next_type:
            _set_runtime_type(agent, next_type)


def _publish_into(
        agent_state: _State,
        pinned: type,
        state: _State,
        names: frozenset[str],
        adapter: Any,
        ) -> None:
    from .overlay import _install_action
    from .constants import _refuse_constant

    for name in names:
        if name in agent_state.constants:
            if agent_state.constants[name][0] is pinned and name in state.constants:
                continue
            _refuse_constant(agent_state, name)
        if name in state.records:
            agent_state.reports[name] = (pinned, None)
            agent_state.published.add(name)
            if name in state.constants:
                agent_state.constants[name] = (pinned, "report", None)
        elif name in state.actions:
            _install_action(
                    agent_state,
                    pinned,
                    name,
                    adapter(pinned, name, state.actions[name]),
                    )
            if name in state.constants:
                agent_state.constants[name] = (pinned, "operation", state.actions[name])


def _needs_new_type(
        agent: object,
        tag: type,
        declarations: _Declarations,
        ) -> bool:
    """Only type-level facts change the runtime type: the first tagging,
    deletions, secrets, published Reports, dunder Actions, conditions,
    or a first Flag."""

    if "_TOPKIT_HOST_TYPE" not in type(agent).__dict__:
        return True   # the Agent still wears its host's own class

    return bool(
            _is_flag(tag)
            or declarations.deletions
            or declarations.secrets
            or declarations.constants
            or declarations.tools
            or declarations.links
            or declarations.dunders
            or declarations.preconditions
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
        except Exception as error:
            raise TagImprintError.Named(name)(
                    f"Imprint {imprint.__qualname__} failed:"
                    f" {type(error).__name__}: {error}"
                    ) from error


_NONE: frozenset[str] = frozenset()   # one empty set for every snapshot that needs none


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

    for name in state.records:
        if name in state.secret_values:
            records[name] = state.secret_values[name]

    reports = {
            name: (origin, getattr(origin, name))
            for name, (origin, _report) in state.reports.items()
            if not _is_link(origin)   # never built here, inside her door, nor shown in her views (STEP-SPEC-22 rule 3.6)
            }
    operations = {
            name: entry
            for name, entry in state.operations.items()
            if not _is_link(entry[0])
            }

    links = {
            name: link
            for name, (link, _layers) in state.links.items()
            if link is not None
            }

    return _Snapshot(
            actions=dict(state.actions),
            records=records,
            reports=reports,
            operations=operations,
            links=links,
            deleted=frozenset(state.deleted) if state.deleted else _NONE,
            secrets=frozenset(state.secrets) if state.secrets else _NONE,
            )
