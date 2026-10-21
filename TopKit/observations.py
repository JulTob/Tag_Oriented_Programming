"""Read-only TOP observations follow the current execution flow.

Preconditions, Posts and Record calculations may query and call Actions.
Explicit TOP mutations are refused; ordinary Python writes and I/O remain
the author's responsibility. This is not an object sandbox.
"""

from __future__ import annotations

from contextvars import ContextVar

from .errors import TagCompositionError


class _ObservationViolation(TagCompositionError):
    """A TOP mutation attempted inside a read-only calculation."""


class _Observation:
    __slots__ = ("phase", "active", "carrier", "violation", "token")

    def __init__(self, phase: str) -> None:
        self.phase = phase
        self.active = False
        self.carrier = None
        self.violation: _ObservationViolation | None = None

    def __enter__(self) -> _Observation:
        previous = _observation.get()
        if previous is not None and previous.active:
            self.carrier = previous
            return previous
        self.carrier = self
        self.active = True
        self.token = _observation.set(self)
        return self

    def __exit__(
            self,
            error_type: type[BaseException] | None,
            error: BaseException | None,
            traceback: object,
            ) -> None:
        violation = self.carrier.violation
        if self.active:
            self.active = False
            # A saved copy_context must retain neither authority nor an
            # exception traceback owning the observed Agent after exit.
            self.violation = None
            _observation.reset(self.token)
        self.carrier = None
        if violation is not None and (error is None or isinstance(error, Exception)):
            raise violation


_observation: ContextVar[_Observation | None] = ContextVar(
        "topkit_read_observation", default=None,
        )


class _UnobservedCleanup:
    """Python finalization has its own cleanup, unrelated to the reader."""

    __slots__ = ("token",)

    def __enter__(self, flow=_observation) -> None:
        self.token = flow.set(None)

    def __exit__(self, error_type, error, traceback, flow=_observation) -> None:
        flow.reset(self.token)


def _unobserved_cleanup(cleanup=_UnobservedCleanup) -> _UnobservedCleanup:
    """Suspend the observation only for Python's best-effort finalizer.

    Context and factory defaults also keep finalization independent of module
    globals being cleared at interpreter shutdown.
    """

    return cleanup()


# The private constructor is itself the context-manager factory.
_observing = _Observation


def _refuse_observed_act(act: str) -> None:
    """Reject an explicit TOP mutation before changing any TOP state."""

    flow = _observation.get()
    if flow is None or not flow.active:
        return
    if flow.violation is None:
        flow.violation = _ObservationViolation(
                f"{flow.phase} may read and query, but cannot {act}"
                )
    raise flow.violation
