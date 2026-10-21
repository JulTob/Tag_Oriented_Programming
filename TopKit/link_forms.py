"""Link declarations and their ordered, independently resolved Tag turns.

The Relation is a blueprint, not a Tag or a Contact Field. Symbolic bases
capture a TOP Form without constructing a Python MRO. An ordinary-only
header is first subject to Python's usual class-creation rules; the Link
decorator then keeps only its own declaration namespace in the blueprint.
"""

from __future__ import annotations

from .observations import _refuse_observed_act

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
from typing import Iterator

from .declarations import _check_rip_declarations
from .declarations import _name_checks
from .errors import TagDeclarationError
from .errors import TagResolutionError
from .fields import FIELD_SEAT
from .geometry import _is_tag_class
from .memo import _Tag_Memo
from .memo import _class_namespace
from .memo import _namespace_snapshot
from .tags import MetaTag
from .tags import Tag


_current_seats: ContextVar[tuple[object, object] | None] = ContextVar(
        "topkit_link_seats",
        default=None,
        )


class _Seat:
    """A declaration symbol, or the current Agent/Contact inside a protocol."""

    __slots__ = ("_index", "_name")

    def __init__(
            seat,
            index: int,
            name: str,
            ) -> None:
        object.__setattr__(seat, "_index", index)
        object.__setattr__(seat, "_name", name)

    def _current(seat) -> object:
        current = _current_seats.get()

        if current is None:
            raise TagResolutionError(
                    f"{seat._name} names a Link seat only inside a Link protocol"
                    )

        return current[seat._index]

    def __getattr__(
            seat,
            name: str,
            ) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)

        if _current_seats.get() is None:
            return _Selector(seat, (name,))

        return getattr(seat._current(), name)

    def __setattr__(seat, name: str, value: Any) -> None:
        setattr(seat._current(), name, value)

    def __delattr__(seat, name: str) -> None:
        delattr(seat._current(), name)

    def __call__(seat, *args: Any, **kwargs: Any) -> Any:
        return seat._current()(*args, **kwargs)

    def __bool__(seat) -> bool:
        return bool(seat._current())

    def __rmatmul__(seat, name: object) -> Any:
        return name @ seat._current()

    def __repr__(seat) -> str:
        if _current_seats.get() is None:
            return f"<Link seat {seat._name}>"

        return repr(seat._current())


agent = _Seat(0, "agent")
contact = _Seat(1, "contact")
_pair_view_type: type | None = None


def _resolve_seat(value: Any) -> Any:
    """Unwrap the two protocol symbols at public TOP Target boundaries."""

    if value is agent or value is contact:
        return value._current()
    if type(value) is _pair_view_type:
        return value._current()

    return value


@contextmanager
def _seat_context(
        owner: object,
        target: object,
        ) -> Iterator[None]:
    token = _current_seats.set(
            (
                _resolve_seat(owner),
                _resolve_seat(target),
                )
            )

    try:
        yield
    finally:
        _current_seats.reset(token)


@dataclass(frozen=True, slots=True)
class _Selector:
    seat: _Seat
    path: tuple[str, ...]

    def __getattr__(selector, name: str) -> "_Selector":
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)

        return _Selector(selector.seat, (*selector.path, name))

    def __mro_entries__(selector, bases: tuple[Any, ...]) -> tuple[type, ...]:
        return (_Link_Header,)

    def Resolve(selector, owner: object, target: object) -> Any:
        current = owner if selector.seat is agent else target

        for name in selector.path:
            current = getattr(current, name)

        return current

    def Spelled(selector) -> str:
        return ".".join((selector.seat._name, *selector.path))


@dataclass(frozen=True, slots=True)
class _Link_Reference:
    """A held Link coordinate owns neither its Agent nor an obsolete Link."""

    coordinate: Any

    def Resolve(reference) -> Any:
        return reference.coordinate.Resolve()


@dataclass(frozen=True, slots=True)
class _Captured_Header:
    name: str
    header: tuple[Any, ...]
    namespace: dict[str, Any]


