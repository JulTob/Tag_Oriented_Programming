"""Tools: a Record whose value is an Agent of the Tags its declaration
names. What an Agent *has* (STEP-SPEC-36), beside what it *is* (a Tag)
and what it is *currently* (a Record).

Three laws, and nothing else:

1. the slot has a kind, checked at admission: when the slot is gained,
   and at every write, including ``object.__setattr__``;
2. the slot is never empty unless its kind says so, ``@Tool(Weapon | None)``;
3. the slot never Tags: the forge Tags the object, in plain sight.
"""

from __future__ import annotations

from types import NoneType
from types import UnionType
from typing import Any
from typing import NamedTuple
from typing import Union
from typing import get_args
from typing import get_origin

from .declarations import Report
from .declarations import _MISSING
from .declarations import _RIP
from .declarations import _TOOL
from .declarations import _has_flag
from .declarations import _is_pin
from .declarations import _kind_of
from .declarations import _mark
from .errors import TagCompositionError
from .errors import TagDeclarationError
from .fields import _Population
from .geometry import _is_tag
from .state import _name_of
from .state import _namespace_of
from .state import _state_of


class _Kind(NamedTuple):
    """What a Tool slot admits: a member of every Tag named, and the empty
    hand only when the declaration wrote ``| None``."""

    tags: tuple[type, ...]
    empty: bool

    def Spelled(
            kind,
            ) -> str:
        names = ", ".join(
                tag.__name__
                for tag in kind.tags
                )

        return f"{names} | None" if kind.empty else names


_DESCRIBED = {
        None: "unmarked",
        "action": "an Action",
        "precondition": "a Precondition",
        "postcondition": "a Postcondition",
        "condition": "a condition",
        "imprint": "an Imprint",
        "delete": "a Delete",
        "operation": "an Operation",
        "record": "a Record",
        "rip": "a Rip protocol",
        }


# ------------------------------------------------------------------
# Declaring
# ------------------------------------------------------------------


def _parts_of(
        given: Any,
        ) -> tuple[Any, ...]:
    """``Weapon | None`` is the language's own class union: its parts."""

    if get_origin(given) in (UnionType, Union):
        return get_args(given)

    return (given,)


def _spelled(
        part: Any,
        ) -> str:
    return getattr(
            part,
            "__name__",
            repr(part),
            )


def _kind_from(
        kinds: tuple[Any, ...],
        ) -> _Kind:
    """Read the Tags, and the ``None``, a ``@Tool(...)`` names."""

    if not kinds:
        raise TagDeclarationError(
                "@Tool names what the held thing is: @Tool(Weapon)"
                )

    tags: list[type] = []
    empty = False

    for given in kinds:
        if isinstance(given, _Population):
            raise TagDeclarationError(
                    "@Tool: a population is not a kind (a Tag in an operator"
                    " seat, as in Weapon | Blessed, ~Weapon or Weapon[:]);"
                    " write @Tool(Weapon, Blessed) for both, @Tool(Weapon | None)"
                    " for an empty hand"
                    )

        for part in _parts_of(given):
            if part is NoneType:
                empty = True
                continue

            if not _is_tag(part):
                raise TagDeclarationError(
                        f"@Tool({_spelled(part)}): {_spelled(part)} is not a"
                        " Tag; a Tool slot holds an Agent of a Tag"
                        )

            if _is_pin(part):
                raise TagDeclarationError(
                        f"@Tool({part.__name__}): {part.__name__} is a Pin,"
                        " whose Agents are Tags; a Tool slot holds an object"
                        " (§1.9)"
                        )

            if part not in tags:
                tags.append(part)

    if not tags:
        raise TagDeclarationError(
                "@Tool(None) names no Tag; a kind is one or more Tags,"
                " @Tool(Weapon | None) for an empty hand"
                )

    return _Kind(
            tuple(tags),
            empty,
            )


def Tool(
        *kinds: Any,
        ) -> Any:
    """Mark a Record whose value is an Agent of the Tags named: what the
    Agent *has*. ``@Tool(Weapon)`` alone declares the Record; ``@Record``
    may be written as well and restates it. ``@Tool(Weapon | None)``
    declares a slot that may be empty. Stacks with ``@Constant``,
    ``@Secret`` and ``@Public`` in either order::

        class Fighter(Tag):

            @Tool(Weapon)
            def weapon(agent):
                sword = Sword(f"{agent.name}'s sword")
                Weapon(sword)                   # the forge Tags it; the slot never does
                return sword
    """

    kind = _kind_from(kinds)

    def mark(
            member: Any,
            ) -> Any:
        if (
                isinstance(member, (classmethod, staticmethod, Report))
                or not callable(member)
                ):
            raise TagDeclarationError(
                    "@Tool declares what the Agent has, a Record: it marks a"
                    " builder, def weapon(agent)"
                    )

        existing = _kind_of(member)

        if _has_flag(member, _RIP):
            existing = "rip"

        if existing not in (None, "record"):
            raise TagDeclarationError(
                    f"{member.__name__}: @Tool declares what the Agent has,"
                    f" a Record; {member.__name__} is"
                    f" {_DESCRIBED.get(existing, existing)}"
                    )

        _mark(
                member,
                "record",
                )
        setattr(
                member,
                _TOOL,
                kind,
                )

        return member

    return mark


