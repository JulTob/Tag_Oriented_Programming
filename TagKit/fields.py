"""Fields: the population of Agents carrying a Tag.

A Field never keeps an Agent alive. Membership is indexed by identity so
registration and removal are constant-time. Iterating a Tag gives the
sound population (every visible Postcondition holds), ``~Tag`` the
defective one, ``Tag[:]`` everyone.
"""

from __future__ import annotations

from typing import Callable
from typing import Iterator
import weakref

from .errors import TagCompositionError


class _Field:
    """Whole population of one Tag, weakly held, in application order."""

    def __init__(
            field,
            ) -> None:
        field._members: dict[int, weakref.ReferenceType[object]] = {}

    def Add(
            field,
            agent: object,
            ) -> None:
        key = id(agent)

        if key in field._members:
            return

        try:
            reference = weakref.ref(
                    agent,
                    lambda expired, key=key: field._Forget(key, expired),
                    )
        except TypeError as error:
            raise TagCompositionError(
                    "Tagged Agents must support weak references for Fields"
                    ) from error

        field._members[key] = reference

    def Remove(
            field,
            agent: object,
            ) -> None:
        field._members.pop(id(agent), None)

    def _Forget(
            field,
            key: int,
            expired: weakref.ReferenceType[object],
            ) -> None:
        if field._members.get(key) is expired:
            del field._members[key]

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


class _Partition:
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

    def __len__(
            partition,
            ) -> int:
        return sum(
                1
                for _ in partition
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

    def __repr__(
            partition,
            ) -> str:
        return f"<{partition._label} Field>"
