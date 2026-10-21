"""Lifecycle: Rip, teardown, and exit protocols.

Rip ends active membership. Contributions are sticky: Actions and Records
stay on the Agent (a Rogue Agent) unless the Tag's @Rip teardowns change
them. Each Rip removes only the named Tag, even if a Shape stays active.

Of the three deletion tiers (§3.2), the kit gives the finalizer's
teardowns and At_Exit. The guaranteed tier is the program's own: it tags
before ``try`` and Rips in ``finally`` (STEP-SPEC-31).
"""

from __future__ import annotations

from typing import Any
from types import MappingProxyType
import atexit

from .observations import _refuse_observed_act

from .arrest import _arrest_of
from .arrest import _may_act
from .arrest import _safehouse
from .declarations import STATE
from .declarations import _parameters_of
from .declarations import _action_chain
from .declarations import _discard_lazy_result
from .declarations import _Lazy_Rip_Guard
from .declarations import _lazy_rip_guard
from .declarations import _takes_underlay
from .errors import TagCompositionError
from .errors import TagResolutionError
from .fields import _Member
from .fields import _field_of
from .rip_runs import _RipRun
from .rip_runs import _pending_run
from .rip_runs import _pending_unrevoked_run
from .rip_runs import _retry_arrested as _retry_saved_runs
from .rip_runs import _run_saved
from .rip_runs import _save_run
from .rip_runs import _tag_name
from .state import _Originals
from .state import _real_namespace_of
from .state import _State
from .state import _runtime_type_for
from .state import _set_runtime_type
from .state import _state_of


def _rip(
        agent: object,
        tag: type,
        *,
        retry_older: bool = True,
        ) -> object:
    """Rip one application, stopping at its first unfinished protocol.

    A saved old application is selected before a fresh membership of the
    same Tag. An explicit different-Tag Rip does its own work first, then
    retries older saved work for this Agent.
    """

    _refuse_observed_act('Rip a Tag')

    state = _state_of(agent)
    pending = _pending_run(agent, tag) if _safehouse else None

    if pending is None:
        if state is None or not (
                state.active and state.active[-1] is tag
                or any(active is tag for active in state.active)
                ):
            raise TagResolutionError(
                    f"{_tag_name(tag)} is not active on this Agent"
                    )

        if not state.rips.get(tag) and tag not in state.post_applications:
            # An ordinary empty application has no protocol or Post update
            # that can fail. Avoid allocating custody for its success path;
            # an injected interruption still records its exact Field seat.
            _rip_empty(agent, state, tag)
            if retry_older and _safehouse and _arrest_of(agent) is not None and not _may_act(agent):
                _retry_arrested(agent)
            return agent

        pending = _new_run(agent, state, tag)
        _save_run(agent, pending, hold_empty=True)

    if state is None:
        raise TagResolutionError("this Agent has no TOP state for saved Rip work")

    _run_one(agent, state, pending)

    if retry_older and _safehouse and _arrest_of(agent) is not None and not _may_act(agent):
        _retry_arrested(agent)

    return agent


def _rip_empty(agent: object, state: _State, tag: type) -> None:
    field = _field_of(tag)
    member = field._members.get(id(agent))
    words, snapshot = state.words, state.snapshots.get(tag)
    try:
        field._Remove(agent)
        if state.active and state.active[-1] is tag:
            state.active.pop()
        else:
            for index, active in enumerate(state.active):
                if active is tag:
                    state.active.pop(index)
                    break
        state.words = None
        state.snapshots.pop(tag, None)
    except BaseException:
        run = _RipRun(tag, ())
        run.member = member
        run.held = (words, snapshot)
        _save_run(agent, run, hold_empty=True)
        raise


def _rip_state(agent: object) -> _State | None:
    """Read physical TOP state without invoking Host namespace hooks."""

    namespace = _real_namespace_of(agent)

    if namespace is None:
        return None
    if issubclass(type(namespace), dict):
        return dict.get(namespace, STATE)
    return MappingProxyType.get(namespace, STATE)


