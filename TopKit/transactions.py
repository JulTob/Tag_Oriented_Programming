"""Applying a Tag: the tagging sequence and its call boundary.

For each Tag in the Form (Bases first), in order:

    1. Gate: that Tag's declarations are checked against the current
       Overlay, then its Preconditions inspect the Agent at this turn.
    2. Its Gains, Posts and deletions take effect in declaration
       order. Each builder can read or call what is already acquired.
    3. Its Imprints run, with acquired Gains but no membership yet.
    4. Field entry establishes membership and published services.

    5. Every current Postcondition is checked before the next Tag starts.

A fresh Tag requires a sound Agent and a successful structural preflight.
Ordinary Record and Imprint failures warn by declaration name and allow
later training to continue. The Agent then enters the Field; its current
Posts decide soundness. Python interruptions stop later training, retain
admission after structural preparation, and keep their original type.
"""

from __future__ import annotations

import warnings

from typing import Any
from typing import Callable

from .arrest import _require_available
from .arrest import _safehouse
from .contracts import _holds_for_population
from .contracts import _bind_condition
from .contracts import _evaluate
from .declarations import _Declarations
from .declarations import _discard_lazy_result
from .declarations import _declarations_of
from .declarations import _is_flag
from .declarations import _protocol_inputs
from .errors import _exception_text
from .errors import _training_warning
from .errors import TagTrainingWarning
from .errors import TaggingFailure
from .errors import TagTargetError
from .errors import _type_name
from .errors import TagCompositionError
from .errors import TagImprintError
from .errors import TagPostconditionError
from .errors import TagPreconditionError
from .fields import _field_of
from .geometry import _form_of
from .overlay import _install
from .overlay import _gainings
from .overlay import _remove_post_application
from .overlay import _WARNING_SKIP_PREFIXES
from .overlay import _quiet
from .overlay import _preflight_record_spaces
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
        *,
        check_posts: bool = True,
        check_source: bool = True,
        after_training: Callable[[], None] | None = None,
        before_gains: Callable[[], None] | None = None,
        post_inspector: Callable[[], None] | None = None,
        ) -> object:
    """Apply ``tag`` and its missing Bases to ``agent`` as one call."""

    from .observations import _refuse_observed_act
    _refuse_observed_act("Tagging")

    if _safehouse:
        _require_available(agent, "Tagging")

    entry_state = _state_of(agent)

    if entry_state is not None and (
            tag in entry_state.active or tag in entry_state.training
            ):
        return agent

    form = _form_of(tag)

    if entry_state is not None:
        for member in form:
            if member in entry_state.training:
                raise TagCompositionError(
                        f"{tag.__name__} needs {member.__name__}, whose"
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
    except TagCompositionError as error:
        if entry_host is not None:
            _restore_host_bindings(agent, entry_host)
        raise _target_failure(agent, tag, error) from error.__cause__
    except BaseException:
        if entry_host is not None:
            _restore_host_bindings(agent, entry_host)
        raise

    try:
        for member in form:
            # An earlier Imprint may have completed this later turn.
            if member in state.active:
                continue

            if check_source:
                _require_sound_source(agent, member)
            _gate(agent, state, member, inputs)
            if before_gains is not None:
                before_gains()
            failures: list[TagTrainingWarning] = []
            interruptions: list[BaseException] | None = None
            try:
                interruptions, closing_errors = _apply_one(
                        agent, state, member, inputs, failures,
                        )
                if after_training is not None:
                    after_training()
            except BaseException as error:
                primary = interruptions[0] if interruptions else error
                _report_training(failures, primary)
                if interruptions:
                    _note_secondary(interruptions[0], [error], "Admission also failed")
                    raise interruptions.pop()
                raise

            if not failures and not interruptions and not closing_errors:
                # Successful training needs no warning or failure containers.
                # Keep the same admission and per-Tag Post boundary.
                if check_posts:
                    if post_inspector is not None:
                        post_inspector()
                    elif state.postconditions:
                        _inspect(agent)
                continue

            post_errors: list[BaseException] = []
            if check_posts:
                try:
                    if post_inspector is None:
                        _inspect(agent)
                    else:
                        post_inspector()
                except BaseException as error:
                    post_errors.append(error)
            primary = (interruptions[0] if interruptions else (
                    post_errors[0] if post_errors else (
                        closing_errors[0][1] if closing_errors else None)))
            _report_training(failures, primary)
            primary = None
            if interruptions:
                _note_secondary(interruptions[0], post_errors,
                                "Post inspection after interruption also failed")
                _note_closing(interruptions[0], closing_errors)
                post_errors.clear()
                closing_errors.clear()
                raise interruptions.pop()
            if post_errors:
                _note_closing(post_errors[0], closing_errors)
                closing_errors.clear()
                raise post_errors.pop()
            if closing_errors:
                _note_closing(closing_errors[0][1], closing_errors[1:])
                del closing_errors[1:]
                raise closing_errors.pop()[1]
    except BaseException:
        if (
                entry_state is None
                and type(agent) is state.host_type
                and not state.active
                and not state.ever
                and not state.actions
                and not state.records
                and not state.postconditions
                and not state.deleted
                ):
            # A state-free runtime clone may have been normalized before
            # its Gate. Restore its original representation when no
            # preparation or Gaining succeeded.
            if entry_host is not None:
                _restore_host_bindings(agent, entry_host)
            else:
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

    Every refusal the Tag's own declarations would meet is raised here,
    before any builder runs, and nothing is installed on the live state.
    When a Tag can use the shortcut, ``_preflight_ordinary_gains`` checks
    its ordinary Action and Record names against the live state, one by one.
    An internal Report or Operation does not by itself require scratch
    composition; a public one does.
    Tags needing full composition are laid over a scratch copy of the state,
    on top of completed Tags. Preconditions are separately bound as
    transient Services over this Tag's ordered Form and judge the live Agent.
    """

    declarations = _declarations_of(tag)
    _preflight_record_spaces(state, tag, declarations)
    if (
            not declarations.gain_order
            and not declarations.reports
            and not declarations.operations
            and not declarations.preconditions
            and not _is_flag(tag)
            ):
        return   # no Overlay or Flag protocol seat to validate

    if declarations.postconditions:
        _refuse_posts_shadowed_by_the_agent(
                agent,
                state,
                tag,
                declarations,
                )
    quiet = _quiet.set(_quiet.get() + 1)   # the real pass warns; catch_warnings() would reset every registry

    try:
        if not _preflight_ordinary_gains(state, tag, declarations):
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
                _precondition_services(tag),
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
        failures: list[TagTrainingWarning],
        ) -> tuple[list[BaseException] | None, list[tuple[str, BaseException]]]:
    declarations = _declarations_of(tag)
    deleted_before = set(state.deleted)
    application = object()
    state.training.add(tag)
    state.composing += 1
    primary_failure: BaseException | None = None
    interruption: BaseException | None = None
    closing_errors: list[tuple[str, BaseException]] = []

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
        previous_arrestable = state.arrestable
        if declarations.rips:
            state.arrestable = True
        try:
            _actualize(agent, state, tag, declarations.header, entering=_is_flag(tag))
        except BaseException as error:
            state.arrestable = previous_arrestable
            if entry_host is not None:
                _restore_host_bindings(agent, entry_host)
            elif entry_namespace is not None:
                if type(agent) is not entry_class:
                    _set_runtime_type(agent, entry_class)
                _restore_namespace(agent, entry_namespace)
            if first and isinstance(error, TagCompositionError):
                raise _target_failure(agent, tag, error) from error.__cause__
            raise

        def prepare(gaining: _Declarations, needs_runtime: bool) -> None:
            _prepare_gains(
                    agent, state, deleted_before, tag, gaining,
                    refresh=needs_runtime,
                    )

        acquired_rips: list[tuple[str, Any]] | None = [] if declarations.rips else None
        interruption = _gainings(
                agent,
                state,
                tag,
                declarations,
                deleted_before,
                inputs,
                prepare,
                application,
                failures,
                acquired_rips,
                )

        # A nested Imprint may lay another Action over a Rip name. Remember
        # this Tag's acquired layer before training can change the Overlay.
        rip_actions = tuple(acquired_rips) if acquired_rips else ()

        if interruption is None:
            interruption = _imprint(agent, tag, declarations, inputs, failures)

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
                _install(
                        state,
                        tag,
                        header,
                        application=application,
                        )
                _prepare_gains(agent, state, deleted_before, tag, header)

            if rip_actions:
                state.rips[tag] = rip_actions

            _enter_field(
                    agent,
                    state,
                    tag,
                    declarations,
                    application,
                    )
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
        if tag not in state.active:
            changed = _remove_post_application(
                    state,
                    application,
                    keep_constants=False,
                    names=tuple(name for name, _ in declarations.postconditions),
                    )

            if changed:
                # A failed provisional Constant can leave a lower Post with
                # the same name.  The name set then stays equal while the
                # runtime gate must change from Constant back to Post.
                next_type = _runtime_type_for(state)
                if type(agent) is not next_type:
                    _set_runtime_type(agent, next_type)
            if interruption is not None:
                _note_secondary(interruption, [error], "Admission also failed")
                raise interruption
            raise
        closing_errors.append(("Post-entry setup also failed", error))
    finally:
        try:
            if tag in state.active:
                try:
                    state.snapshots[tag] = _snapshot(
                            agent,
                            state,
                            )
                except BaseException as closing_error:
                    closing_errors.append((
                            f"The {tag.__name__} view could not be captured after Write",
                            closing_error,
                            ))
        finally:
            primary_failure = None
            state.training.discard(tag)
            state.composing -= 1


    return (None if interruption is None else [interruption]), closing_errors

def _precondition_services(
        tag: type,
        ) -> tuple[tuple[str, Any], ...]:
    """Bind the current Tag's transient Pre Services over its Form.

    Pres from unrelated active Tags are deliberately absent: Services
    compose through the current ordered Form, not through Agent history.
    The returned checks exist only for this Gate evaluation.
    """

    visible: dict[str, Any] = {}
    current: list[tuple[str, Any]] = []

    for member in _form_of(tag):
        for name, function in _declarations_of(member).preconditions:
            check = _bind_condition(
                    function,
                    visible.get(name),
                    True,
                    name,
                    )
            visible[name] = check

            if member is tag:
                current.append((name, check))

    return tuple(current)


def _refuse_posts_shadowed_by_the_agent(
        agent: object,
        state: _State,
        tag: type,
        declarations: Any,
        ) -> None:
    """A Post is read on the Agent by its name. A value
    the Agent itself already holds under that name would shadow it in
    silence, so the tagging is refused at the door."""

    namespace = _namespace_of(agent) or {}

    for name, _function in declarations.postconditions:
        if (
                name in namespace
                and name not in state.records
                and name not in state.actions
                and name != STATE
                ):
            raise TagCompositionError(
                    f"{tag.__name__}.{name} is a Post, but"
                    f" {_name_of(agent)} already holds a value called"
                    f" {name!r}; a Post is read by its name and cannot"
                    " share it"
                    )


def _inspect(
        agent: object,
        ) -> None:
    """Judge every visible Post after admission, reporting one final error."""

    state = _state_of(agent)

    if not state.postconditions:
        return   # nothing promised: nothing to inspect

    state.composing += 1

    from .post_queries import _post_evaluation
    try:
        failures: list[TagPostconditionError] = []
        with _post_evaluation():
            _inspect_posts(agent, state, failures)

        if len(failures) == 1:
            failures[0].failed_posts = (failures[0].name,)
            # Pop before raising: a raised error must not own an _inspect
            # frame whose locals still contain that same error and Agent.
            raise failures.pop()

        if failures:
            names = tuple(error.name for error in failures)
            details = tuple(str(failure) for failure in failures)
            provenance = tuple((error.name, error.layer_provenance) for error in failures)
            failures.clear()
            failures.append(TaggingFailure(names, details))
            failures[0].layer_provenance = provenance
            for name, context in provenance:
                BaseException.add_note(failures[0], _post_context_note(name, context))
            raise failures.pop()
    finally:
        state.composing -= 1



def _inspect_posts(agent: object, state: _State,
                   failures: list[TagPostconditionError]) -> None:
    for name, check in tuple(state.postconditions.items()):
        try:
            _evaluate(
                    ((name, check),),
                    agent,
                    {},
                    TagPostconditionError,
                    "Postcondition",
                    post=True,
                    )
        except TagPostconditionError as error:
            context = _post_provenance(state, name, check)
            error.layer_provenance = context
            BaseException.add_note(error, _post_context_note(name, context))
            failures.append(error)



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
            or (state.arrestable and "__getattribute__" not in type(agent).__dict__)
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
        application: object,
        ) -> None:
    """Establish membership after the Tag's Gains have been prepared."""

    plans = None
    if state.pinned is not None and declarations.published:
        plans = _publication_plans(state.pinned, declarations.published)

    _field_of(tag)._Add(agent)
    state.active.append(tag)
    post_names = tuple(
            name
            for name, _function in declarations.postconditions
            if any(
                    layer.application is application
                    for layer in state.post_layers.get(name, ())
                    )
            )
    if post_names:
        state.post_applications[tag] = (application, post_names)
    state.words = None
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


def _imprint(
        agent: object,
        tag: type,
        declarations: _Declarations,
        inputs: dict[str, Any],
        failures: list[TagTrainingWarning],
        ) -> BaseException | None:
    for name, imprint in declarations.imprints:
        try:
            result = imprint(
                    agent,
                    **_protocol_inputs(imprint, inputs, 1),
                    )
            lazy = _discard_lazy_result(result)
        except Exception as error:
            try:
                cause_type = _type_name(error)
                cause_text = _exception_text(error)
                failure = TagImprintError.Named(name)(
                        f"Imprint {str.__str__(name)!r} failed:"
                        f" {cause_type}: {cause_text}"
                        )
                failures.append(
                        _training_warning(
                            "Imprint", tag, name, failure, error,
                            cause_type=cause_type,
                            cause_text=cause_text,
                            )
                        )
            except BaseException as interruption:
                return interruption
            continue
        except BaseException as interruption:
            return interruption

        if lazy is not None:
            article = "an" if lazy == "async generator" else "a"

            failure = TagImprintError.Named(name)(
                    f"Imprint {str.__str__(name)!r} returned {article}"
                    f" {lazy}; an Imprint must complete synchronously."
                    " TOP does not await or iterate application protocols."
                    )
            failures.append(
                    TagTrainingWarning.Named(name)(
                        "Imprint", tag, name, failure,
                        )
                    )

    return None



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
            }

    return _Snapshot(
            actions=dict(state.actions),
            records=records,
            reports=reports,
            operations=dict(state.operations),
            deleted=frozenset(state.deleted) if state.deleted else _NONE,
            secrets=frozenset(state.secrets) if state.secrets else _NONE,
            links=dict(state.links),
            )


