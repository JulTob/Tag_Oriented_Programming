"""Applying a Tag: the tagging sequence and its call boundary.

For each Tag in the Form (Bases first), in order:

    1. Gate: that Tag's declarations are checked against the current
       Overlay, then its Preconditions inspect the Agent at this turn.
    2. Its Gains, conditions and deletions take effect in declaration
       order. Each builder can read or call what is already acquired.
    3. Its Imprints run, with acquired Gains but no membership yet.
    4. Field entry establishes membership and published services.

Once for the whole call:

    5. Every visible Postcondition is checked.

A refusal in 1 leaves completed Tags and existing Gains in place. A
failure in 2 or 3 retains acquired Gains and Posts, but never admits the
unfinished Tag. A failure after 4 retains membership. Current Posts
determine soundness; failures are not permanent defects. Python
interruptions keep their original type and follow the same boundary.
"""

from __future__ import annotations

from typing import Any
import weakref

from .contracts import _evaluate
from .declarations import _is_link
from .declarations import _Declarations
from .declarations import _discard_lazy_result
from .declarations import _declarations_of
from .declarations import _is_flag
from .declarations import _protocol_inputs
from .errors import _exception_text
from .errors import _type_name
from .errors import TagCompositionError
from .errors import TagImprintError
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .geometry import _form_of
from .overlay import _install
from .overlay import _gainings
from .overlay import _quiet
from .overlay import _preflight_ordinary_gains
from .state import STATE
from .state import _Published
from .state import _Snapshot
from .state import _State
from .state import _actualize_runtime_type
from .state import _bind_to
from .state import _host_bindings_of
from .state import _name_of
from .state import _namespace_of
from .state import _rebind_all
from .state import _restore_namespace
from .state import _restore_host_bindings
from .state import _runtime_type_for
from .state import _state_for
from .state import _state_of
from .state import _set_runtime_type


def _apply(
        agent: object,
        tag: type,
        inputs: dict[str, Any],
        ) -> object:
    """Apply ``tag`` and its missing Bases to ``agent`` as one call."""

    entry_state = _state_of(agent)

    if entry_state is not None and (
            tag in entry_state.active or tag in entry_state.training
            ):
        return agent

    return _apply_form(agent, _form_of(tag), inputs)


def _apply_form(
        agent: object,
        form: tuple[type, ...] | list[type],
        inputs: dict[str, Any],
        *,
        inspect: bool = True,
        admitted: list[type] | None = None,
        ) -> object:
    """Complete independent Tag turns and optionally report direct admissions.

    A Link uses ``admitted`` for its internal Pair memberships. Completed
    nested Taggings belong to their own calls and are never reported here.
    """

    entry_state = _state_of(agent)
    if entry_state is not None:
        for member in form:
            if member in entry_state.training:
                raise TagCompositionError(
                        f"{form[-1].__name__} needs {member.__name__}, whose"
                        " Tagging has not finished"
                        )

    entry_class = type(agent)
    entry_host = (
            _host_bindings_of(agent)
            if entry_state is None and not issubclass(type(agent), type)
            else None
            )
    try:
        state = _state_for(agent)
    except BaseException:
        if entry_host is not None:
            _restore_host_bindings(agent, entry_host)
        raise
    entry_host = None   # later training keeps its own acquired Gains

    try:
        for member in form:
            # An earlier Imprint may have completed this later turn.
            if member in state.active:
                continue

            _gate(agent, state, member, inputs)
            if member in state.active:
                continue   # a nested call made by the Gate completed this turn
            if admitted is None:
                _apply_one(agent, state, member, inputs)
            else:
                try:
                    _apply_one(agent, state, member, inputs)
                finally:
                    if member in state.active and member not in admitted:
                        admitted.append(member)

        if inspect:
            _inspect(agent)   # Posts judge the completed Form, once.
    except BaseException:
        if (
                entry_state is None
                and type(agent) is state.host_type
                and not state.active
                and not state.ever
                and not state.actions
                and not state.records
                and not state.preconditions
                and not state.postconditions
                and not state.deleted
                and not state.links
                ):
            # A state-free runtime clone may have been normalized before
            # its Gate. Restore its original representation when no
            # preparation or Gaining succeeded.
            if type(agent) is not entry_class:
                _set_runtime_type(agent, entry_class)
            _namespace_of(agent).pop(STATE, None)
        raise

    return agent


