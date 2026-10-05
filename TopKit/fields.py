"""Fields: the population of Agents carrying a Tag.

A Field never keeps an Agent alive. Membership is indexed by identity so
registration and removal are constant-time. Iterating a Tag gives the
sound population (every visible Postcondition holds), ``~Tag`` the
defective one, ``Tag[:]`` everyone. ``agent in Tag`` answers the same
population as the loop (STEP-SPEC-19); ``agent in Tag[:]`` is membership.

Populations combine (STEP-SPEC-13): ``Wizard[:] | Fighter[:]`` is everyone
who is either, ``Wizard - Sworn`` the sound Wizards who have not sworn,
``Wizard & Fighter`` the sound Agents who are both. A Tag in an operator
seat means its sound population. The result is a lazy view: it reads the
Fields when it is walked, never copies them, and keeps application order.

A Pin's population holds Tags and a Tag's holds objects; the two never
combine, and the refusal names both sides. A population is not a type:
``isinstance(x, Wizard | Fighter)`` and ``Wizard | Fighter | None`` are
refused, and the refusal names the rewrite.
"""

from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Iterator
import types
import typing
import weakref

from .declarations import _is_pin
from .errors import TagCompositionError

_MetaTag: type | None = None   # imported on first use: tags imports this module


def _is_tag_type(
        candidate: object,
        ) -> bool:
    """A Tag is one by its metaclass, never by an attribute it happens to
    carry: a class with its own ``_sound`` is a plain class."""

    global _MetaTag

    if _MetaTag is None:
        from .tags import MetaTag as _MetaTag

    return isinstance(candidate, _MetaTag)


class _Population:
    """What every population answers: walk, ``in``, ``len``, truth, and
    the algebra. ``__iter__`` and ``__contains__`` come from the subclass,
    as do ``_tags`` (the Tags it is made of, each once), ``_spell`` (how
    a program writes it) and ``_kind`` ("Tags" for a Pin's, "objects" for
    an ordinary Tag's, None where the Tag is gone). ``_names`` spells the
    Tags by ``__name__``, or by ``__qualname__`` where two share one.
    ``_either`` says whether the population is its Tags' members joined
    only by ``|``, the one shape a tuple of Tags can stand for."""

    _label: str = "population"

    def __iter__(
            population,
            ) -> Iterator[object]:
        raise NotImplementedError

    def __contains__(
            population,
            agent: object,
            ) -> bool:
        raise NotImplementedError

    def _tags(
            population,
            ) -> list[Any]:
        raise NotImplementedError

    def _names(
            population,
            ) -> list[str]:
        return _spell_tags(population._tags())

    def _spell(
            population,
            ) -> str:
        raise NotImplementedError

    def _kind(
            population,
            ) -> str | None:
        raise NotImplementedError

    def _either(
            population,
            ) -> bool:
        raise NotImplementedError

    def __instancecheck__(
            population,
            candidate: object,
            ) -> bool:
        """``isinstance(x, Wizard | Fighter)``: a population is not a type."""

        raise TypeError(
                f"isinstance(x, {population._spell()}): a population is not"
                f" a type; {_class_rewrite('isinstance', population)}"
                )

    def __subclasscheck__(
            population,
            candidate: object,
            ) -> bool:
        raise TypeError(
                f"issubclass(x, {population._spell()}): a population is not"
                f" a type; {_class_rewrite('issubclass', population)}"
                )

    def __len__(
            population,
            ) -> int:
        return sum(
                1
                for _ in population
                )

    def __bool__(
            population,
            ) -> bool:
        return any(
                True
                for _ in population
                )

    def __or__(
            population,
            other: Any,
            ) -> Any:
        return _combine(
                population,
                other,
                "|",
                )

    def __ror__(
            population,
            other: Any,
            ) -> Any:
        return _combine(
                other,
                population,
                "|",
                )

    def __and__(
            population,
            other: Any,
            ) -> Any:
        return _combine(
                population,
                other,
                "&",
                )

    def __rand__(
            population,
            other: Any,
            ) -> Any:
        return _combine(
                other,
                population,
                "&",
                )

    def __sub__(
            population,
            other: Any,
            ) -> Any:
        return _combine(
                population,
                other,
                "-",
                )

    def __rsub__(
            population,
            other: Any,
            ) -> Any:
        return _combine(
                other,
                population,
                "-",
                )

    def __repr__(
            population,
            ) -> str:
        return f"<{population._label} Field>"


