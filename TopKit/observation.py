"""Refuse TOP mutations while a Pre or Record builder is reading.

The boundary follows the current execution flow, including called Actions.
It does not isolate ordinary Python objects or I/O.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any
from typing import Callable

from .errors import TagCompositionError


class _Observation_Flow:
    """A flow-local read interval, reusable by nested observations."""

    __slots__ = ("active", "phase", "violation", "carrier", "token")

    def __init__(self, phase: str) -> None:
        self.active = False
        self.phase = phase
        self.violation: TagCompositionError | None = None
        self.carrier: _Observation_Flow = self

    def __enter__(self) -> _Observation_Flow:
        prior = _observation_flow.get()

        if prior is not None and prior.active:
            self.carrier = prior
            return prior

        self.active = True
        self.token = _observation_flow.set(self)
        return self

    def __exit__(
            self,
            error_type: type[BaseException] | None,
            error: BaseException | None,
            traceback: object,
            ) -> None:
        try:
            if (self.carrier.violation is not None
                    and (error_type is None
                         or issubclass(error_type, Exception))):
                raise self.carrier.violation
        finally:
            if self.active:
                self.active = False
                _observation_flow.reset(self.token)


_observation_flow: ContextVar[_Observation_Flow | None] = ContextVar(
        "TopKit_read_observation",
        default=None,
        )


def _refuse_observed_mutation(act: str) -> None:
    """Reject an explicit TOP state change before it can take effect."""

    flow = _observation_flow.get()

    if flow is None or not flow.active:
        return

    if flow.violation is None:
        flow.violation = TagCompositionError(
                f"{flow.phase} may read and query, but cannot {act}"
                )

    raise flow.violation


def _observing(phase: str) -> _Observation_Flow:
    """First attempted mutation wins, including one caught by user code.

    A copied context may retain the token, so the owner deactivates it at
    exit. Nested observations share the owner's first violation.
    """

    return _Observation_Flow(phase)


def _pre_observation() -> _Observation_Flow:
    """Observe a whole Pre read, including verdict and error rendering."""

    return _Observation_Flow("a Precondition")


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
