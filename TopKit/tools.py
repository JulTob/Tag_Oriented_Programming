"""Tools: a Record whose value is an object of a declared kind. What an
Agent *has* (STEP-SPEC-36), beside what it *is* (a Tag) and what it is
*currently* (a Record).

A kind is one or more **terms**, every one of which must hold; a term is
one or more alternatives, any of which admits the value:

    @Tool(Weapon)                # a member of the Tag Weapon, now
    @Tool(Sword)                 # an instance of the Python class Sword
    @Tool(Sword, Weapon)         # both: a Sword that is a Weapon
    @Tool(Sword | Staff)         # either class (Python's own union)
    @Tool(Weapon | None)         # the empty hand, declared

Three laws, and nothing else:

1. the slot has a kind, checked at admission: when the slot is gained,
   and at every write, ``object.__setattr__`` included;
2. the slot is never empty unless its kind says so, ``| None``;
3. the slot never Tags: the forge Tags the object, in plain sight.
"""

from __future__ import annotations

from types import NoneType
from types import UnionType
from typing import Any
from typing import NamedTuple
from typing import Protocol
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
from .declarations import _tool_kind_of_static
from .declarations import _tool_physical_dict
from .errors import TagCompositionError
from .errors import TagDeclarationError
from .fields import _Population
from .geometry import _is_tag
from .state import _name_of
from .state import _namespace_of
from .state import _state_of


class _Kind(NamedTuple):
    """What a Tool slot admits. Every term holds; a term holds when any
    of its alternatives admits the value. An alternative is a Tag (a
    member now) or a class (an instance). ``empty`` admits None."""

    terms: tuple[tuple[Any, ...], ...]
    empty: bool

    def Spelled(
            kind,
            ) -> str:
        spelled = ", ".join(
                _spelled_term(term)
                for term in kind.terms
                )

        return f"{spelled} | None" if kind.empty else spelled


def _spelled_term(
        term: tuple[Any, ...],
        ) -> str:
    return " | ".join(
            _spelled(alternative)
            for alternative in term
            )


def _spelled(
        part: Any,
        ) -> str:
    return getattr(
            part,
            "__name__",
            repr(part),
            )


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

_SPELLINGS = "a Tag, @Tool(Weapon), or a class, @Tool(Sword)"


# ------------------------------------------------------------------
# Declaring
# ------------------------------------------------------------------


def _parts_of(
        given: Any,
        ) -> tuple[Any, ...]:
    """``Sword | None`` is the language's own class union: its parts."""

    if get_origin(given) in (UnionType, Union):
        return get_args(given)

    return (given,)


def _is_root_tag(
        part: Any,
        ) -> bool:
    from .tags import Pin, Tag   # tags imports this module's neighbours

    return part is Tag or part is Pin


def _is_typing_construct(
        part: Any,
        ) -> bool:
    """``Any`` and ``Protocol`` classes have no plain instance test."""

    if part is Any:
        return True

    return Protocol in getattr(
            part,
            "__mro__",
            (),
            )


def _refuse_as_kind(
        part: Any,
        ) -> None:
    """Why ``part`` cannot be an alternative of a kind, if it cannot."""

    if _is_tag(part):
        if _is_pin(part):
            raise TagDeclarationError(
                    f"@Tool({part.__name__}): {part.__name__} is a Pin, whose"
                    " Agents are Tags; a Tool slot holds an object (§1.9)"
                    )

        return

    if _is_root_tag(part):
        raise TagDeclarationError(
                f"@Tool({part.__name__}): a declaration root names no kind; name the Tag the"
                " held thing is, @Tool(Weapon)"
                )

    if part is object:
        raise TagDeclarationError(
                "@Tool(object): a plain @Record already holds any object;"
                " name the class the held thing is, @Tool(Sword)"
                )

    if _is_typing_construct(part):
        raise TagDeclarationError(
                f"@Tool({_spelled(part)}): a typing construct has no instance"
                f" test; name {_SPELLINGS}"
                )

    if not isinstance(part, type):
        raise TagDeclarationError(
                f"@Tool({_spelled(part)}): {_spelled(part)} is not a Tag or a"
                f" class; a Tool slot holds an object of a kind: {_SPELLINGS}"
                )


def _kind_from(
        kinds: tuple[Any, ...],
        ) -> _Kind:
    """Read the terms, their alternatives, and the ``None``, that a
    ``@Tool(...)`` names."""

    if not kinds:
        raise TagDeclarationError(
                f"@Tool names what the held thing is: {_SPELLINGS}"
                )

    if len(kinds) == 1 and _is_builder_like(kinds[0]):
        raise TagDeclarationError(
                f"@Tool needs its kind in parentheses, {_SPELLINGS}, above"
                " the builder"
                )

    terms: list[tuple[Any, ...]] = []
    empty = False

    for given in kinds:
        if isinstance(given, _Population):
            raise TagDeclarationError(
                    "@Tool: a population is not a kind (a Tag in an operator"
                    " seat, as in Weapon | Blessed, ~Weapon or Weapon[:]);"
                    " write @Tool(Weapon, Blessed) for both, a common Base Tag"
                    " for either, @Tool(Weapon | None) for an empty hand"
                    )

        alternatives: list[Any] = []

        for part in _parts_of(given):
            if part is NoneType:
                empty = True
                continue

            _refuse_as_kind(part)

            if part not in alternatives:
                alternatives.append(part)

        if alternatives:
            terms.append(tuple(alternatives))

    if not terms:
        raise TagDeclarationError(
                "@Tool(None) names no kind; a kind is a Tag or a class,"
                " @Tool(Weapon | None) or @Tool(Sword | None) for an empty"
                " hand"
                )

    return _Kind(
            tuple(terms),
            empty,
            )