def _report_training(
        failures: list[TagTrainingWarning],
        primary: BaseException | None,
        ) -> None:
    """Report each failed step after admission, without masking Posts or interrupts."""

    warning_errors: list[Exception] = []
    for failure in failures:
        try:
            warnings.warn(
                    failure,
                    skip_file_prefixes=_WARNING_SKIP_PREFIXES,
                    )
        except BaseException as error:
            # Warning filters and custom reporting hooks run after Field
            # entry. Neither may mask a failed Post or an interruption.
            if primary is not None:
                try:
                    BaseException.add_note(primary, str(error))
                except BaseException:
                    pass
            elif not isinstance(error, Exception):
                # A new Python interruption remains an interruption when
                # training and Posts themselves completed normally.
                raise
            elif warning_errors:
                try:
                    BaseException.add_note(warning_errors[0], str(error))
                except BaseException:
                    pass
            else:
                warning_errors.append(error)

    if failures:
        del failure
    failures.clear()
    if warning_errors:
        raise warning_errors.pop()



def _note_secondary(
        primary: BaseException,
        others: list[BaseException],
        label: str,
        ) -> None:
    """Keep secondary failures visible without retaining their tracebacks."""

    for error in others:
        try:
            BaseException.add_note(
                    primary,
                    f"{label}: {_type_name(error)}: {_exception_text(error)}",
                    )
        except BaseException:
            pass   # a diagnostic must not replace the primary failure



