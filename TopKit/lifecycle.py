"""Lifecycle: Rip, teardown, and exit protocols.

Rip ends active membership. Contributions are sticky: Actions and Records
stay on the Agent (a Rogue Agent) unless the Tag's @Rip teardowns change
them. Each Rip removes only the named Tag, even if a Shape stays active.
An explicit Post can require continued Base membership when needed.

Of the three deletion tiers (§3.2), the kit gives the finalizer's
teardowns and At_Exit. The guaranteed tier is the program's own: it tags
before ``try`` and Rips in ``finally`` (STEP-SPEC-31).
"""

from __future__ import annotations

from typing import Any
from types import MappingProxyType
import atexit

from .declarations import _is_link
from .arrest import _arrest_of
from .arrest import _may_act
from .declarations import _parameters_of
from .declarations import _action_chain
from .declarations import _discard_lazy_result
from .declarations import _Lazy_Rip_Guard
from .declarations import _lazy_rip_guard
from .declarations import _takes_underlay
from .declarations import STATE
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
from .state import _State
from .state import _real_namespace_of
from .state import _state_of


def _rip(
        agent: object,
        tag: type,
        *,
        retry_older: bool = True,
        ) -> object:
    """End this Tag's application, then finish older arrested work.

    If an old application of the same Tag still owes Rip, retry that
    application first. A new Tagging of the same Tag stays in its Field.
    """

    state = _state_of(agent)

    arrest = _arrest_of(agent)
    pending = _pending_run(agent, tag) if arrest is not None else None

    if pending is not None:
        _run_one(agent, state, pending)
        if retry_older and _arrest_of(agent) is not None and not _may_act(agent):
            _retry_arrested(agent)
        return agent

    if state is None or tag not in state.active:
        raise TagResolutionError(
                f"{tag.__name__} is not active on this Agent"
                )

    teardowns = state.rips.get(tag, ())

    if teardowns:
        # This exact tuple identifies the Tag application. A fresh
        # reTagging builds a new Rip tuple, even for the same declarations.
        run = _RipRun(tag, teardowns)
        run.member = _field_of(tag)._members.get(id(agent))
        # Publish the original work before the Agent leaves the Field.
        # A failing callback can then never strand an unrecorded suffix.
        _save_run(agent, run)
        _run_one(agent, state, run)
    else:
        # No callback can fail or remain unfinished. Keep ordinary Rip's
        # short path, including its one Field removal and sticky Gains.
        _field_of(tag)._Remove(agent)
        state.active.remove(tag)
        state.words = None
        state.snapshots.pop(tag, None)

    # An explicit other-Tag Rip runs its own protocol first. After it
    # succeeds, any older arrested work must clear before the Agent is free.
    if (
            retry_older
            and (teardowns or arrest is not None)
            and _arrest_of(agent) is not None
            and not _may_act(agent)
            ):
        _retry_arrested(agent)

    return agent


def _revoke_membership(
        agent: object,
        tag: type,
        ) -> tuple[_State, tuple[tuple[str, Any], ...]]:
    """End one membership and hand its saved Rip chain to the caller.

    The Safehouse path uses ``_revoke`` so it can recognize an old
    application's Rip tuple after a fresh Tagging. This simpler seam
    remains available to callers that own an ordinary active membership.
    """

    state = _state_of(agent)

    if state is None or tag not in state.active:
        raise TagResolutionError(
                f"{tag.__name__} is not active on this Agent"
                )

    state.active.remove(tag)
    state.words = None
    state.snapshots.pop(tag, None)
    _field_of(tag)._Remove(agent)

    return state, state.rips.pop(tag, ())


def _teardown(
        agent: object,
        state: _State,
        tag: type,
        teardowns: tuple[tuple[str, Any], ...],
        ) -> None:
    """Run the handed-over Rip chain without reading a fresh Tagging's state."""

    failures: list[tuple[str, Exception]] = []
    state.composing += 1

    try:
        for name, teardown in teardowns:
            try:
                _call_teardown(name, teardown, agent, state)
            except Exception as error:
                failures.append((name, error))
    finally:
        state.composing -= 1

    if failures:
        names = ", ".join(name for name, _error in failures)
        raise TagCompositionError(
                f"{tag.__name__} teardown failed in: {names}"
                ) from failures[0][1]