def _gate(
        agent: object,
        state: _State,
        tag: type,
        inputs: dict[str, Any],
        ) -> None:
    """Let one Tag inspect the Agent before that Tag begins.

    The scratch Overlay composes this Tag's own declarations over Tags whose
    turns have already finished. Nothing is installed on the live state.
    """

    declarations = _declarations_of(tag)
    if (
            not declarations.gain_order
            and not declarations.reports
            and not declarations.operations
            and not _is_flag(tag)
            ):
        return   # no Overlay or Flag protocol seat to validate

    if declarations.preconditions or declarations.postconditions:
        _refuse_conditions_shadowed_by_the_agent(
                agent,
                state,
                tag,
                declarations,
                )
    if declarations.links:
        _refuse_links_shadowed_by_the_agent(agent, state, tag, declarations)
    quiet = _quiet.set(_quiet.get() + 1)   # the real pass warns; catch_warnings() would reset every registry

    try:
        if _preflight_ordinary_gains(state, tag, declarations):
            return
        scratch = state.Copy()
        _install(
                scratch,
                tag,
                declarations,
                )
    finally:
        _quiet.reset(quiet)

    if not declarations.preconditions:
        return

    state.composing += 1

    try:
        _evaluate(
                (
                    (name, scratch.preconditions[name])
                    for name, _function in declarations.preconditions
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
        state: _State,
        tag: type,
        inputs: dict[str, Any],
        ) -> None:
    declarations = _declarations_of(tag)
    deleted_before = set(state.deleted)
    state.training.add(tag)
    state.composing += 1
    primary_failure: BaseException | None = None

    try:
        # Mechanical actualization precedes every builder and Imprint.
        # A rejected host transition has not acquired any new Gains yet.
        entry_class = type(agent)
        first = "_TOPKIT_HOST_TYPE" not in entry_class.__dict__
        entry_host = (
                _host_bindings_of(agent)
                if first and state.pinned is None else None
                )
        entry_namespace = (
                dict(_namespace_of(agent))
                if first and state.pinned is not None else None
                )
        try:
            _actualize(agent, state, tag, declarations.header, entering=_is_flag(tag))
        except BaseException:
            if entry_host is not None:
                _restore_host_bindings(agent, entry_host)
            elif entry_namespace is not None:
                if type(agent) is not entry_class:
                    _set_runtime_type(agent, entry_class)
                _restore_namespace(agent, entry_namespace)
            raise

        def prepare(gaining: _Declarations, needs_runtime: bool) -> None:
            _prepare_gains(
                    agent, state, deleted_before, tag, gaining,
                    refresh=needs_runtime,
                    )

        _gainings(
                agent,
                state,
                tag,
                declarations,
                deleted_before,
                inputs,
                prepare,
                )

        _imprint(agent, declarations, inputs)

        # Tag-scope services arrive with admission. A failed representation
        # must not replace the services of an already active Agency.
        header = declarations.header
        has_header = bool(header.runtime or header.reports or header.operations)
        previous = state.Copy() if has_header else None
        if previous is not None:
            previous_type = type(agent)
            previous_namespace = dict(_namespace_of(agent))

        try:
            if has_header:
                _install(state, tag, header)
                _prepare_gains(agent, state, deleted_before, tag, header)

            if declarations.rips:
                state.rips[tag] = tuple((name, state.actions[name]) for name in declarations.rips)

            _enter_field(agent, state, tag, declarations)
        except BaseException:
            if tag not in state.active:
                if previous is not None:
                    if type(agent) is not previous_type:
                        _set_runtime_type(agent, previous_type)
                    _restore_namespace(agent, previous_namespace)
                    state.Restore(previous)
                else:
                    state.rips.pop(tag, None)
            raise
    except BaseException as error:
        primary_failure = error
        raise
    finally:
        try:
            if tag in state.active:
                try:
                    state.snapshots[tag] = _snapshot(
                            agent,
                            state,
                            )
                except BaseException as closing_error:
                    if primary_failure is None:
                        raise
                    try:
                        BaseException.add_note(
                                primary_failure,
                                f"The {tag.__name__} view could not be captured after Write:"
                                f" {type(closing_error).__name__}",
                                )
                    except BaseException:
                        pass
        finally:
            primary_failure = None
            state.training.discard(tag)
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


def _prepare_gains(
        agent: object,
        state: _State,
        deleted_before: set[str],
        tag: type,
        declarations: _Declarations,
        *,
        refresh: bool = True,
        ) -> None:
    """Expose each acquired declaration before the next builder runs."""

    if declarations.deletions:
        namespace = _namespace_of(agent)
        for name in state.deleted - deleted_before:
            namespace.pop(name, None)

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

    if refresh:
        _actualize(agent, state, tag, declarations)


def _actualize(
        agent: object,
        state: _State,
        tag: type,
        declarations: _Declarations,
        *,
        entering: bool = False,
        ) -> None:
    """Refresh the runtime behavior independently of Field membership."""

    changes_type = (
            "_TOPKIT_HOST_TYPE" not in type(agent).__dict__
            or declarations.runtime
            or (entering and _is_flag(tag))
            )

    if not changes_type:
        for name, _function in (*declarations.actions, *declarations.records):
            if type(type(agent).__dict__.get(name)) is _Published:
                break
        else:
            return

    next_type = _runtime_type_for(state)

    if type(agent) is not next_type:
        if type(agent) is state.host_type:
            _actualize_runtime_type(agent, next_type, state)
        else:
            _set_runtime_type(agent, next_type)


def _enter_field(
        agent: object,
        state: _State,
        tag: type,
        declarations: _Declarations,
        ) -> None:
    """Establish membership after the Tag's Gains have been prepared."""

    plans = None
    if state.pinned is not None and declarations.published:
        plans = _publication_plans(state.pinned, declarations.published)

    tag._topkit_field._Add(agent)
    state.active.append(tag)
    state.words = None
    if _is_link(tag):
        if state.ever_links is None:
            state.ever_links = weakref.WeakSet()
        state.ever_links.add(tag)
    else:
        state.ever.add(tag)

    if state.pinned is not None:
        state.published.update(declarations.published)

    # Flag query syntax was prepared during training; answers change only
    # now. A Pin publishes its acquired Gains only after admission.
    if state.pinned is not None and declarations.published:
        _actualize(agent, state, tag, declarations, entering=True)

    if state.pinned is not None and declarations.published:
        _publish_to_field(
                state.pinned,
                declarations.published,
                plans,
                )


def _publication_plans(
        pinned: type,
        names: frozenset[str],
        ) -> list[tuple[object, _State]]:
    """Check publication before admitting the Pin; no recipient is changed."""

    from .declarations import _invalidate_declarations
    from .overlay import _adapter

    state = _state_of(pinned)
    _invalidate_declarations(pinned)   # the Tag's declarations grew
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

    return plans


def _publish_to_field(
        pinned: type,
        names: frozenset[str],
        plans: list[tuple[object, _State]],
        ) -> None:
    """Publish an admitted Pin's Gains after every recipient passed preflight."""

    from .overlay import _adapter

    state = _state_of(pinned)
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
    from .overlay import _install_action, _refuse_member_over_link
    from .constants import _refuse_constant

    for name in names:
        _refuse_member_over_link(agent_state, pinned, name, "a published member")
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


def _imprint(
        agent: object,
        declarations: _Declarations,
        inputs: dict[str, Any],
        ) -> None:
    for name, imprint in declarations.imprints:
        try:
            result = imprint(
                    agent,
                    **_protocol_inputs(imprint, inputs, 1),
                    )
            lazy = _discard_lazy_result(result)
        except Exception as error:
            raise TagImprintError.Named(name)(
                    f"Imprint {str.__str__(name)!r} failed:"
                    f" {_type_name(error)}: {_exception_text(error)}"
                    ) from error

        if lazy is not None:
            article = "an" if lazy == "async generator" else "a"

            raise TagImprintError.Named(name)(
                    f"Imprint {str.__str__(name)!r} returned {article}"
                    f" {lazy}; an Imprint must complete synchronously."
                    " TOP does not await or iterate application protocols."
                    )


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