def _note_closing(
        primary: BaseException,
        others: list[tuple[str, BaseException]],
        ) -> None:
    """Record each later post-entry error without keeping its traceback."""

    for label, error in others:
        _note_secondary(primary, [error], label)



def _require_sound_source(agent: object, tag: type) -> None:
    """A missing Tag starts only from an Agent whose current Posts hold."""
    state = _state_of(agent)
    if state is not None and state.postconditions and not _holds_for_population(agent):
        raise TagCompositionError(
                f"{tag.__name__} cannot start Tagging while the"
                " Agent's current Posts fail"
                )


def _post_provenance(state: _State, name: str, check: Any) -> tuple[Any, ...]:
    """Diagnostic context only: no claim that every recorded layer failed."""
    return tuple(
            (str.__str__(type.__dict__["__name__"].__get__(layer.tag)),
             layer.constant,
             any(active is layer.tag for active in state.active),
             layer.underlay)
            for layer in state.post_layers.get(name, ())
            )


def _post_context_note(name: str, provenance: tuple[Any, ...]) -> str:
    if not provenance:
        return f"Post {str.__str__(name)!r} has no recorded Tag layer"
    visible = provenance[-1][0]
    retained = tuple(tag for tag, constant, admitted, _ in provenance
                     if constant and not admitted)
    note = f"Post {str.__str__(name)!r} is visible from Tag {visible}"
    if retained:
        note += "; Constant Post underlay retained after Rip: " + ", ".join(retained)
    return note


def _target_failure(agent: object, tag: type, error: TagCompositionError) -> TagTargetError:
    """Classify a failed first mechanical preparation without hiding its cause."""
    return TagTargetError(
            f"{tag.__name__} cannot tag {type(agent).__name__}: object is not a valid"
            f" Target for Tagging; {_exception_text(error)}"
            )
