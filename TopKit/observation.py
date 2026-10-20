"""Refuse guarded TOP acts while a Precondition or Postcondition is reading.

The boundary follows the current execution flow, including called Actions.
It does not isolate ordinary Python attribute writes or I/O.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from contextvars import Token
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


class _Pre_Read:
    __slots__ = ("active",)

    def __init__(self) -> None:
        self.active = True


_pre_reads: ContextVar[tuple[_Pre_Read, ...]] = ContextVar(
        "TopKit_precondition_reads",
        default=(),
        )


def _reading_pre() -> bool:
    return any(marker.active for marker in _pre_reads.get())


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


class _Observation:
    """Observe a check, including verdict and error rendering.

    Nested scopes share the first violation. A copied context may retain the
    token after this call, so deactivate it before resetting this context.
    """

    __slots__ = ("phase", "flow", "opened", "token")

    def __init__(self, phase: str) -> None:
        self.phase = phase
        self.flow: _Pre_Flow | None = None
        self.opened = False
        self.token: Token[_Pre_Flow | None] | None = None

    def __enter__(self) -> _Pre_Flow:
        flow = _pre_flow.get()
        self.opened = flow is None or not flow.active

        if self.opened:
            flow = _Pre_Flow(self.phase)
            self.token = _pre_flow.set(flow)

        self.flow = flow
        return flow

    def __exit__(self, exc_type, exc, traceback) -> bool:
        try:
            if (exc_type is None or issubclass(exc_type, Exception)) and (
                    self.flow.violation is not None
                    ):
                raise self.flow.violation
            return False
        finally:
            if self.opened:
                self.flow.active = False
                _pre_flow.reset(self.token)


def _observing(phase: str) -> _Observation:
    return _Observation(phase)


@contextmanager
def _pre_observation() -> Iterator[_Pre_Flow]:
    """Observe a Precondition, retaining the existing guarded TOP boundary."""

    # A copied execution context may share a Post session but not its epoch.
    from .contracts import _taint_post_memo

    _taint_post_memo()
    marker = _Pre_Read()
    token = _pre_reads.set((*_pre_reads.get(), marker))
    try:
        with _observing("a Precondition") as flow:
            yield flow
    finally:
        # Also taint a Post that began while this Pre was running and may
        # continue in a copied context after the Pre ends here.
        _taint_post_memo()
        marker.active = False
        _pre_reads.reset(token)


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
