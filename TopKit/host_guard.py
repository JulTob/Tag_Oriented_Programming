"""Opt-in custody checks on ordinary Python Host instance methods.

The mark is placed on the Host class before an instance method can be
captured. It keeps the same class object and Python MRO. A method captured
before the first Tagging then remains capable of checking a later arrest.
"""

from __future__ import annotations

from functools import wraps
from inspect import isasyncgenfunction
from types import FunctionType
from typing import Any

from .arrest import _require_available
from .arrest import _safehouse
from .errors import TagDeclarationError
from .geometry import _is_tag_class
from .lazy_guard import _guard_lazy_result


_CLEANUP_HOOKS = frozenset((
        "__enter__", "__exit__", "__aenter__", "__aexit__",
        "__getbuffer__", "__release_buffer__",
        ))

# These are class creation/finalization hooks, not ordinary instance acts.
# Their direct-call policy is part of the open Safehouse design.
_CLASS_HOOKS = frozenset((
        "__new__", "__init_subclass__", "__class_getitem__",
        "__del__",
        ))


def _guarded_method(name: str, source: FunctionType) -> FunctionType:
    act = f"Host method {name}"

    @wraps(source)
    def Guarded(receiver: object, *args: Any, **kwargs: Any) -> Any:
        if _safehouse:
            _require_available(receiver, act)

        result = source(receiver, *args, **kwargs)

        # A Host method can catch its own failing Rip and try to return a
        # value. Its result must pass the same custody check as its entry.
        if _safehouse:
            _require_available(receiver, act)

        return _guard_lazy_result(result, receiver, act, _require_available)

    Guarded.__topkit_host_source__ = source
    return Guarded


def GuardedHost(host: type) -> type:
    """Mark a Host whose own instance functions must respect Rip custody.

    Decorate the completed class, outermost to ``@dataclass`` and similar
    class decorators. A class with context or buffer cleanup hooks is
    refused until their already-entered cleanup door is implemented.
    Python descriptors, class/static methods and unmarked Python Bases are
    outside this first, intentionally narrow profile.
    """

    if not isinstance(host, type):
        raise TagDeclarationError("GuardedHost needs a Python Host class")
    if _is_tag_class(host):
        raise TagDeclarationError(
                "GuardedHost marks a Python Host, not a Tag declaration"
                )

    namespace = dict(type.__getattribute__(host, "__dict__"))
    blocked = _CLEANUP_HOOKS.intersection(namespace)
    if blocked:
        name = sorted(blocked)[0]
        raise TagDeclarationError(
                f"{host.__name__}.{name} is a Host cleanup hook;"
                " GuardedHost has no entered cleanup door for it yet"
                )

    selected = tuple(
            (name, source)
            for name, source in namespace.items()
            if (
                    name not in _CLASS_HOOKS
                    and type(source) is FunctionType
                    and getattr(source, "__topkit_host_source__", None) is None
                    )
            )

    for name, source in selected:
        if isasyncgenfunction(source):
            raise TagDeclarationError(
                    f"{host.__name__}.{name} is an async generator;"
                    " its event-loop finalizer cannot yet be guarded"
                    )

    for name, source in selected:
        type.__setattr__(host, name, _guarded_method(name, source))

    return host