def _spell_tags(
        tags: list[Any],
        ) -> list[str]:
    """Each Tag by ``__name__``; by ``__qualname__`` where two Tags share
    a name; a Tag that is gone by a placeholder. Two Tags can still read
    alike (a Twin made with ``type("T2", (T2,), {})`` shares both names),
    so a refusal names a rewrite only when every Tag reads apart
    (``_rewrite_names``); even then a renamed Tag, or a Twin made under
    another Tag's name, may not answer to that name in the program's own
    namespace."""

    names = [
            "<a Tag that is gone>" if tag is None else tag.__name__
            for tag in tags
            ]

    return [
            tag.__qualname__
            if tag is not None and names.count(name) > 1
            else name
            for tag, name in zip(tags, names)
            ]


def _rewrite_names(
        population: _Population,
        ) -> list[str] | None:
    """The Tags a rewrite names, or None when no list of Tags says what
    the population means: an operator other than ``|``, a defective view
    (``~``), a Tag that is gone, or two Tags that read alike."""

    if not population._either():
        return None

    tags = population._tags()

    if any(tag is None for tag in tags):
        return None

    names = _spell_tags(tags)

    if len(set(names)) < len(names):
        return None

    return names


def _class_rewrite(
        check: str,
        population: _Population,
        ) -> str:
    """The end of an ``isinstance`` or ``issubclass`` refusal: the call
    that means "a member of any of these Tags", when there is one."""

    names = _rewrite_names(population)

    if names is None:
        return f"{check} takes Tags"

    if len(names) == 1:
        return f"write {check}(x, {names[0]})"

    return f"write {check}(x, ({', '.join(names)}))"


def _population_of(
        candidate: Any,
        ) -> Any:
    """The population a value stands for in an operator seat: a population
    as itself, a Tag (by its metaclass) as its sound population; anything
    else NotImplemented."""

    if isinstance(candidate, _Population):
        return candidate

    if _is_tag_type(candidate):
        from .tags import _sound_of   # tags imports this module

        return _sound_of(candidate)

    return NotImplemented


def _is_type_material(
        value: Any,
        ) -> bool:
    """What ``|`` joins into a type hint: ``None``, a class, a union, a
    generic alias (``list[int]``) or a ``typing`` form (``typing.Any``,
    ``typing.List[int]``)."""

    return (
            value is None
            or isinstance(value, (type, types.UnionType, types.GenericAlias))
            or type(value).__module__ in ("typing", "annotationlib")   # ForwardRef lives in annotationlib from 3.14
            )


def _hint_rewrite(
        population: _Population,
        other: Any,
        ) -> str:
    """The end of a hint's refusal: the ``typing`` spelling of what a hint
    over the population meant, when a list of Tags says it."""

    names = _rewrite_names(population)

    if names is None:
        return "a hint takes Tags"

    if other is not None:
        return f"write typing.Union[{', '.join(names)}, {_spell_operand(other, inside_union=True)}]"

    if len(names) == 1:
        return f"write typing.Optional[{names[0]}]"

    return f"write typing.Optional[typing.Union[{', '.join(names)}]]"


def _combine(
        left: Any,
        right: Any,
        operator: str,
        ) -> Any:
    """Two operands under one operator: a Combined population, or a refusal.

    ``|`` with ``None`` or a class in either seat is a type hint over a
    population, which is not a type: refused, naming the rewrite. A
    Pin's population (Tags) with a Tag's (objects) is refused, naming
    both sides. Anything else that is not a population is NotImplemented,
    and Python raises its own TypeError.
    """

    left_population = _population_of(left)
    right_population = _population_of(right)

    if left_population is NotImplemented or right_population is NotImplemented:
        if operator == "|":
            population, other = (
                    (right_population, left)
                    if left_population is NotImplemented
                    else (left_population, right)
                    )

            if isinstance(population, _Population) and _is_type_material(other):
                spelled = (
                        f"{_spell_operand(left)} | {population._spell()}"
                        if population is right_population
                        else f"{population._spell()} | {_spell_operand(right)}"
                        )

                raise TypeError(
                        f"{spelled}: a population is not a type;"
                        f" {_hint_rewrite(population, other)}"
                        )

        return NotImplemented

    left_kind = left_population._kind()
    right_kind = right_population._kind()

    if left_kind is not None and right_kind is not None and left_kind != right_kind:
        raise TypeError(
                f"{left_population._spell()} {operator} {right_population._spell()}:"
                f" {left_population._spell()} holds {left_kind} and"
                f" {right_population._spell()} holds {right_kind};"
                " a Pin's population and a Tag's do not combine"
                )

    return _Combined(
            left_population,
            right_population,
            operator,
            )