def _rip_field(tag: type) -> None:
    """Revoke the starting Field, then attempt its saved Rips.

    Every starting member enters pending custody before the first callback.
    A failure or interruption stops this invocation. Unfinished runs stay
    in their original Tag's Safehouse and can be retried by member; no
    cleanup order among Field members is part of the deletion contract.
    """

    field = _field_of(tag)
    initial = []

    for agent in list(field):
        # The first phase cannot call a Host property or dictionary hook.
        namespace = _real_namespace_of(agent)

        if namespace is None:
            state = None
        elif issubclass(type(namespace), dict):
            state = dict.get(namespace, STATE)
        else:  # a Pin's physical class namespace is a mappingproxy
            state = MappingProxyType.get(namespace, STATE)

        if state is None or not any(active is tag for active in state.active):
            raise TagResolutionError(
                    f"{_tag_name(tag)} is not active on this Agent"
                    )

        initial.append((
                agent,
                state,
                state.rips.get(tag, ()),
                field._members.get(id(agent)),
                ))

    pending = []

    for agent, state, teardowns, member in initial:
        # A single-Agent Rip may have saved this application before an
        # interruption left it in the Field. Reuse that run, not a second
        # copy of its teardown chain. A fresh Tagging has a different
        # Field seat, even if both applications have no @Rip declarations.
        run = _pending_unrevoked_run(agent, tag, teardowns, member)

        if run is None:
            run = _RipRun(tag, teardowns)
            run.member = member
            # Empty runs still hold custody until selected cleanup.
            _save_run(agent, run, hold_empty=True)

        _revoke(agent, state, run, bulk=True)
        pending.append((agent, state, run))

    for agent, state, run in pending:
        _run_one(agent, state, run)
        # A Field Rip is an explicit Rip for each starting member. Just
        # like _rip, finish older saved work for this Agent after its
        # chosen Tag's Rip, before moving to another Field member.
        if _arrest_of(agent) is not None and not _may_act(agent):
            _retry_arrested(agent)


def _retry_arrested(
        agent: object,
        *,
        orphaned_only: bool = False,
        ) -> object:
    """Retry saved Rip work; root deletion selects orphaned work only."""

    state = _state_of(agent)

    if state is None:
        raise TagResolutionError("this Agent has no TOP state for saved Rip work")

    state.composing += 1

    try:
        return _retry_saved_runs(
                agent,
                lambda run: _revoke(agent, state, run),
                lambda run, name, teardown: _call_teardown(
                        name, teardown, agent, state,
                        ),
                defer_running=_may_act(agent),
                orphaned_only=orphaned_only,
                )
    finally:
        state.composing -= 1


def _run_one(agent: object, state: _State, run: _RipRun) -> None:
    """Run a chosen Rip before older custody, retaining its failure seat."""

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


def _revoke(
        agent: object,
        state: _State,
        run: _RipRun,
        *,
        bulk: bool = False,
        ) -> None:
    """Remove one saved application before its teardown starts.

    Repeating a partly interrupted revocation is safe. A new Tagging may
    happen during the later Rip callbacks, after this boundary is marked.
    """

    if run.revoked:
        return

    # A reTagging installs a different weak Field seat. This also keeps
    # no-@Rip applications separate, whose teardown tuples are both ().
    field = _field_of(run.tag)
    member = field._members.get(id(agent))
    if run.member is not None and member is not None and member is not run.member:
        run.revoked = True
        return

    # The Rip tuple is this application identity. If the old membership
    # was removed before an interruption and the Agent reTagged, the new
    # application has a different tuple. Never revoke its fresh Field.
    if not bulk and state.rips.get(run.tag) is not run.teardowns:
        run.revoked = True
        return

    # Remove the Field seat before dropping active. Until active leaves,
    # another Tagging of this same Tag is still a no-op. If interrupted
    # later, the tuple and Field seat tell retry which application remains.
    field._Remove(agent)
    for index, active in enumerate(state.active):
        if active is run.tag:
            state.active.pop(index)
            break

    words = state.words
    snapshot = state.snapshots.get(run.tag)
    run.held = (words, snapshot)
    state.words = None
    state.snapshots.pop(run.tag, None)
    state.rips.pop(run.tag, None)
    run.revoked = True


def _teardown_all(
        agent: object,
        ) -> None:
    """Best-effort teardown of every still-active Tag (finalizer, exit)."""

    state = _state_of(agent)

    if state is None:
        return

    if state.links:
        from .links import _begin_ending   # links builds on this module

        _begin_ending(
                agent,
                state,
                )   # the Agent in hand fills the first seat of its own Links (STEP-SPEC-22 rule 8.3)

    state.composing += 1   # teardowns run inside the composition door, as on a Rip
    interrupted: BaseException | None = None

    try:
        for tag in reversed(list(state.active)):
            if interrupted is not None and not _is_link(tag):
                continue   # after an interruption only its exits from Links still run (STEP-SPEC-22 rule 8.4)

            if _is_link(tag):
                # A Contact's finalizer may be its last caller. Use the
                # ordinary saved Rip so a failed Pair teardown leaves the
                # Contact in its Link's Safehouse for later retry.
                try:
                    _rip(agent, tag, retry_older=False)
                except Exception:
                    pass
                except BaseException as error:
                    if interrupted is None:
                        interrupted = error
                continue

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
                except BaseException as error:
                    if interrupted is None:
                        interrupted = error
                    break   # preserve the ordinary Tag's interruption boundary; Link exits still follow
    finally:
        state.composing -= 1

        if state.links:
            from .links import _end_links   # links builds on this module

            try:
                _end_links(
                        agent,
                        state,
                        )   # after its own teardowns, its exits from other Links included (STEP-SPEC-22 rules 8.3, 8.6)
            except BaseException:
                if interrupted is None:
                    raise   # otherwise the first interrupt is the one raised, below

    try:
        if interrupted is not None:
            raise interrupted
    finally:
        interrupted = None   # never keep the Agent alive through a traceback that holds this frame


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