def _is_builder_like(
        given: Any,
        ) -> bool:
    """A bare ``@Tool`` on a def hands the def itself to ``Tool``."""

    if isinstance(given, (classmethod, staticmethod, Report)):
        return True

    return (
            callable(given)
            and not isinstance(given, type)
            and not _is_tag(given)
            and hasattr(given, "__code__")
            )


def Tool(
        *kinds: Any,
        ) -> Any:
    """Mark a Record whose value is an object of the kinds named: what the
    Agent *has*. ``@Tool(Weapon)`` alone declares the Record; ``@Record``
    may be written as well and restates it. A kind is a Tag (a member,
    now) or a Python class (an instance); several kinds all hold;
    ``| None`` declares a slot that may be empty. Stacks with
    ``@Constant``, ``@Secret`` and ``@Public`` in either order::

        class Fighter(Tag):

            @Tool(Sword, Weapon)        # a Sword that is a Weapon
            def weapon(agent, *, weapon):
                return weapon           # the forge Tagged it; the slot never does
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

        # A callable can implement the mark as a custom descriptor whose
        # getter later hides it. Keep a physical copy for Tag publication
        # and Record gaining. A native slot is physical storage too.
        if _tool_kind_of_static(member) is not kind:
            namespace = _tool_physical_dict(member)
            if namespace is None:
                raise TagDeclarationError(
                        "@Tool needs a physical mark on its callable"
                        )
            namespace[_TOOL] = kind

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


def _admits(
        alternative: Any,
        value: Any,
        where: str,
        ) -> bool:
    """One alternative's answer: a Tag asks membership now, a class asks
    the language's own instance test."""

    if _is_tag(alternative):
        held = _state_of(value)

        return (
                held is not None
                and alternative in held.active
                )

    try:
        return isinstance(value, alternative)
    except Exception as error:   # a metaclass's own __instancecheck__ may refuse
        raise TagCompositionError(
                f"{where}: the instance test of {alternative.__name__} failed:"
                f" {type(error).__name__}: {error}"
                ) from error


def _left(
        term: tuple[Any, ...],
        value: Any,
        ) -> Any:
    """The Tag of the term the value once belonged to, if any: a Rogue."""

    held = _state_of(value)

    if held is None:
        return None

    for alternative in term:
        if _is_tag(alternative) and alternative in held.ever:
            return alternative

    return None


def _advice(
        term: tuple[Any, ...],
        built: bool,
        ) -> str:
    tags = [
            alternative
            for alternative in term
            if _is_tag(alternative)
            ]

    if tags:
        first = tags[0].__name__

        if built:
            return f"Tag it before the builder runs, {first}(...)"

        return f"Tag it first, {first}(...), or hand over a {first}"

    return f"Hand over a {_spelled_term(term)}"


def _refuse_misfit(
        state: Any,
        name: str,
        value: Any,
        agent: object,
        built: bool = False,
        ) -> None:
    """Admit only the slot's kind, and None only where the kind says so.
    ``built`` words the refusal for what a builder returned rather than
    for a write."""

    slot = None if state is None else state.tools.get(name)

    if slot is None:
        return

    origin, kind = slot
    _refuse_tool_value(origin, kind, name, value, agent, built=built)


def _refuse_tool_value(
        origin: type,
        kind: _Kind,
        name: str,
        value: Any,
        agent: object,
        *,
        built: bool = False,
        ) -> None:
    """Check a proposed value before changing the live Tool binding or kind."""

    where = f"{origin.__name__}.{name}"

    if value is None:
        if kind.empty:
            return

        if built:
            raise TagCompositionError(
                    f"{where} returned None; its slot is never empty: return"
                    f" a value, drop with del agent.{name}, or declare the"
                    f" empty hand, @Tool({kind.Spelled()} | None)"
                    )

        raise TagCompositionError(
                f"{where} is never empty; drop it with"
                f" del {_name_of(agent).lower()}.{name}, or declare the empty"
                f" hand, @Tool({kind.Spelled()} | None)"
                )

    for term in kind.terms:
        if any(
                _admits(alternative, value, where)
                for alternative in term
                ):
            continue

        left = _left(term, value)

        if left is not None:
            raise TagCompositionError(
                    f"{where} holds a Tool of {kind.Spelled()}; this"
                    f" {type(value).__name__} left {left.__name__}"
                    )

        raise TagCompositionError(
                f"{where} holds a Tool of {kind.Spelled()}; {_shown(value)} is"
                f" not a {_spelled_term(term)} now. {_advice(term, built)}"
                )


# ------------------------------------------------------------------
# The gate on the runtime type
# ------------------------------------------------------------------


class _Tool_Gate:
    """A data descriptor for a Tool slot: every write passes admission,
    ``object.__setattr__`` included. Reads and deletions go to the member
    beneath (a Constant or Secret gate) or to the Agent's own binding.

    A slot under a protocol name (``__rmatmul__``) gets no gate, since a
    descriptor there would replace the language's own hook; the write
    hook guards its ordinary writes, and ``object.__setattr__`` on such a
    name is a documented bypass, like writing the instance dictionary."""

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