def _spell_operand(
        value: Any,
        inside_union: bool = False,
        ) -> str:
    """The other side of a hint as a program writes it: by its name, or
    as it spells itself; a ``ForwardRef`` as ``typing.ForwardRef('X')``,
    or as the string ``'X'`` inside ``typing.Union[...]``."""

    if value is None or value is type(None):
        return "None"

    if isinstance(value, type):
        if value.__module__ == "typing":
            return f"typing.{value.__qualname__}"

        return value.__name__

    if isinstance(value, (typing.TypeVar, typing.ParamSpec, typing.TypeVarTuple, typing.NewType)):
        return value.__name__   # their repr, ~T or __main__.N, is not code

    if isinstance(value, typing.ForwardRef):
        if inside_union:
            return repr(value.__forward_arg__)   # typing.Union takes the name as a string

        return f"typing.ForwardRef({value.__forward_arg__!r})"

    return repr(value)   # a union or an alias spells itself: int | str, list[int]


class _Combined(_Population):
    """Two populations under one operator, read lazily.

    ``|`` walks the left population then the right, each Agent once;
    ``&`` walks the left and keeps those also in the right; ``-`` walks
    the left and drops those in the right. Application order is kept
    within each side.
    """

    def __init__(
            combined,
            left: _Population,
            right: _Population,
            operator: str,
            ) -> None:
        combined._left = left
        combined._right = right
        combined._operator = operator
        combined._label = f"{left._label} {operator} {right._label}"

    def __iter__(
            combined,
            ) -> Iterator[object]:
        left = combined._left
        right = combined._right

        if combined._operator == "|":
            seen: set[int] = set()

            for agent in left:
                seen.add(id(agent))
                yield agent

            for agent in right:
                if id(agent) not in seen:
                    yield agent

            return

        if combined._operator == "&":
            for agent in left:
                if agent in right:
                    yield agent

            return

        for agent in left:
            if agent not in right:
                yield agent

    def __contains__(
            combined,
            agent: object,
            ) -> bool:
        left = combined._left
        right = combined._right

        if combined._operator == "|":
            return agent in left or agent in right

        if combined._operator == "&":
            return agent in left and agent in right

        return agent in left and agent not in right

    def _tags(
            combined,
            ) -> list[Any]:
        tags = combined._left._tags()
        seen = {id(tag) for tag in tags}

        return tags + [
                tag
                for tag in combined._right._tags()
                if id(tag) not in seen   # by identity: two Tags may share a name
                ]

    def _spell(
            combined,
            ) -> str:
        return (
                f"({combined._left._spell()} {combined._operator}"
                f" {combined._right._spell()})"
                )

    def _kind(
            combined,
            ) -> str | None:
        return combined._left._kind() or combined._right._kind()

    def _either(
            combined,
            ) -> bool:
        return (
                combined._operator == "|"
                and combined._left._either()
                and combined._right._either()
                )


class _Member(weakref.ref):
    """A Field's weak reference to one Agent, carrying its identity key
    and its place in the Field's order."""

    __slots__ = (
            "key",
            "order",
            )


