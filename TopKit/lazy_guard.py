"""Guard each continuation of a lazy Action or Operation result.

Native generators and coroutines may execute long after
their Action or Operation call returns. A protocol proxy checks the receiver
before *each* resumption, including send, throw and close. It also checks
after send and throw, so a result cannot escape if that continuation arrests
its receiver. Denying a resume leaves the source suspended, so a saved Rip
can resume it through its door. An entered view may finish close/aclose
after membership ends, using a separate cleanup authorizer. Secret and
custody checks still apply on every cleanup step.

These are Python protocol objects, not native generator/coroutine objects:
``inspect.isgenerator`` and ``inspect.iscoroutine`` therefore return False.
They retain the source's ``__name__`` and ``__qualname__`` for diagnostics.
The coroutine proxy implements ``collections.abc.Coroutine`` and is accepted
by ``asyncio.create_task``. A native wrapper would permanently unwind on a
denied resume and could execute the source's ``finally`` while arrested.

Async-generator continuations use the same check. Python event-loop shutdown
may still close a native source directly through its async-generator registry;
that host-level finalization is outside this TOP proxy boundary.

If asyncio cancels a Task during arrest, the proxy reports cancellation to
the Task but retains the native coroutine in the Safehouse. The source's
``finally`` can run only after the Rip clears and the source is resumed or
closed through the authorized path.
"""

from __future__ import annotations

from asyncio import CancelledError
from collections.abc import Coroutine
from collections.abc import Generator
from types import AsyncGeneratorType
from types import CoroutineType
from types import GeneratorType
from typing import Any
from typing import Callable
from weakref import ref

from .arrest import _hold_lazy_result
from .arrest import _safehouse
from .errors import TagArrestedAccessError


_Check = Callable[[object, str], None]

# Only fixed native and private framework classes enter this table. Strong
# class references prevent ID reuse; identity guards avoid host type hooks.
# Looking up an ordinary return value never adds its type to the table.
_framework_lazy_types: dict[int, tuple[type, int, str | None]] = {}


def _register_lazy_proxy_types(
        generator: type, coroutine: type, async_generator: type, *,
        source_attribute: str | None = None,
        ) -> None:
    for kind, category in ((generator, 0), (coroutine, 1), (async_generator, 2)):
        _framework_lazy_types[id(kind)] = kind, category, source_attribute


class _Guard:
    __slots__ = ("receiver", "act", "authorize", "cleanup_authorize", "hold")

    def __init__(
            self,
            receiver: object,
            act: str,
            authorize: _Check,
            cleanup_authorize: _Check | None = None,
            ) -> None:
        self.receiver = ref(receiver)
        self.act = act
        self.authorize = authorize
        self.cleanup_authorize = authorize if cleanup_authorize is None else cleanup_authorize
        self.hold = _hold_lazy_result

    def check(self, source: Any, *, cleanup: bool = False) -> None:
        receiver = self.receiver()
        if receiver is None:
            raise ReferenceError("the receiver of this lazy TOP act no longer exists")
        try:
            authorize = self.cleanup_authorize if cleanup else self.authorize
            authorize(receiver, self.act)
        except BaseException:
            # A denied continuation leaves the source suspended. Keep that
            # source in the same Safehouse entry as its unfinished Rip so
            # dropping the proxy cannot run a generator's finally early.
            # Python interruptions in the retry path need the same rule.
            self.hold(receiver, source)
            raise

    def for_cleanup(self) -> _Guard:
        """Authorize only the returned close awaitable's continuation steps."""

        receiver = self.receiver()
        if receiver is None:
            raise ReferenceError("the receiver of this lazy TOP act no longer exists")
        return _Guard(receiver, self.act, self.cleanup_authorize)

    def park(self, source: Any) -> None:
        """Dropping a started lazy result must not finalize it in custody."""

        receiver = self.receiver()
        if receiver is not None:
            self.hold(receiver, source)


def _checked_resume(
        guard: _Guard, source: Any, resume: Callable, *args: Any,
        cleanup: bool = False,
        ) -> Any:
    """Do not release a continuation result if it arrested its receiver."""

    # Like an executing bound call, retain its receiver through the postcheck.
    # A Link may release its completed private Pair inside this continuation.
    receiver = guard.receiver()
    if receiver is None:
        guard.check(source, cleanup=cleanup)
    try:
        try:
            result = resume(*args)
        except (StopIteration, StopAsyncIteration):
            # A terminal value belongs behind the same custody check.
            guard.check(source, cleanup=cleanup)
            raise
        guard.check(source, cleanup=cleanup)
        return result
    finally:
        # A saved exception traceback must not keep the receiver alive.
        receiver = None


