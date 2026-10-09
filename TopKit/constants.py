"""Constant bindings: protect names without freezing the objects they hold."""

from dataclasses import replace
from functools import partial
from typing import Any

from .declarations import STATE, _MISSING, _check_constant_shapes, _constant_owner
from .errors import TagCompositionError
from .state import _namespace_of, _state_of


def _refuse_constant(state, name: str) -> None:
    if state is not None and name in state.constants:
        origin, _kind, _declaration = state.constants[name]
        raise TagCompositionError(
                f"{origin.__name__}.{name} is Constant; its binding cannot"
                " be replaced or deleted"
                )


def _check_pin_lock(tag: type, name: str) -> None:
    """A new shared Constant must not arrive hidden by an existing Shape."""

    pending = list(type.__subclasses__(tag))
    seen = set()
    while pending:
        shape = pending.pop()
        if shape in seen:
            continue
        seen.add(shape)
        for earlier in shape.__mro__:
            if earlier is tag:
                break
            managed = earlier.__dict__.get(STATE)
            if name in earlier.__dict__ or (managed is not None and name in managed.constants):
                raise TagCompositionError(
                        f"{shape.__name__} already inherits {name!r} from {earlier.__name__};"
                        f" {tag.__name__} cannot acquire a hidden Constant"
                        )
        pending.extend(type.__subclasses__(shape))


def _constant_overlay(state, tag: type, declarations):
    """Validate all affected names before installation; retain old Constants.

    The returned declarations omit already installed, identical Constants.
    Internal shared names belong to their Tags, independently of Agent names.
    """

    if not state.constants and not declarations.constants and state.pinned is None:
        return declarations, {}

    for name in declarations.deletions:
        _refuse_constant(state, name)
        if state.pinned is not None and _constant_owner(state.pinned, name) is not None:
            raise TagCompositionError(f"{name!r} is Constant on the pinned Tag")
        if state.pinned is not None:
            _check_constant_shapes(state.pinned, name)

    kept = {}
    locks = {}
    for group, kind in (
            ("preconditions", "precondition"),
            ("postconditions", "postcondition"),
            ("actions", "action"),
            ("records", "record"),
            ("reports", "report"),
            ("operations", "operation"),
            ):
        entries = []
        for entry in getattr(declarations, group):
            name, original = entry[:2]
            shared = group in ("reports", "operations")
            visible = not shared or entry[2]
            old = state.constants.get(name)
            # Even an internal Report would replace a published Report's
            # origin in the registry used by its existing descriptor.
            affects = visible or (old is not None and kind == old[1] == "report")
            if old is not None and affects:
                same_kind = old[1] == kind or (
                        kind == "precondition" and old[1] == "postcondition"
                        )
                if (old[0] is tag and same_kind and old[2] is original
                        and name in declarations.constants):
                    continue
                _refuse_constant(state, name)

            if state.pinned is not None and not shared:
                _check_constant_shapes(state.pinned, name)
                owner = _constant_owner(state.pinned, name)
                if owner is not None:
                    raise TagCompositionError(
                            f"{owner.__name__}.{name} is Constant; a Pin cannot replace it"
                            )
                if name in declarations.constants:
                    _check_pin_lock(state.pinned, name)

            entries.append(entry)
            if visible and name in declarations.constants and kind != "precondition":
                locks[name] = (tag, kind, original)
        kept[group] = tuple(entries)
    return replace(declarations, **kept), locks


class _Constant_Gate:
    """A read-preserving data descriptor that refuses writes and deletion."""

    __slots__ = ("name", "member")

    def __init__(self, name: str, member: Any = _MISSING):
        self.name = name
        self.member = member

    def __get__(self, agent, owner=None):
        if agent is None:
            if self.member is not _MISSING:
                getter = getattr(type(self.member), "__get__", None)
                return getter(self.member, None, owner) if getter else self.member
            return self
        if self.member is not _MISSING:
            getter = getattr(type(self.member), "__get__", None)
            return getter(self.member, agent, type(agent)) if getter else self.member
        state = _state_of(agent)
        if state is not None and state.constants.get(self.name, (None, None))[1] == "postcondition":
            from .contracts import _condition_member
            return _condition_member(agent, state, self.name)
        namespace = _namespace_of(agent)
        if self.name in namespace:
            return namespace[self.name]
        raise AttributeError(self.name)

    def __set__(self, agent, value):
        _refuse_constant(_state_of(agent), self.name)
        _namespace_of(agent)[self.name] = value

    def __delete__(self, agent):
        _refuse_constant(_state_of(agent), self.name)
        _namespace_of(agent).pop(self.name, None)


class _Binding_Write:
    """Check protected bindings before a host or Action setter can run."""

    def __init__(self, fallback):
        self.fallback = fallback

    def __get__(self, agent, owner=None):
        return self if agent is None else partial(self, agent)

    def __call__(self, agent, name, *values):
        _refuse_constant(_state_of(agent), name)
        from .contracts import _refuse_condition_binding
        _refuse_condition_binding(agent, name)
        if issubclass(type(agent), type) and _constant_owner(agent, name) is not None:
            raise TagCompositionError(f"{name!r} is Constant on this Tag")
        if values and issubclass(type(agent), type):
            _check_constant_shapes(agent, name)
        getter = getattr(type(self.fallback), "__get__", None)
        bound = getter(self.fallback, agent, type(agent)) if getter else self.fallback
        return bound(name, *values)


def _binding_write_hooks(namespace, host_type):
    for name in ("__setattr__", "__delattr__"):
        fallback = namespace.get(name, _MISSING)
        if fallback is _MISSING:
            for owner in host_type.__mro__:
                if name in owner.__dict__:
                    fallback = owner.__dict__[name]
                    break
        if isinstance(fallback, _Binding_Write):
            fallback = fallback.fallback
        namespace[name] = _Binding_Write(fallback)