class _Field(_Population):
    """Whole population of one Tag, weakly held, in application order.

    ``_owner`` is a weak reference to the Tag, set when the Tag's class
    is made: the Tag holds its Field, never the other way round. It
    gives a refusal the Tag's name, and says whether the Field holds
    Tags (a Pin's) or objects, read when asked, because ``@Pin`` marks a
    Tag after its class exists.
    """

    _label = "whole"
    _owner: Callable[[], Any] | None = None

    def __init__(
            field,
            ) -> None:
        field._members: dict[int, _Member] = {}
        field._expire = field._Forget   # one callback for every member
        field._joined = 0               # members so far: each one's place in the order

    def Add(
            field,
            agent: object,
            ) -> None:
        key = id(agent)

        if key in field._members:
            return

        try:
            reference = _Member(
                    agent,
                    field._expire,
                    )
        except TypeError as error:
            raise TagCompositionError(
                    "Tagged Agents must support weak references for Fields"
                    ) from error

        reference.key = key
        reference.order = field._joined
        field._joined += 1
        field._members[key] = reference

    def Remove(
            field,
            agent: object,
            ) -> None:
        field._members.pop(id(agent), None)

    def Rejoin(
            field,
            agent: object,
            member: _Member | None,
            ) -> None:
        """Put the Agent back as ``member`` had it, in its place in the
        order: a rolled-back Rip or deletion gives the Field back as it
        was. Where Python already cleared ``member`` (a collected cycle),
        or there was none, the Agent joins at the end."""

        members = field._members
        key = id(agent)

        if member is None or member() is not agent:
            if members.get(key) is None:
                field.Add(agent)

            return

        if members.get(key) is member:
            return

        members.pop(key, None)
        later = [
                (other, reference)
                for other, reference in members.items()
                if reference.order > member.order
                ]

        for other, _reference in later:
            del members[other]

        members[key] = member
        members.update(later)

    def _Forget(
            field,
            expired: _Member,
            ) -> None:
        if field._members.get(expired.key) is expired:
            del field._members[expired.key]

    def _tag(
            field,
            ) -> Any:
        owner = field._owner

        return None if owner is None else owner()

    def _tags(
            field,
            ) -> list[Any]:
        return [field._tag()]

    def _spell(
            field,
            ) -> str:
        return field._names()[0] + "[:]"

    def _kind(
            field,
            ) -> str | None:
        tag = field._tag()

        if tag is None:
            return None

        return "Tags" if _is_pin(tag) else "objects"

    def _either(
            field,
            ) -> bool:
        return True

    def __contains__(
            field,
            agent: object,
            ) -> bool:
        reference = field._members.get(id(agent))

        return (
                reference is not None
                and reference() is agent
                )

    def __iter__(
            field,
            ) -> Iterator[object]:
        live = [
                agent
                for reference in list(field._members.values())
                if (agent := reference()) is not None
                ]

        return iter(live)

    def _held(
            field,
            ) -> list[object | None]:
        """Every member, held for as long as the list lives; None where
        one has died. A question that stops early skips the filtering a
        walk pays for."""

        return [
                reference()
                for reference in list(field._members.values())
                ]

    def __len__(
            field,
            ) -> int:
        return sum(
                1
                for reference in list(field._members.values())
                if reference() is not None
                )

    def __bool__(
            field,
            ) -> bool:
        return any(
                reference() is not None
                for reference in list(field._members.values())
                )


class _Partition(_Population):
    """One half of a Field: the Agents for which ``holds`` is True."""

    def __init__(
            partition,
            field: _Field,
            holds: Callable[[object], bool],
            label: str,
            ) -> None:
        partition._field = field
        partition._holds = holds
        partition._label = label

    def __iter__(
            partition,
            ) -> Iterator[object]:
        return (
                agent
                for agent in partition._field
                if partition._holds(agent)
                )

    def __contains__(
            partition,
            agent: object,
            ) -> bool:
        return (
                agent in partition._field
                and partition._holds(agent)
                )

    def __bool__(
            partition,
            ) -> bool:
        """Anyone? Stops at the first member that counts (``while Enemy:``)."""

        holds = partition._holds

        for agent in partition._field._held():   # every member held while the checks run
            if agent is not None and holds(agent):
                return True

        return False

    def __invert__(
            partition,
            ) -> "_Partition":
        holds = partition._holds

        return _Partition(
                partition._field,
                lambda agent: not holds(agent),
                "defective" if partition._label == "sound" else "sound",
                )

    def _tags(
            partition,
            ) -> list[Any]:
        return partition._field._tags()

    def _spell(
            partition,
            ) -> str:
        name = partition._names()[0]

        return name if partition._label == "sound" else "~" + name

    def _kind(
            partition,
            ) -> str | None:
        return partition._field._kind()

    def _either(
            partition,
            ) -> bool:
        return partition._label == "sound"