class _Guarded_Generator(Generator):
    __slots__ = ("_source", "_guard", "_closed", "__name__", "__qualname__")

    def __init__(self, source: Any, guard: _Guard) -> None:
        self._source = source
        self._guard = guard
        self._closed = False
        self.__name__ = source.__name__
        self.__qualname__ = source.__qualname__

    def __iter__(self):
        self._guard.check(self._source)
        return self

    def __next__(self):
        return self.send(None)

    def send(self, value):
        self._guard.check(self._source)
        try:
            return _checked_resume(self._guard, self._source, self._source.send, value)
        except (StopIteration, StopAsyncIteration):
            self._closed = True
            raise
        except BaseException:
            if _lazy_finished(self._source):
                self._closed = True
            raise

    def throw(self, *args):
        self._guard.check(self._source)
        try:
            return _checked_resume(self._guard, self._source, self._source.throw, *args)
        except (StopIteration, StopAsyncIteration):
            self._closed = True
            raise
        except BaseException:
            if _lazy_finished(self._source):
                self._closed = True
            raise

    def close(self):
        if self._guard.receiver() is None and (
                self._closed or _lazy_finished(self._source)):
            return None   # disposal already completed; no receiver or code remains
        self._guard.check(self._source, cleanup=True)
        try:
            result = _checked_resume(
                    self._guard, self._source, self._source.close, cleanup=True,
                    )
        except BaseException:
            if _lazy_finished(self._source):
                self._closed = True
            raise
        self._closed = True
        return result

    def __del__(self):
        self._guard.park(self._source)


class _Guarded_Coroutine(Coroutine):
    """Guard every resumption of a native coroutine."""

    __slots__ = ("_source", "_iterator", "_guard", "_closed", "_on_complete",
                 "_completion_source", "__name__", "__qualname__")

    def __init__(
            self, source: Any, guard: _Guard, *,
            on_complete: Callable[[bool], None] | None = None,
            completion_source: Any = None,
            ) -> None:
        self._source = source
        self._iterator = None
        self._guard = guard
        self._closed = False
        self._on_complete = on_complete
        self._completion_source = completion_source
        self.__name__ = getattr(source, "__name__", "<async continuation>")
        self.__qualname__ = getattr(source, "__qualname__", self.__name__)

    def _finished(self, exhausted: bool) -> None:
        self._closed = True
        completed = self._on_complete
        self._on_complete = None
        self._completion_source = None
        if completed is not None:
            completed(exhausted)

    def _failed(self) -> None:
        parent_closed = (self._completion_source is not None
                         and _lazy_finished(self._completion_source))
        if parent_closed or _lazy_finished(self._source):
            self._finished(parent_closed)

    def _step(self):
        if self._iterator is None:
            self._iterator = self._source.__await__()
        return self._iterator

    def __await__(self):
        self._guard.check(self._source)
        return self

    def __iter__(self):
        return self.__await__()

    def __next__(self):
        return self.send(None)

    def send(self, value):
        self._guard.check(self._source)
        try:
            return _checked_resume(self._guard, self._source, self._step().send, value)
        except (StopIteration, StopAsyncIteration) as stopped:
            self._finished(isinstance(stopped, StopAsyncIteration))
            raise
        except BaseException:
            self._failed()
            raise

    def throw(self, *args):
        try:
            self._guard.check(self._source)
        except TagArrestedAccessError:
            # asyncio cancels Tasks by throwing CancelledError into their
            # coroutine. The Guard has already parked the native source;
            # report a cancelled Task without delivering the exception to
            # that source (which would run its finally during arrest).
            cancellation = args[0] if args else None
            if cancellation is CancelledError:
                raise CancelledError from None
            if isinstance(cancellation, CancelledError):
                raise cancellation from None
            raise
        try:
            return _checked_resume(self._guard, self._source, self._step().throw, *args)
        except (StopIteration, StopAsyncIteration) as stopped:
            self._finished(isinstance(stopped, StopAsyncIteration))
            raise
        except BaseException:
            self._failed()
            raise

    def close(self):
        if self._guard.receiver() is None and (
                self._closed or _lazy_finished(self._source)):
            return None
        self._guard.check(self._source, cleanup=True)
        iterator = self._iterator
        if iterator is None:
            # Disposing an unstarted coroutine must not enter a nested
            # proxy's ordinary __await__ permission path merely to close it.
            iterator = self._source
        try:
            result = _checked_resume(
                    self._guard, self._source, iterator.close, cleanup=True,
                    )
        except BaseException:
            self._failed()
            raise
        self._closed = True
        # Closing an unfinished asend awaitable does not close its generator.
        self._on_complete = None
        self._completion_source = None
        return result

    def __del__(self):
        self._guard.park(self._source)


