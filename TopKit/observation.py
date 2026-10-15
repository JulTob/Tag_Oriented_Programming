"""Refuse TOP mutations while a Precondition is judging an Agent.

The boundary follows the current execution flow, including Actions a Pre
calls. It does not pretend to isolate ordinary Python objects or I/O.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any
from typing import Callable

from .errors import TagCompositionError


class _Pre_Flow:
    __slots__ = ("active", "violation")

    def __init__(self) -> None:
        self.active = True
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
                f"a Precondition may read and query, but cannot {act}"
                )

    raise flow.violation


def _observe_pre(
        check: Callable[[object, dict[str, Any]], Any],
        ) -> Callable[[object, dict[str, Any]], Any]:
    """Keep the first attempted TOP mutation fatal, even when caught.

    Nested Preconditions use the same flow. A copied context may retain the
    token after this call, so deactivate it before resetting this context.
    """

    def Observed_Pre(
            agent: object,
            inputs: dict[str, Any],
            ) -> Any:
        flow = _pre_flow.get()
        opened = flow is None or not flow.active

        if opened:
            flow = _Pre_Flow()
            token = _pre_flow.set(flow)

        try:
            try:
                result = check(agent, inputs)
            except Exception:
                if flow.violation is not None:
                    raise flow.violation
                raise

            if flow.violation is not None:
                raise flow.violation

            return result
        finally:
            if opened:
                flow.active = False
                _pre_flow.reset(token)

    return Observed_Pre
