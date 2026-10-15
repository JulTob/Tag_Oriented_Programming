"""Private ledger and ordered retry for unfinished Rip work.

No public Rip path uses this module yet. The lifecycle supplies the actual
membership revocation and teardown invocation when Safehouse is activated.
The ledger is sequential; concurrent saves and retries need a separate
STEP-32 task-safety ruling before they can share an Agent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Callable

from .arrest import _Arrest
from .arrest import _arrest_of
from .arrest import _rip_door
from .arrest import _safehouse
from .errors import TagCompositionError
from .errors import TagResolutionError


@dataclass(slots=True, eq=False)
class _RipRun:
    """One Tag application's original teardown sequence and next step."""

    tag: type
    teardowns: tuple[tuple[str, Any], ...]
    cursor: int = 0
    running: bool = False
    revoked: bool = False


def _tag_name(tag: type) -> str:
    """Read the real name without a Tag metaclass getter hiding a failure."""

    return str.__str__(type.__dict__["__name__"].__get__(tag))


def _save_run(agent: object, run: _RipRun) -> None:
    """Hold a pending run by Agent identity, never host hash or equality."""

    if not run.teardowns:
        return

    arrest = _arrest_of(agent)

    if arrest is None:
        arrest = _Arrest(agent)
        arrest.runs.append(run)
        _safehouse[id(agent)] = arrest
        return

    arrest.runs.append(run)


def _pending_run(agent: object, tag: type) -> _RipRun | None:
    """Find the oldest unfinished application of this exact Tag class."""

    arrest = _arrest_of(agent)

    if arrest is not None:
        for run in arrest.runs:
            if run.tag is tag:
                return run

    return None


def _finish_run(agent: object, run: _RipRun) -> None:
    """Release only this completed run, then release an empty custody."""

    arrest = _arrest_of(agent)

    if arrest is None:
        return

    for index, pending in enumerate(arrest.runs):
        if pending is run:
            arrest.runs.pop(index)
            break
    else:
        return

    if not arrest.runs and dict.get(_safehouse, id(agent)) is arrest:
        _safehouse.pop(id(agent))


def _retry_arrested(
        agent: object,
        revoke: Callable[[_RipRun], None],
        invoke: Callable[[_RipRun, str, Any], None],
        ) -> object:
    """Drain live saved runs in order, including work created during retry.

    The caller supplies ordinary TOP membership revocation and Rip calling.
    A revocation that is interrupted must be safe to resume from its last
    boundary. The run remains held until all its teardowns complete.
    """

    if _arrest_of(agent) is None:
        raise TagResolutionError("this Agent has no saved Rip work")

    while (arrest := _arrest_of(agent)) is not None:
        _run_saved(agent, arrest.runs[0], revoke, invoke)

    return agent


def _run_saved(
        agent: object,
        run: _RipRun,
        revoke: Callable[[_RipRun], None],
        invoke: Callable[[_RipRun, str, Any], None],
        ) -> object:
    """Finish one chosen run, even when older work is also pending.

    An explicit Rip can perform its own new work before retrying older
    arrests. The root retry uses this same primitive in ledger order.
    """

    if run.running:
        raise TagCompositionError(
                f"{_tag_name(run.tag)} teardown is already running"
                )

    run.running = True

    try:
        with _rip_door(agent):
            if not run.revoked:
                revoke(run)
                run.revoked = True

            while run.cursor < len(run.teardowns):
                name, teardown = run.teardowns[run.cursor]

                try:
                    invoke(run, name, teardown)
                except Exception as error:
                    raise TagCompositionError(
                            f"{_tag_name(run.tag)} teardown failed in:"
                            f" {str.__str__(name)};"
                            " the Agent is arrested"
                            ) from error

                run.cursor += 1
    finally:
        run.running = False

    _finish_run(agent, run)

    return agent
