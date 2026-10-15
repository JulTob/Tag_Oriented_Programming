"""Guard each continuation of a lazy Action or Operation result.

Native generators, coroutines and async generators may execute long after
their Action or Operation call returns. A protocol proxy checks the receiver
before *each* resumption, including send, throw and close. Denying a resume
leaves the source suspended, so a saved Rip can resume it through its door.

These are Python protocol objects, not native generator/coroutine objects:
``inspect.isgenerator`` and ``inspect.iscoroutine`` therefore return False.
The coroutine proxy implements ``collections.abc.Coroutine`` and is accepted
by ``asyncio.create_task``. A native wrapper would permanently unwind on a
denied resume and could execute the source's ``finally`` while arrested.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from collections.abc import Coroutine
from collections.abc import Generator
from types import AsyncGeneratorType
from types import CoroutineType
from types import GeneratorType
from typing import Any
from typing import Callable
from weakref import ref

from .arrest import _hold_lazy_result


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


class _Guarded_Generator(Generator):
    __slots__ = ("_source", "_guard")

    def __init__(self, source: Any, guard: _Guard) -> None:
        self._source = source
        self._guard = guard

    def __iter__(self):
        self._guard.check(self._source)
        return self

    def __next__(self):
        return self.send(None)

    def send(self, value):
        self._guard.check(self._source)
        return self._source.send(value)

    def throw(self, *args):
        self._guard.check(self._source)
        return self._source.throw(*args)

    def close(self):
        self._guard.check(self._source)
        return self._source.close()

    def __del__(self):
        self._guard.park(self._source)


class _Guarded_Coroutine(Coroutine):
    """Also wrap one step of an async generator, whose result is awaitable."""

    __slots__ = ("_source", "_iterator", "_guard")

    def __init__(self, source: Any, guard: _Guard) -> None:
        self._source = source
        self._iterator = None
        self._guard = guard

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
        return self._step().send(value)

    def throw(self, *args):
        self._guard.check(self._source)
        return self._step().throw(*args)

    def close(self):
        self._guard.check(self._source)
        iterator = self._iterator
        if iterator is None:
            # A native coroutine has a side-effect-free close before entry.
            # For an async-generator step, __await__ creates its driver but
            # does not start its body.
            iterator = self._step()
        return iterator.close()

    def __del__(self):
        self._guard.park(self._source)


class _Guarded_Async_Generator(AsyncGenerator):
    __slots__ = ("_source", "_guard")

    def __init__(self, source: Any, guard: _Guard) -> None:
        self._source = source
        self._guard = guard

    def __aiter__(self):
        self._guard.check(self._source)
        return self

    def __anext__(self):
        return self.asend(None)

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


_LAZY_TYPES = (
        GeneratorType, CoroutineType, AsyncGeneratorType,
        _Guarded_Generator, _Guarded_Coroutine, _Guarded_Async_Generator,
        )


def _guard_lazy_result(
        result: Any,
        receiver: object,
        act: str,
        authorize: _Check,
        ) -> Any:
    """Return an ordinary value unchanged; guard native and TOP lazy results.

    A published Operation passes through a Tag call and then an Agent Action.
    Nesting proxies keeps both receivers' arrest checks on every resume.
    """

    kind = type(result)
    if kind not in _LAZY_TYPES:
        return result

    guard = _Guard(receiver, act, authorize)
    if kind in (GeneratorType, _Guarded_Generator):
        return _Guarded_Generator(result, guard)
    if kind in (CoroutineType, _Guarded_Coroutine):
        return _Guarded_Coroutine(result, guard)
    return _Guarded_Async_Generator(result, guard)