def _new_run(agent: object, state: _State, tag: type) -> _RipRun:
    run = _RipRun(tag, state.rips.get(tag, ()))
    run.member = _field_of(tag)._members.get(id(agent))
    run.post_application = state.post_applications.get(tag)
    return run


def _revoke_membership(
        agent: object,
        tag: type,
        ) -> tuple[_State, tuple[tuple[str, Any], ...]]:
    """End an active application and hand its original Rip chain over.

    Callers retaining unfinished work must use the saved-run engine instead.
    """

    state = _rip_state(agent)
    if state is None or not any(active is tag for active in state.active):
        raise TagResolutionError(f"{_tag_name(tag)} is not active on this Agent")
    run = _new_run(agent, state, tag)
    _revoke(agent, state, run)
    return state, run.teardowns


def _rip_field(tag: type) -> None:
    """Revoke the whole starting Field before invoking any Rip protocol.

    A failure or interruption stops this invocation. Every unfinished run
    stays in custody and may be selected explicitly, independently of other
    Field members; the Field defines no cleanup-order obligation.
    """

    _refuse_observed_act('Rip a Field')

    pending = []
    for agent in _field_of(tag):
        state = _rip_state(agent)
        if state is None or not any(active is tag for active in state.active):
            raise TagResolutionError(f"{_tag_name(tag)} is not active on this Agent")
        teardowns = state.rips.get(tag, ())
        member = _field_of(tag)._members.get(id(agent))
        run = _pending_unrevoked_run(agent, tag, teardowns, member)
        if run is None:
            run = _new_run(agent, state, tag)
            _save_run(agent, run, hold_empty=True)
        pending.append((agent, state, run))

    # Publish every original application before any revocation can fail.
    for agent, state, run in pending:
        _revoke(agent, state, run)

    for agent, state, run in pending:
        _run_one(agent, state, run)
        if _arrest_of(agent) is not None and not _may_act(agent):
            _retry_arrested(agent)


def _retry_arrested(
        agent: object,
        *,
        orphaned_only: bool = False,
        ) -> object:
    """Finish saved work without starting a fresh Tagging or Rip."""

    _refuse_observed_act('retry saved Rip work')

    state = _rip_state(agent)
    if state is None:
        raise TagResolutionError("this Agent has no TOP state for saved Rip work")

    state.composing += 1
    try:
        return _retry_saved_runs(
                agent,
                lambda run: _revoke(agent, state, run),
                lambda run, name, teardown: _call_teardown(name, teardown, agent, state),
                defer_running=_may_act(agent),
                orphaned_only=orphaned_only,
                )
    finally:
        state.composing -= 1


def _run_one(agent: object, state: _State, run: _RipRun) -> None:
    state.composing += 1
    try:
        _run_saved(
                agent,
                run,
                lambda current: _revoke(agent, state, current),
                lambda current, name, teardown: _call_teardown(
                        name, teardown, agent, state,
                        ),
                )
    finally:
        state.composing -= 1


