"""Refuse guarded TOP acts while a Precondition or Postcondition is reading.

The boundary follows the current execution flow, including called Actions.
It does not isolate ordinary Python attribute writes or I/O.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any
from typing import Callable
from typing import Iterator

from .errors import TagCompositionError


class _Pre_Flow:
    __slots__ = ("active", "phase", "violation")

    def __init__(self, phase: str) -> None:
        self.active = True
        self.phase = phase
        self.violation: TagCompositionError | None = None


_pre_flow: ContextVar[_Pre_Flow | None] = ContextVar(
        "TopKit_precondition_observation",
        default=None,
        )


def _refuse_pre_mutation(act: str) -> None:
    """Reject an explicit TOP state change before it can take effect."""

    flow = _pre_flow.get()

    if flow is None or not flow.active:
        return

    if flow.violation is None:
        flow.violation = TagCompositionError(
                f"{flow.phase} may read and query, but cannot {act}"
                )

    raise flow.violation


@contextmanager
def _observing(phase: str) -> Iterator[_Pre_Flow]:
    """Observe a check, including verdict and error rendering.

    Nested scopes share the first violation. A copied context may retain the
    token after this call, so deactivate it before resetting this context.
    """

    flow = _pre_flow.get()
    opened = flow is None or not flow.active

    if opened:
        flow = _Pre_Flow(phase)
        token = _pre_flow.set(flow)

    try:
        try:
            yield flow
        except Exception:
            if flow.violation is not None:
                raise flow.violation
            raise

        if flow.violation is not None:
            raise flow.violation
    finally:
        if opened:
            flow.active = False
            _pre_flow.reset(token)


@contextmanager
def _pre_observation() -> Iterator[_Pre_Flow]:
    """Observe a Precondition, retaining the existing guarded TOP boundary."""

    with _observing("a Precondition") as flow:
        yield flow


def _observe_pre(
        check: Callable[[object, dict[str, Any]], Any],
        ) -> Callable[[object, dict[str, Any]], Any]:
    """Guard a Pre called directly or through an Underlay."""

    def Observed_Pre(
            agent: object,
            inputs: dict[str, Any],
            ) -> Any:
        with _pre_observation():
            return check(agent, inputs)

    return Observed_Pre
