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

A walk takes a Field's join order when it begins. At each saved member's
turn it asks membership again: one Ripped earlier in the walk is skipped,
while one Ripped and tagged again before its turn is visited once.
"""

from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Iterator
import weakref

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
        return _walk_combined(combined)

    def __contains__(
            combined,
            agent: object,
            ) -> bool:
        return _contains_combined(combined, agent)


def _uses_combined_method(population: _Population, name: str) -> bool:
    """Expand the kit's expression nodes, respecting a subclass override."""

    kind = type(population)

    if kind is _Combined:
        return True

    if not issubclass(kind, _Combined):
        return False

    expected = _Combined.__dict__[name]

    # Inspect raw special-method declarations, not their class binding:
    # a descriptor may support only normal instance lookup.
    for ancestor in type.__dict__["__mro__"].__get__(kind):
        namespace = type.__dict__["__dict__"].__get__(ancestor)

        if name in namespace:
            return namespace[name] is expected

    return False


def _contains_combined(combined: _Combined, agent: object) -> bool:
    """Evaluate membership with the same left-first short circuits, without
    borrowing Python's call stack for the expression's depth."""

    pending: list[tuple[_Population | None, str]] = [
            (combined._right, combined._operator),
            ]
    population: _Population = combined._left

    while True:
        while _uses_combined_method(population, "__contains__"):
            pending.append((population._right, population._operator))
            population = population._left

        verdict = agent in population

        while pending:
            right, operator = pending.pop()

            if right is None:   # the right verdict of a difference is negated
                verdict = not verdict
            elif operator == "|" and verdict or operator != "|" and not verdict:
                continue   # the left side already decides this node
            else:
                if operator not in ("|", "&"):
                    pending.append((None, "-"))

                population = right
                break
        else:
            return verdict


class _Walk_Frame:
    """One suspended expression node, including its own union identities.

    The last received Agent matches a recursive generator's loop variable;
    it is released with this frame, not kept by the population at rest.
    """

    __slots__ = ("left", "right", "operator", "on_right", "seen", "agent")

    def __init__(frame, combined: _Combined) -> None:
        frame.left = combined._left
        frame.right = combined._right
        frame.operator = combined._operator
        frame.on_right = False
        frame.seen: dict[int, object] = {}
        frame.agent: object | None = None


def _walk_combined(combined: _Combined) -> Iterator[object]:
    """Walk the expression's branches without flattening them. Each leaf
    starts only when reached; filters and union ownership stay node-local."""

    frames = [_Walk_Frame(combined)]
    population: _Population = frames[0].left

    while True:
        while _uses_combined_method(population, "__iter__"):
            frame = _Walk_Frame(population)
            frames.append(frame)
            population = frame.left

        frame = None   # only the stack owns suspended frames
        iterator = iter(population)

        for agent in iterator:
            for frame in reversed(frames):
                frame.agent = agent

                if frame.operator == "|":
                    if not frame.on_right:
                        frame.seen[id(agent)] = agent
                    elif frame.seen.get(id(agent)) is agent:
                        break
                elif (agent in frame.right) != (frame.operator == "&"):
                    break
            else:
                yield agent

            agent = None   # each suspended node keeps its own loop value
            frame = None

        iterator = None   # finish this leaf before starting another

        while frames:
            frame = frames[-1]

            if frame.operator == "|" and not frame.on_right:
                frame.on_right = True
                population = frame.right
                frame = None
                break

            frames.pop()
            frame = None
        else:
            return


class _Member(weakref.ref):
    """A Field's weak reference to one Agent, carrying its identity key."""

    __slots__ = ("key",)


class _Field(_Population):
    """Whole population of one Tag, weakly held, in application order."""

    _label = "whole"

    def __init__(
            field,
            ) -> None:
        field._members: dict[int, _Member] = {}
        field._expire = field._Forget   # one callback for every member

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
        field._members[key] = reference

    def Remove(
            field,
            agent: object,
            ) -> None:
        field._members.pop(id(agent), None)

    def _Forget(
            field,
            expired: _Member,
            ) -> None:
        if field._members.get(expired.key) is expired:
            del field._members[expired.key]

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
        held = [
                agent
                for reference in list(field._members.values())
                if (agent := reference()) is not None
                ]

        return field._Walk(held)

    def _Walk(
            field,
            held: list[object],
            ) -> Iterator[object]:
        """Walk the saved join order, asking membership at each turn.

        Holding the starting members keeps identity stable for the walk.
        Membership itself stays live: Rip skips a coming turn, and a
        fresh Tagging restores it without adding a second turn.
        """

        members = field._members

        for agent in held:
            reference = members.get(id(agent))

            if reference is not None and reference() is agent:
                yield agent

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
        field = partition._field

        return (
                agent
                for agent in field
                if partition._holds(agent) and agent in field
                )

    def __contains__(
            partition,
            agent: object,
            ) -> bool:
        field = partition._field

        return (
                agent in field
                and partition._holds(agent)
                and agent in field
                )

    def __bool__(
            partition,
            ) -> bool:
        """Anyone? Stops at the first member that counts (``while Enemy:``)."""

        return any(
                True
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