# ------------------------------------------------------------------
# Admission
# ------------------------------------------------------------------


def _shown(
        value: Any,
        ) -> str:
    text = repr(value)

    if len(text) > 40:
        text = text[:37] + "..."

    return f"{text} ({type(value).__name__})"


def _refuse_misfit(
        state: Any,
        name: str,
        value: Any,
        agent: object,
        built: bool = False,
        ) -> None:
    """Admit only the slot's kind: a member of every Tag, never the
    bearer, and None only where the kind says so. ``built`` words the
    refusal for what a builder returned rather than for a write."""

    slot = None if state is None else state.tools.get(name)

    if slot is None:
        return

    origin, kind = slot
    where = f"{origin.__name__}.{name}"

    if value is None:
        if kind.empty:
            return

        if built:
            raise TagCompositionError(
                    f"{where} returned None; its slot is never empty: return"
                    f" a Target, drop with del agent.{name}, or declare the"
                    f" empty hand, @Tool({kind.Spelled()} | None)"
                    )

        raise TagCompositionError(
                f"{where} is never empty; drop it with"
                f" del {_name_of(agent).lower()}.{name}, or declare the empty"
                f" hand, @Tool({kind.Spelled()} | None)"
                )

    if value is agent:
        first = kind.tags[0].__name__
        raise TagCompositionError(
                f"{where}: a Tool is something the Agent has, never the"
                f" Agent; to make it a {first}, Tag it: {first}(agent)"
                )

    held = _state_of(value)

    for tag in kind.tags:
        if held is not None and tag in held.active:
            continue

        if held is not None and tag in held.ever:
            raise TagCompositionError(
                    f"{where} holds a Tool of {tag.__name__}; this"
                    f" {type(value).__name__} left {tag.__name__}"
                    )

        if built:
            advice = f"Tag it in the builder, {tag.__name__}(...)"
        else:
            advice = (
                    f"Tag it first, {tag.__name__}(...), or hand over a"
                    f" {tag.__name__}"
                    )

        raise TagCompositionError(
                f"{where} holds a Tool of {tag.__name__}; {_shown(value)} is"
                f" not a {tag.__name__} now. {advice}"
                )


# ------------------------------------------------------------------
# The gate on the runtime type
# ------------------------------------------------------------------


class _Tool_Gate:
    """A data descriptor for a Tool slot: every write passes admission,
    ``object.__setattr__`` included. Reads and deletions go to the member
    beneath (a Constant or Secret gate) or to the Agent's own binding."""

    __slots__ = ("name", "member")

    def __init__(
            gate,
            name: str,
            member: Any = _MISSING,
            ) -> None:
        gate.name = name
        gate.member = member

    def __get__(
            gate,
            agent: object,
            owner: type | None = None,
            ) -> Any:
        if gate.member is not _MISSING:
            getter = getattr(
                    type(gate.member),
                    "__get__",
                    None,
                    )

            if getter is None:
                return gate.member

            return getter(
                    gate.member,
                    agent,
                    owner if agent is None else type(agent),
                    )

        if agent is None:
            return gate

        namespace = _namespace_of(agent)

        if gate.name in namespace:
            return namespace[gate.name]

        raise AttributeError(gate.name)

    def __set__(
            gate,
            agent: object,
            value: Any,
            ) -> None:
        _refuse_misfit(
                _state_of(agent),
                gate.name,
                value,
                agent,
                )

        setter = None

        if gate.member is not _MISSING:
            setter = getattr(
                    type(gate.member),
                    "__set__",
                    None,
                    )

        if setter is not None:
            setter(
                    gate.member,
                    agent,
                    value,
                    )
        else:
            _namespace_of(agent)[gate.name] = value

    def __delete__(
            gate,
            agent: object,
            ) -> None:
        deleter = None

        if gate.member is not _MISSING:
            deleter = getattr(
                    type(gate.member),
                    "__delete__",
                    None,
                    )

        if deleter is not None:
            deleter(
                    gate.member,
                    agent,
                    )
        else:
            _namespace_of(agent).pop(
                    gate.name,
                    None,
                    )