def _revoke(agent: object, state: _State, run: _RipRun) -> None:
    """Remove only the saved application, preserving any fresh reTagging.

    The sequence is idempotent after an interruption. STEP-SPEC-61's opaque
    application identity also lets an interrupted old Post removal finish
    without ending a newly admitted application's Posts.
    """

    if run.revoked:
        return

    field = _field_of(run.tag)
    member = field._members.get(id(agent))
    fresh = member is not None and member is not run.member

    if not run.held:
        names = run.post_application[1] if run.post_application is not None else ()
        run.held = (
                state.words,
                state.snapshots.get(run.tag),
                tuple(state.post_layers.get(name, ()) for name in names),
                tuple(state.postconditions.get(name) for name in names),
                )

    if not fresh:
        # The Field leaves first. Until active leaves, this same Tagging
        # still reads as already applied and cannot insert a fresh seat.
        field._Remove(agent)
        for index, active in enumerate(state.active):
            if active is run.tag:
                state.active.pop(index)
                break
        state.words = None
        state.snapshots.pop(run.tag, None)
        if state.rips.get(run.tag) is run.teardowns:
            state.rips.pop(run.tag, None)

    if run.post_application is not None:
        application, names = run.post_application
        if state.post_applications.get(run.tag) is run.post_application:
            state.post_applications.pop(run.tag, None)
        from .overlay import _remove_post_application
        _remove_post_application(
                state, application, keep_constants=True, names=names,
                )
        # Retry a failed representation update even if the Post layers were
        # already removed by the preceding interrupted attempt.
        next_type = _runtime_type_for(state)
        if type(agent) is not next_type:
            _set_runtime_type(agent, next_type)

    run.revoked = True


def _teardown_all(
        agent: object,
        ) -> None:
    """Best-effort teardown of every still-active Tag (finalizer, exit)."""

    state = _state_of(agent)

    if state is None:
        return

    state.composing += 1   # teardowns run inside the composition door, as on a Rip

    try:
        for tag in reversed(list(state.active)):
            for name, teardown in state.rips.pop(tag, ()):
                try:
                    _call_teardown(
                            name,
                            teardown,
                            agent,
                            state,
                            )
                except Exception:
                    pass
    finally:
        state.composing -= 1


def _call_teardown(
        name: str,
        teardown: Any,
        agent: object,
        state: _State,
        ) -> None:
    """Run one @Rip teardown. On a pinned Tag, a teardown that declares a
    seat after the receiver (and after its Underlay, if it takes one)
    receives the Tag's original declarations, so un-patching is
    ``tag.Control = original.Control``."""

    guard = _Lazy_Rip_Guard(
            name,
            _action_chain(teardown)
            )
    token = _lazy_rip_guard.set(guard)

    try:
        if state.pinned is None:
            result = teardown(agent)
        else:
            declared = getattr(
                    teardown,
                    "__wrapped__",
                    teardown,
                    )
            seats = _parameters_of(declared).positional
            receiver_seats = 2 if _takes_underlay(declared, name) else 1

            if seats > receiver_seats:
                result = teardown(
                        agent,
                        _Originals(state.originals),
                        )
            else:
                result = teardown(agent)
    finally:
        guard.active = False
        _lazy_rip_guard.reset(token)

    lazy = _discard_lazy_result(result)

    if guard.failures:
        raise guard.failures[0]

    if lazy is not None:
        article = "an" if lazy == "async generator" else "a"

        raise TagCompositionError(
                f"Rip protocol {str.__str__(name)!r} returned {article}"
                f" {lazy}; a Rip protocol must complete synchronously."
                " TOP does not await or iterate teardown protocols."
                )


_exit_registry: dict[int, _Member] = {}   # by registration number; an entry leaves when its Agent dies
_exit_count = 0   # registrations so far; each one's number is its key


def _forget_exit(
        expired: _Member,
        ) -> None:
    _exit_registry.pop(expired.key, None)


def At_Exit(
        agent: object,
        ) -> object:
    """Also run the Agent's teardowns at normal interpreter exit.

    Registration is weak: it never keeps the Agent alive, and it leaves
    the registry when the Agent dies.
    """

    _refuse_observed_act('register an At_Exit teardown')

    global _exit_count

    reference = _Member(
            agent,
            _forget_exit,
            )
    reference.key = _exit_count
    _exit_registry[reference.key] = reference
    _exit_count += 1

    return agent


def _run_exit_protocols() -> None:
    number = 0

    while number < _exit_count:   # registrations made during the pass are reached too
        reference = _exit_registry.get(number)
        number += 1

        if reference is not None:
            agent = reference()

            if agent is not None:
                _teardown_all(agent)


atexit.register(_run_exit_protocols)