class _Header_Meta(MetaTag):
    """A symbolic base captures declarations before Python MRO construction."""

    def __new__(
            meta,
            name: str,
            bases: tuple[type, ...],
            namespace: dict[str, Any],
            **kwargs: Any,
            ) -> _Captured_Header:
        _refuse_observed_act('create a Link declaration')

        if kwargs:
            raise TagDeclarationError(
                    f"{name}: a Link Form does not accept class keywords"
                    )

        return _Captured_Header(
                name,
                namespace.get("__orig_bases__", bases),
                namespace,
                )


# This one private base supplies the compatible metaclass for __mro_entries__.
# Its __new__ is deliberately bypassed; authored headers use _Header_Meta.
_Link_Header = type.__new__(
        _Header_Meta,
        "_Link_Header",
        (Tag,),
        {"__module__": __name__},
        )


@dataclass(eq=False, slots=True, weakref_slot=True)
class _Relation:
    name: str
    header: tuple[Any, ...]
    namespace: dict[str, Any]

    __topkit_kind__ = "relation"

    def __call__(relation, *args: Any, **kwargs: Any) -> Any:
        raise TagDeclarationError(
                f"{relation.name} is a Relation blueprint; call an Agent's"
                f" actual Link, agent.{relation.name}(contact)"
                )

    def __mro_entries__(relation, bases: tuple[Any, ...]) -> tuple[type, ...]:
        raise TagDeclarationError(
                f"{relation.name} is a Relation blueprint, not a Tag in a"
                f" Form; name an actual Link such as agent.{relation.name}"
                )


def _own_namespace(namespace: dict[str, Any]) -> dict[str, Any]:
    generated = ("__dict__", "__weakref__", "__orig_bases__", FIELD_SEAT)

    return {
            name: member
            for name, member in namespace.items()
            if name not in generated and type(member) is not _Tag_Memo
            }


def _header_part(name: str, part: Any) -> Any:
    if isinstance(part, _Selector):
        return part

    if not _is_tag_class(part):
        raise TagDeclarationError(
                f"{name}: each Link Form entry must name a Tag or an actual Link"
                )

    coordinate = _class_namespace(part).get("_topkit_link_coordinate")

    if coordinate is not None:
        return _Link_Reference(coordinate)

    return part


def Link(
        first: Any = None,
        second: Any = None,
        ) -> Any:
    """Declare a Relation as ``@Link(agent, contact)`` on its ordered Form."""

    if first is not agent or second is not contact:
        raise TagDeclarationError(
                "@Link declares its two seats as @Link(agent, contact)"
                )

    def Declare(given: Any) -> _Relation:
        _refuse_observed_act('create a Link declaration')

        if isinstance(given, _Captured_Header):
            name, header, namespace = given.name, given.header, given.namespace
        elif _is_tag_class(given):
            name = given.__name__
            header = given.__bases__
            namespace = _namespace_snapshot(given)
        else:
            raise TagDeclarationError(
                    "@Link(agent, contact) decorates a TOP Form declaration"
                    )

        own = _own_namespace(namespace)
        _check_rip_declarations(name, own)
        _name_checks(own, name)

        return _Relation(
                name,
                tuple(_header_part(name, part) for part in header if part is not Tag),
                own,
                )

    return Declare


def _resolve_header(
        relation: _Relation,
        owner: object,
        target: object,
        ) -> Iterator[type]:
    """Resolve each turn only when reached, after earlier Taggings finish."""

    owner, target = _resolve_seat(owner), _resolve_seat(target)

    for entry in relation.header:
        if isinstance(entry, _Selector):
            try:
                resolved = entry.Resolve(owner, target)
            except AttributeError as error:
                raise TagResolutionError(
                        f"{relation.name}: Link Form entry {entry.Spelled()}"
                        " is unavailable at its turn"
                        ) from error
        elif isinstance(entry, _Link_Reference):
            resolved = entry.Resolve()
        else:
            resolved = entry

        if not _is_tag_class(resolved):
            raise TagResolutionError(
                    f"{relation.name}: a Link Form entry did not resolve to a Tag"
                    )

        yield resolved
