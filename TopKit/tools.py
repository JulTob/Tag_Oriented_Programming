"""Opt-in class admission for a Record, independent of Tag membership."""

from dataclasses import dataclass
from inspect import getattr_static
from types import FunctionType, MethodType, UnionType
from typing import Any, Protocol

from .declarations import _KIND, _MISSING, _RIP, Report, _is_private
from .errors import TagCompositionError, TagDeclarationError, _exception_text, _type_name


_TOOL = "__topkit_tool__"
_NO_KIND = object()


def _target(member):
    if issubclass(type(member), Report):
        return member.builder
    if issubclass(type(member), (classmethod, staticmethod, MethodType)):
        return member.__func__
    return member


@dataclass(frozen=True)
class _Tool_Policy:
    classes: tuple[type, ...]
    nullable: bool

    def Check(self, value, owner: str, name: str) -> None:
        if value is None:
            admitted = self.nullable
        else:
            try:
                admitted = isinstance(value, self.classes)
            except Exception as error:
                raise TagCompositionError(
                        f"{owner}.{name}: @Tool class admission failed:"
                        f" {_type_name(error)}: {_exception_text(error)}"
                        ) from error
        if not admitted:
            names = " | ".join(
                    str.__str__(type.__dict__["__name__"].__get__(kind))
                    for kind in self.classes
                    )
            if self.nullable:
                names += " | None"
            raise TagCompositionError(
                    f"{owner}.{name}: @Tool requires {names}; got {_type_name(value)}"
                    )


def _tool_mark(kind):
    if issubclass(type(kind), (FunctionType, MethodType, classmethod, staticmethod, Report)):
        raise TagDeclarationError(
                "@Tool requires a Python host class policy in parentheses"
                )
    if kind is _MISSING:
        kind = _NO_KIND
    def Mark(member):
        target = _target(member)
        setattr(target, _TOOL, kind)
        if getattr(target, _KIND, None) in (None, "record"):
            setattr(target, _KIND, "record")
        return member
    return Mark


def _tool_policy(member):
    target = _target(member)
    policy = (target.__dict__.get(_TOOL, _MISSING) if type(target) is FunctionType
              else getattr_static(target, _TOOL, _MISSING))
    return policy if type(policy) is _Tool_Policy else None


def _validate_tool_binding(owner: str, name: str, member, *, pinned=False):
    """Validate marks at their declared name, including either stack order."""

    target = _target(member)
    kind = (target.__dict__.get(_TOOL, _MISSING) if type(target) is FunctionType
            else getattr_static(target, _TOOL, _MISSING))
    if kind is _MISSING:
        return
    if (pinned or _is_private(name)
            or issubclass(type(member), (Report, classmethod, staticmethod))
            or not callable(member)
            or getattr(target, _KIND, None) != "record"
            or getattr(target, _RIP, False)):
        raise TagDeclarationError(
                f"{owner}.{name}: @Tool modifies an Agent Record"
                )
    if type(kind) is _Tool_Policy:
        return

    from .tags import MetaTag

    members = kind.__args__ if type(kind) is UnionType else (kind,)
    classes = []
    nullable = False
    for member_kind in members:
        if member_kind is type(None):
            nullable = True
        elif (not issubclass(type(member_kind), type)
                or issubclass(type(member_kind), MetaTag)
                or member_kind is Any
                or (issubclass(type(member_kind), type(Protocol))
                    and type.__dict__["__dict__"].__get__(member_kind).get("_is_protocol", False))):
            raise TagDeclarationError(
                    f"{owner}.{name}: @Tool requires a Python host class"
                    " or native class union, with optional None; Tags and"
                    " populations are not host classes"
                    )
        else:
            classes.append(member_kind)
    if not classes:
        raise TagDeclarationError(
                f"{owner}.{name}: @Tool requires at least one Python host class"
                )
    setattr(target, _TOOL, _Tool_Policy(tuple(classes), nullable))


def _check_tool_write(agent, name: str, value):
    from .state import _state_of

    state = _state_of(agent)
    if state is None or name not in state.tools:
        return
    if name in state.secrets and state.composing == 0:
        raise AttributeError(f"{name!r} is a secret member")
    origin, policy = state.tools[name]
    owner = str.__str__(type.__dict__["__name__"].__get__(origin))
    policy.Check(value, owner, name)


class _Tool_Gate:
    """A shared descriptor reads the receiving Agent's effective policy."""

    __slots__ = ("name", "member")

    def __init__(self, name: str, member=_MISSING):
        self.name = name
        self.member = member

    def __get__(self, agent, owner=None):
        if agent is None:
            return self
        if self.member is not _MISSING:
            return self.member.__get__(agent, owner)
        from .state import _namespace_of
        namespace = _namespace_of(agent)
        if self.name in namespace:
            return namespace[self.name]
        raise AttributeError(self.name)

    def __set__(self, agent, value):
        _check_tool_write(agent, self.name, value)
        from .state import _namespace_of
        _namespace_of(agent)[self.name] = value

    def __delete__(self, agent):
        if self.member is not _MISSING:
            return self.member.__delete__(agent)
        from .state import _namespace_of
        _namespace_of(agent).pop(self.name, None)
