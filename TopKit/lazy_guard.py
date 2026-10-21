"""Guard each continuation of a lazy Action or Operation result.

Native generators and coroutines may execute long after
their Action or Operation call returns. A protocol proxy checks the receiver
before *each* resumption, including send, throw and close. It also checks
after send and throw, so a result cannot escape if that continuation arrests
its receiver. Denying a resume leaves the source suspended, so a saved Rip
can resume it through its door.

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


class _Guard:
    __slots__ = ("receiver", "act", "authorize", "hold")

    def __init__(
            self,
            receiver: object,
            act: str,
            authorize: _Check,
            ) -> None:
        self.receiver = ref(receiver)
        self.act = act
        self.authorize = authorize
        self.hold = _hold_lazy_result

    def check(self, source: Any) -> None:
        receiver = self.receiver()
        if receiver is None:
            raise ReferenceError("the receiver of this lazy TOP act no longer exists")
        try:
            self.authorize(receiver, self.act)
        except BaseException:
            # A denied continuation leaves the source suspended. Keep that
            # source in the same Safehouse entry as its unfinished Rip so
            # dropping the proxy cannot run a generator's finally early.
            # Python interruptions in the retry path need the same rule.
            self.hold(receiver, source)
            raise

    def park(self, source: Any) -> None:
        """Dropping a started lazy result must not finalize it in custody."""

        receiver = self.receiver()
        if receiver is not None:
            self.hold(receiver, source)


def _checked_resume(guard: _Guard, source: Any, resume: Callable, *args: Any) -> Any:
    """Do not release a continuation result if it arrested its receiver."""

    try:
        result = resume(*args)
    except (StopIteration, StopAsyncIteration):
        # A completed generator or coroutine can carry a return value in
        # StopIteration. That value belongs behind the same custody check.
        guard.check(source)
        raise
    guard.check(source)
    return result


class _Guarded_Generator(Generator):
    __slots__ = ("_source", "_guard", "__name__", "__qualname__")

    def __init__(self, source: Any, guard: _Guard) -> None:
        self._source = source
        self._guard = guard
        self.__name__ = source.__name__
        self.__qualname__ = source.__qualname__

    def __iter__(self):
        self._guard.check(self._source)
        return self

    def __next__(self):
        return self.send(None)

    def send(self, value):
        self._guard.check(self._source)
        return _checked_resume(
                self._guard, self._source, self._source.send, value
                )

    def throw(self, *args):
        self._guard.check(self._source)
        return _checked_resume(
                self._guard, self._source, self._source.throw, *args
                )

    def close(self):
        self._guard.check(self._source)
        return _checked_resume(self._guard, self._source, self._source.close)

    def __del__(self):
        self._guard.park(self._source)


class _Guarded_Coroutine(Coroutine):
    """Guard every resumption of a native coroutine."""

    __slots__ = ("_source", "_iterator", "_guard", "__name__", "__qualname__")

    def __init__(self, source: Any, guard: _Guard) -> None:
        self._source = source
        self._iterator = None
        self._guard = guard
        self.__name__ = getattr(source, "__name__", "<async continuation>")
        self.__qualname__ = getattr(source, "__qualname__", self.__name__)

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
        return _checked_resume(
                self._guard, self._source, self._step().send, value
                )

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
        return _checked_resume(
                self._guard, self._source, self._step().throw, *args
                )

    def close(self):
        self._guard.check(self._source)
        iterator = self._iterator
        if iterator is None:
            # A native coroutine has a side-effect-free close before entry.
            iterator = self._step()
        return _checked_resume(self._guard, self._source, iterator.close)

    def __del__(self):
        self._guard.park(self._source)


class _Guarded_AsyncGenerator:
    __slots__ = ("_source", "_guard", "__name__", "__qualname__")

    def __init__(self, source: Any, guard: _Guard) -> None:
        self._source = source
        self._guard = guard
        self.__name__ = source.__name__
        self.__qualname__ = source.__qualname__

    def __aiter__(self):
        self._guard.check(self._source)
        return self

    def __anext__(self):
        self._guard.check(self._source)
        return _Guarded_Coroutine(self._source.__anext__(), self._guard)

    def asend(self, value):
        self._guard.check(self._source)
        return _Guarded_Coroutine(self._source.asend(value), self._guard)

    def athrow(self, *args):
        self._guard.check(self._source)
        return _Guarded_Coroutine(self._source.athrow(*args), self._guard)

    def aclose(self):
        self._guard.check(self._source)
        return _Guarded_Coroutine(self._source.aclose(), self._guard)

    def __del__(self):
        self._guard.park(self._source)


def _guard_lazy_result(
        result: Any,
        receiver: object,
        act: str,
        authorize: _Check,
        ) -> Any:
    """Check the receiver after its call and guard supported lazy results.

    A published Operation passes through a Tag call and then an Agent Action.
    Nesting proxies keeps both receivers' arrest checks on every resume.
    A started result must enter custody before a new arrest can deny its
    return: dropping it otherwise runs its finalizer outside the Rip door.
    """

    kind = type(result)
    generator = kind is GeneratorType or kind is _Guarded_Generator
    coroutine = kind is CoroutineType or kind is _Guarded_Coroutine
    async_generator = kind is AsyncGeneratorType or kind is _Guarded_AsyncGenerator
    lazy = generator or coroutine or async_generator
    if _safehouse:
        try:
            authorize(receiver, act)
        except BaseException:
            if lazy:
                _hold_lazy_result(receiver, result)
            raise

    if not lazy:
        return result

    guard = _Guard(receiver, act, authorize)
    if generator:
        return _Guarded_Generator(result, guard)
    if async_generator:
        return _Guarded_AsyncGenerator(result, guard)
    return _Guarded_Coroutine(result, guard)
