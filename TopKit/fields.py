"""Fields: the population of Agents carrying a Tag.

A Field never keeps an Agent alive. Membership is indexed by identity so
registration and removal are constant-time. Iterating a Tag gives the
sound population (every visible Postcondition holds), ``~Tag`` the
defective one, ``Tag[:]`` everyone. ``~`` means broken, and broken twice
is still broken: ``~~Tag`` is ``~Tag``.

Populations combine (STEP-SPEC-13): ``Wizard[:] | Fighter[:]`` is everyone
who is either, ``Wizard - Sworn`` the sound Wizards who have not sworn,
``Wizard & Fighter`` the sound Agents who are both. A Tag in an operator
seat means its sound population. The result is a lazy view: it reads the
Fields when it is walked, never copies them, and keeps application order.
A Pin's population holds Tags and never combines with one of Agents.

A walk takes a Field's members when it begins, and skips a member that an
earlier turn of the same walk Ripped (STEP-SPEC-29, rule 7.1).
"""

from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Iterator
import weakref

from .declarations import _is_pin
from .errors import TagCategoryError


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

    def _home(
            population,
            ) -> type | None:
        """The Tag the population was drawn from (a combination's left
        side's), or None once that Tag is gone."""

        raise NotImplementedError

    def _holds_tags(
            population,
            ) -> bool:
        """A Pin's population holds Tags; every other Tag's holds Agents."""

        home = population._home()

        return (
                home is not None
                and _is_pin(home)
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

    _refuse_tags_with_agents(
            left,
            right,
            operator,
            )

    return _Combined(
            left,
            right,
            operator,
            )


def _refuse_tags_with_agents(
        left: _Population,
        right: _Population,
        operator: str,
        ) -> None:
    """A Pin's population holds Tags, and a Tag's holds Agents: the two
    never combine (STEP-SPEC-28). Python's own type union, ``Wizard |
    None``, never reaches here."""

    left_holds_tags = left._holds_tags()

    if left_holds_tags == right._holds_tags():
        return

    if left_holds_tags:
        pins, agents = left, right
    else:
        pins, agents = right, left

    raise TagCategoryError(
            f"{_name_of_home(left)} {operator} {_name_of_home(right)}:"
            f" {_name_of_home(pins)} is a Pin, and its population holds Tags;"
            f" {_name_of_home(agents)} is a Tag, and its population holds"
            " Agents. The two never combine: combine Pins with Pins, and"
            " Tags with Tags"
            )


def _name_of_home(
        population: _Population,
        ) -> str:
    home = population._home()

    if home is None:
        return "a population"

    return home.__name__


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

    def _home(
            combined,
            ) -> type | None:
        return combined._left._home()

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
        field._tag: weakref.ref | None = None   # its Tag, set when the Tag is made

    def _home(
            field,
            ) -> type | None:
        if field._tag is None:
            return None

        return field._tag()

    def _Add(
            field,
            agent: object,
            ) -> None:
        """The commit step's half of membership (§0.6, step 3): hold the
        Agent weakly in the Field. Private: by itself it skips the gate,
        the Records and the Imprints, and the Agent's own state would
        still say it is no member."""

        key = id(agent)

        if key in field._members:
            return

        try:
            reference = _Member(
                    agent,
                    field._expire,
                    )
        except TypeError as error:
            raise TagCategoryError(
                    "Tagged Agents must support weak references for Fields"
                    ) from error

        reference.key = key
        field._members[key] = reference

    def _Remove(
            field,
            agent: object,
            ) -> None:
        """Rip's and rollback's half of leaving: drop the Agent from the
        Field. Private: by itself it runs no teardown."""

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
        """The members at the start of the walk, in application order. An
        Agent that joins during the walk waits for the next one."""

        held = [
                (reference, agent)
                for reference in list(field._members.values())
                if (agent := reference()) is not None
                ]

        return field._Walk(held)

    def _Walk(
            field,
            held: list[tuple[_Member, object]],
            ) -> Iterator[object]:
        """Each held member at its turn, unless it left the Field since the
        walk began: one an earlier turn Ripped is skipped (STEP-SPEC-29,
        rule 7.1). Its membership is the reference it had at the start, so
        one Ripped and tagged again during the walk is skipped too."""

        members = field._members

        for reference, agent in held:
            if members.get(reference.key) is reference:
                yield agent

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

    def _home(
            partition,
            ) -> type | None:
        return partition._field._home()

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
        """``~`` means broken, and broken twice is still broken: on the
        defective half it gives that half back, so ``~~Wizard`` is
        ``~Wizard`` (STEP-SPEC-29, rule 3.2)."""

        if partition._label == "defective":
            return partition

        holds = partition._holds

        return _Partition(
                partition._field,
                lambda agent: not holds(agent),
                "defective",
                )
