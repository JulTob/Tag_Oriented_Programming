"""Fields: the population of Agents carrying a Tag.

A Field never keeps an Agent alive. Membership is indexed by identity so
registration and removal are constant-time. Iterating a Tag gives the
sound population (every visible Postcondition holds), ``~Tag`` the
defective one, ``Tag[:]`` everyone.

Populations combine (STEP-SPEC-13): ``Wizard[:] | Fighter[:]`` is everyone
who is either, ``Wizard - Sworn`` the sound Wizards who have not sworn,
``Wizard & Fighter`` the sound Agents who are both. A Tag in an operator
seat means its sound population. The result is a lazy view: it reads the
Fields when it is walked, never copies them, and keeps application order.

A Field whose Tag declares an Index (STEP-SPEC-17) also keeps the key of
each member: a map from the whole key to the member, and the keys in
order, so a lookup is one dictionary read and a range is a bisection.
Keys come and go with membership: registered at commit, released at Rip,
at rollback and when the Agent dies.
"""

from __future__ import annotations

from bisect import bisect_left
from bisect import insort
from typing import Any
from typing import Callable
from typing import Iterator
import weakref

from .declarations import _MISSING
from .errors import TagCompositionError


class _Population:
    """What every population answers: walk, ``in``, ``len``, truth, and
    the algebra. ``__iter__`` and ``__contains__`` come from the subclass."""

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
                _population_of(other),
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
                _population_of(other),
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
                _population_of(other),
                population,
                "-",
                )

    def __repr__(
            population,
            ) -> str:
        return f"<{population._label} Field>"


def _population_of(
        candidate: Any,
        ) -> Any:
    """The population a value stands for in an operator seat: a population
    as itself, a Tag as its sound population; anything else NotImplemented."""

    if isinstance(candidate, _Population):
        return candidate

    sound = getattr(
            candidate,
            "_sound",
            None,
            )

    if callable(sound) and isinstance(candidate, type):
        return sound()

    return NotImplemented


def _combine(
        left: Any,
        right: Any,
        operator: str,
        ) -> Any:
    left = _population_of(left)
    right = _population_of(right)

    if left is NotImplemented or right is NotImplemented:
        return NotImplemented

    return _Combined(
            left,
            right,
            operator,
            )


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


class _Field(_Population):
    """Whole population of one Tag, weakly held, in application order.

    When the Tag declares an Index, the Field also holds each member's
    whole key: ``_keys`` maps a key to the member's identity, ``_key_of``
    the other way, and ``_ordered`` keeps the keys sorted. Only the Tag
    that declares the Index registers keys; a Shape's Field holds none and
    reads through its Base's.
    """

    _label = "whole"

    def __init__(
            field,
            ) -> None:
        field._members: dict[int, weakref.ReferenceType[object]] = {}
        field._keys: dict[Any, int] = {}
        field._key_of: dict[int, Any] = {}
        field._ordered: list[Any] = []

    def Add(
            field,
            agent: object,
            key: Any = _MISSING,
            ) -> None:
        member_id = id(agent)

        if member_id in field._members:
            return

        try:
            reference = weakref.ref(
                    agent,
                    lambda expired, member_id=member_id: field._Forget(
                            member_id,
                            expired,
                            ),
                    )
        except TypeError as error:
            raise TagCompositionError(
                    "Tagged Agents must support weak references for Fields"
                    ) from error

        field._members[member_id] = reference

        if key is not _MISSING:
            field._Register(
                    member_id,
                    key,
                    )

    def Remove(
            field,
            agent: object,
            ) -> None:
        member_id = id(agent)
        field._members.pop(member_id, None)
        field._Release(member_id)

    def _Forget(
            field,
            member_id: int,
            expired: weakref.ReferenceType[object],
            ) -> None:
        if field._members.get(member_id) is expired:
            del field._members[member_id]
            field._Release(member_id)

    # -- keys (STEP-SPEC-17) -------------------------------------------

    def _Register(
            field,
            member_id: int,
            key: Any,
            ) -> None:
        """Hold ``key`` for the member. The key was checked before commit:
        hashable, unique, comparable with the keys already present."""

        field._keys[key] = member_id
        field._key_of[member_id] = key
        insort(
                field._ordered,
                key,
                )

    def _Release(
            field,
            member_id: int,
            ) -> None:
        key = field._key_of.pop(
                member_id,
                _MISSING,
                )

        if key is _MISSING:
            return

        field._keys.pop(key, None)
        position = bisect_left(
                field._ordered,
                key,
                )

        if (
                position < len(field._ordered)
                and field._ordered[position] == key
                ):
            del field._ordered[position]

    def Keys(
            field,
            ) -> list[Any]:
        """The whole keys present, in order. Read, never written."""

        return field._ordered

    def Key_Of(
            field,
            agent: object,
            ) -> Any:
        """The member's whole key, or ``_MISSING`` when it has none."""

        if agent not in field:
            return _MISSING

        return field._key_of.get(
                id(agent),
                _MISSING,
                )

    def Holder(
            field,
            key: Any,
            ) -> object | None:
        """The live member at ``key``, or None. A member that died before
        its weak reference reported it is released on the way."""

        member_id = field._keys.get(key)

        if member_id is None:
            return None

        reference = field._members.get(member_id)
        agent = reference() if reference is not None else None

        if agent is None:
            field._members.pop(member_id, None)
            field._Release(member_id)

        return agent

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
                for agent in (
                    reference()
                    for reference in list(field._members.values())
                    )
                if agent is not None
                ]

        return iter(live)

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

    def __invert__(
            partition,
            ) -> "_Partition":
        holds = partition._holds

        return _Partition(
                partition._field,
                lambda agent: not holds(agent),
                "defective" if partition._label == "sound" else "sound",
                )