class _Guarded_AsyncGenerator:
    __slots__ = ("_source", "_guard", "_closed", "__name__", "__qualname__")

    def __init__(self, source: Any, guard: _Guard) -> None:
        self._source = source
        self._guard = guard
        self._closed = False
        self.__name__ = source.__name__
        self.__qualname__ = source.__qualname__

    def __aiter__(self):
        self._guard.check(self._source)
        return self

    def __anext__(self):
        self._guard.check(self._source)
        return _Guarded_Coroutine(
                self._source.__anext__(), self._guard, on_complete=self._step_finished,
                completion_source=self._source,
                )

    def asend(self, value):
        self._guard.check(self._source)
        return _Guarded_Coroutine(
                self._source.asend(value), self._guard, on_complete=self._step_finished,
                completion_source=self._source,
                )

    def athrow(self, *args):
        self._guard.check(self._source)
        return _Guarded_Coroutine(
                self._source.athrow(*args), self._guard, on_complete=self._step_finished,
                completion_source=self._source,
                )

    def aclose(self):
        if self._guard.receiver() is None and (
                self._closed or _lazy_finished(self._source)):
            return _finished_cleanup()
        self._guard.check(self._source, cleanup=True)
        return _Guarded_Coroutine(
                self._source.aclose(), self._guard.for_cleanup(),
                on_complete=self._close_finished,
                completion_source=self._source,
                )

    def _step_finished(self, exhausted: bool) -> None:
        if exhausted:
            self._closed = True

    def _close_finished(self, exhausted: bool) -> None:
        self._closed = True

    def __del__(self):
        self._guard.park(self._source)


async def _finished_cleanup() -> None:
    """Repeated disposal of a completed result has no user body to execute."""


_register_lazy_proxy_types(GeneratorType, CoroutineType, AsyncGeneratorType)
_register_lazy_proxy_types(
        _Guarded_Generator, _Guarded_Coroutine, _Guarded_AsyncGenerator,
        source_attribute="_source",
        )


def _lazy_kind_of(result: Any) -> int | None:
    """Recognize fixed trusted classes without calling host type hooks."""
    kind = type(result)
    entry = _framework_lazy_types.get(id(kind))
    return entry[1] if entry is not None and entry[0] is kind else None


def _lazy_finished(source: Any) -> bool:
    """Inspect closed frames only through fixed trusted private adapters."""
    while True:
        kind = type(source)
        if kind is GeneratorType:
            return source.gi_frame is None
        if kind is CoroutineType:
            return source.cr_frame is None
        if kind is AsyncGeneratorType:
            return source.ag_frame is None
        entry = _framework_lazy_types.get(id(kind))
        if entry is None or entry[0] is not kind or entry[2] is None:
            return False
        if (kind is _Guarded_Generator or kind is _Guarded_Coroutine
                or kind is _Guarded_AsyncGenerator):
            if object.__getattribute__(source, "_closed"):
                return True
        source = object.__getattribute__(source, entry[2])


def _guard_lazy_result(
        result: Any,
        receiver: object,
        act: str,
        authorize: _Check,
        *,
        cleanup_authorize: _Check | None = None,
        ) -> Any:
    """Check the receiver after its call and guard supported lazy results.

    A published Operation passes through a Tag call and then an Agent Action.
    Nesting proxies keeps both receivers' arrest checks on every resume.
    A started result must enter custody before a new arrest can deny its
    return: dropping it otherwise runs its finalizer outside the Rip door.
    """

    kind = type(result)
    entry = _framework_lazy_types.get(id(kind))
    category = entry[1] if entry is not None and entry[0] is kind else None
    lazy = category is not None
    if _safehouse:
        try:
            authorize(receiver, act)
        except BaseException:
            if lazy:
                _hold_lazy_result(receiver, result)
            raise

    if not lazy:
        return result

    guard = _Guard(receiver, act, authorize, cleanup_authorize)
    if category == 0:
        return _Guarded_Generator(result, guard)
    if category == 2:
        return _Guarded_AsyncGenerator(result, guard)
    return _Guarded_Coroutine(result, guard)
