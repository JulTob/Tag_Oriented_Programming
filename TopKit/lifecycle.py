"""Lifecycle: Rip, teardown, Scope, and exit protocols.

Rip ends active membership. Contributions are sticky: Actions and Records
stay on the Agent (a Rogue Agent) unless the Tag's @Rip teardowns change
them. Ripping a Base is refused while an active Shape still requires it.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from typing import Iterator
import atexit
import sys
import weakref

from .declarations import _parameters_of
from .declarations import _takes_underlay
from .errors import TagCompositionError
from .errors import TagError
from .errors import TagResolutionError
from .fields import _Member
from .geometry import _requiring_shapes
from .state import _Originals
from .state import _State
from .state import _name_of
from .state import _state_of


def _rip(
        agent: object,
        tag: type,
        ) -> object:
    state = _state_of(agent)

    if state is None or tag not in state.active:
        raise TagResolutionError(
                f"{tag.__name__} is not active on this Agent"
                )

    blocking = _requiring_shapes(
            tag,
            state.active,
            )

    if blocking:
        names = ", ".join(
                shape.__name__
                for shape in blocking
                )

        raise TagCompositionError(
                f"{tag.__name__} is required by active Shape(s): {names}"
                )

    state.active.remove(tag)
    state.words = None
    state.snapshots.pop(tag, None)   # a view needs membership: never read again
    tag._topkit_field.Remove(agent)

    _teardown(
            agent,
            state,
            tag,
            )

    return agent


def _teardown(
        agent: object,
        state: _State,
        tag: type,
        ) -> None:
    """Run every @Rip teardown of ``tag`` once, then report failures."""

    teardowns = state.rips.pop(tag, ())
    failures: list[tuple[str, Exception]] = []
    state.composing += 1

    try:
        for teardown in teardowns:
            try:
                _call_teardown(
                        teardown,
                        agent,
                        state,
                        )
            except Exception as error:
                failures.append(
                        (
                            teardown.__name__,
                            error,
                            )
                        )
    finally:
        state.composing -= 1

    if failures:
        names = ", ".join(
                name
                for name, _error in failures
                )

        raise TagCompositionError(
                f"{tag.__name__} teardown failed in: {names}"
                ) from failures[0][1]


_Failure = tuple[type, Any, Exception]   # the Tag, the teardown, its error


def _teardown_all(
        agent: object,
        failures: list[_Failure],
        ) -> None:
    """Best-effort teardown of every still-active Tag (finalizer, exit):
    every teardown still due runs, once, while the Agent is still a
    member. Each failure is added to ``failures``, the caller's list, for
    the caller to report once everything else has run (STEP-SPEC-18,
    amended); an interruption leaves what was gathered there."""

    state = _state_of(agent)

    if state is None:
        return

    state.composing += 1   # teardowns run inside the composition door, as on a Rip

    try:
        for tag in reversed(list(state.active)):
            for teardown in state.rips.pop(tag, ()):
                try:
                    _call_teardown(
                            teardown,
                            agent,
                            state,
                            )
                except Exception as error:
                    failures.append(
                            (
                                tag,
                                teardown,
                                error,
                                )
                            )
    finally:
        state.composing -= 1


def _unraisable_type() -> type:
    """The type ``sys.unraisablehook`` receives (``UnraisableHookArgs``).
    Python does not export it, so one report is provoked under a hook
    that keeps its type: a weak reference whose callback raises."""

    kinds: list[type] = []
    missing = object()
    hook = getattr(sys, "unraisablehook", missing)   # a program may have removed it: Python's default then
    sys.unraisablehook = lambda report: kinds.append(type(report))

    try:
        def Raise(
                reference: object,
                ) -> None:
            raise RuntimeError("probe")

        probe: set[int] = set()
        reference = weakref.ref(probe, Raise)
        del probe
    finally:
        if hook is missing:
            del sys.unraisablehook   # left as it was found
        else:
            sys.unraisablehook = hook

    return kinds[0]   # CPython 3.12 and later always report it


_Unraisable = _unraisable_type()


def _report_failures(
        agent: object,
        failures: list[_Failure],
        occasion: str = "deleting",
        ) -> None:
    """Each failed teardown, reported as Python reports a finalizer's
    error: through ``sys.unraisablehook``, naming the teardown, its Tag
    and the Agent, with the ``occasion`` (``deleting``, or ``in the
    At_Exit pass of``). Nothing is stopped by it. The failures are dropped once
    reported: an error's traceback holds ``_teardown_all``'s frame, which
    holds the list that holds the error, a cycle whose frames hold the
    Agent; kept, it would resurrect the Agent until a collection."""

    try:
        for tag, teardown, error in failures:
            _report_failure(
                    agent,
                    tag,
                    teardown,
                    error,
                    occasion,
                    )
    finally:
        failures.clear()


def _report_failure(
        agent: object,
        tag: type,
        teardown: Any,
        error: Exception,
        occasion: str,
        ) -> None:
    _report_error(
            error,
            f"Exception ignored in teardown {teardown.__name__} of"
            f" {tag.__name__}, {occasion} {_name_of(agent)}",
            teardown,
            )


def _report_layer_failure(
        agent: object,
        error: BaseException,
        layer: Any,
        ) -> None:
    """A ``__del__`` Layer's own error, when an interrupted teardown must
    be raised after it: raising the interruption would hide it, so the
    kit reports it as Python would have (STEP-SPEC-18, item 7)."""

    _report_error(
            error,
            f"Exception ignored in __del__, deleting {_name_of(agent)}",
            layer,
            )


def _report_error(
        error: BaseException,
        message: str,
        source: Any,
        ) -> None:
    """``error`` reported as Python reports a finalizer's: through
    ``sys.unraisablehook``, or Python's default hook where it is ``None``
    or missing, as Python does. A hook that raises stops nothing: its own
    error goes to the default hook, as Python reports it, and a failure
    there is dropped, as Python drops it."""

    hook = getattr(sys, "unraisablehook", None) or sys.__unraisablehook__

    try:
        hook(
                _Unraisable(
                    (
                        type(error),
                        error,
                        error.__traceback__,
                        message,
                        source,
                        )
                    )
                )
    except BaseException as failed:   # a hook that raises stops nothing: Python reports it as its own
        try:
            sys.__unraisablehook__(
                    _Unraisable(
                        (
                            type(failed),
                            failed,
                            failed.__traceback__,
                            "Exception ignored in sys.unraisablehook",
                            hook,
                            )
                        )
                    )
        except BaseException:
            pass   # as Python does: the default hook's own failure is dropped


def _call_teardown(
        teardown: Any,
        agent: object,
        state: _State,
        ) -> None:
    """Run one @Rip teardown. On a pinned Tag, a teardown that declares a
    seat after the receiver (and after its Underlay, if it takes one)
    receives the Tag's original declarations, so un-patching is
    ``tag.Control = original.Control``."""

    if state.pinned is None:
        teardown(agent)
        return

    declared = getattr(
            teardown,
            "__wrapped__",
            teardown,
            )
    seats = _parameters_of(declared).positional
    receiver_seats = 2 if _takes_underlay(declared) else 1

    if seats > receiver_seats:
        teardown(
                agent,
                _Originals(state.originals),
                )
    else:
        teardown(agent)


@contextmanager
def Scope(
        agent: object,
        *tags: type,
        **inputs: Any,
        ) -> Iterator[object]:
    """Apply Tags for a block and Rip them, in reverse, on exit, even if
    the block raises. The guaranteed teardown path.

    It Rips the Tags it names that it applied, and only those. A Tag the
    Agent already carries when the Scope reaches it is left as it was,
    and the block still runs. A Tag that applied and then failed at the
    door, through its Postcondition or its Imprint, did apply, so it is
    Ripped on the way out like any other. A Base pulled in with a Shape
    stays, even when the Scope names it after that Shape: the Agent
    already carries it by then. When a Shape the Scope names fails at
    the door through its Base's Imprint, the Shape never lands, and the
    Base it pulled in stays after the Scope raises. Whether the Scope
    should Rip such a Base is open in STEP-SPEC-6. A Tag the block
    itself Ripped is not Ripped again.

    On the way out, a Rip the Scope cannot make is reported as a Rip
    reports it, once every Rip is done: a Rip refused because a Shape
    that arrived in the block requires the Tag leaves that Tag, and a
    teardown that fails ends the membership all the same. When the block
    ended without an exception, the first such Composition Failure
    leaves the ``with``, with the others as its notes; when it raised,
    its own exception leaves, with each failure as a note (STEP-SPEC-6,
    drafted for the Director's confirmation).
    """

    applied: list[type] = []
    leaving: BaseException | None = None

    try:
        for tag in tags:
            if _carries(agent, tag):
                continue                    # already the Agent's: not the Scope's to take away

            try:
                tag(
                        agent,
                        **inputs,
                        )
            except BaseException:
                if _carries(agent, tag):
                    applied.append(tag)     # applied, then failed at the door: still the Scope's to Rip

                raise

            applied.append(tag)

        yield agent
    except BaseException as error:
        leaving = error
        raise
    finally:
        refused = _rip_all(
                agent,
                applied,
                )

        try:
            if refused:
                _report(
                        refused,
                        leaving,
                        )
        finally:
            refused = leaving = None        # an exception held by its own frame would keep the Agent in a cycle


def _rip_all(
        agent: object,
        applied: list[type],
        ) -> list[TagError]:
    """Rip what a Scope applied, in reverse, each one tried whatever the
    others do; return the Rips that failed, as a Rip reports them."""

    refused: list[TagError] = []

    for tag in reversed(applied):
        if not _carries(agent, tag):
            continue                        # the block Ripped it: nothing left to take away

        try:
            _rip(
                    agent,
                    tag,
                    )
        except TagError as failure:
            refused.append(failure)

    try:
        return refused
    finally:
        del refused                         # the failures' tracebacks hold this frame


def _report(
        refused: list[TagError],
        leaving: BaseException | None,
        ) -> None:
    """Report the Rips a Scope could not make: as notes on the exception
    leaving the block, or, when the block ended without one, by raising
    the first, with the others as its notes."""

    first = leaving if leaving is not None else refused[0]

    try:
        for failure in refused:
            if failure is not first:
                first.add_note(f"On leaving the Scope: {type(failure).__name__}: {failure}")

        if leaving is None:
            raise first
    finally:
        first = failure = refused = leaving = None   # the raised failure's traceback holds this frame


def _carries(
        agent: object,
        tag: type,
        ) -> bool:
    """Whether the Tag is active on the Agent, sound or defective: what a
    Rip asks, never a population. A Tag whose promise broke at the door
    is still active (§0.6)."""

    state = _state_of(agent)

    return state is not None and tag in state.active


_exit_registry: dict[int, _Member] = {}   # by registration number; an entry leaves when its Agent dies
_exit_count = 0   # registrations so far; each one's number is its key


def _forget_exit(
        expired: _Member,
        ) -> None:
    _exit_registry.pop(expired.key, None)


def At_Exit(
        agent: object,
        ) -> object:
    """Also run the Agent's teardowns at normal interpreter exit, while it
    is still a member. A teardown that fails there is reported through
    ``sys.unraisablehook`` once that Agent's teardowns in the pass have
    run.

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
                failures: list[_Failure] = []

                try:
                    _teardown_all(
                            agent,
                            failures,
                            )   # the list is ours: an interruption leaves it filled
                finally:
                    _report_failures(
                            agent,
                            failures,
                            "in the At_Exit pass of",
                            )   # once this Agent's teardowns in the pass ran; its Layers run later, when it is deleted


atexit.register(_run_exit_protocols)
