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

A walk takes a Field's join order when it begins. At each saved member's
turn it asks membership again: one Ripped earlier in the walk is skipped,
while one Ripped and tagged again before its turn is visited once.
"""

from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Iterator
import weakref

from .contracts import _holds_for_population
from .errors import TagCompositionError
from .geometry import _is_tag_class
from .memo import _class_namespace


FIELD_SEAT = "_topkit_field"   # the kit's own seat on every Tag class; MetaTag.__new__ fills it
# A fresh identity marks each physical Field change. Compound queries can
# then avoid rescanning a growing set of witnesses when no Field has changed.
_field_change_token = object()


def _field_of(
        tag: type,
        ) -> "_Field":
    """The Tag's own Field, read from its class dictionary: never through
    attribute lookup, which the programmer's namespace could shadow."""

    return _class_namespace(tag)[FIELD_SEAT]


def _sound_of(
        tag: type,
        ) -> "_Partition":
    """The Tag's sound population."""

    return _Partition(
            _field_of(tag),
            _holds_for_population,
            "sound",
            )


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

    if _is_tag_class(candidate):
        return _sound_of(candidate)

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
        combined._pure_fields = (
                _pure_fields(left)
                and _pure_fields(right)
                )

    def __iter__(
            combined,
            ) -> Iterator[object]:
        return _walk_combined(combined)

    def __contains__(
            combined,
            agent: object,
            ) -> bool:
        return _contains_combined(combined, agent)


def _pure_fields(population: _Population) -> bool:
    """This branch can only read raw Fields; evaluating it runs no Posts."""

    return (
            type(population) is _Field
            or type(population) is _Combined and population._pure_fields
            )


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

    if combined._pure_fields:
        return _contains_pure_fields(combined, agent)

    verdict, _ = _probe_combined(combined, agent)
    return verdict


def _contains_pure_fields(combined: _Combined, agent: object) -> bool:
    """The original short-circuit path for branches with no user calls."""

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

            if right is None:
                verdict = not verdict
            elif operator == "|" and verdict or operator != "|" and not verdict:
                continue
            else:
                if operator not in ("|", "&"):
                    pending.append((None, "-"))

                population = right
                break
        else:
            return verdict


def _positive_field(population: _Population) -> "_Field | None":
    """A Field that can prove a positive leaf verdict without another Post."""

    if type(population) is _Field:
        return population
    if type(population) is _Partition:
        return population._field
    return None


class _Evidence:
    """Selected positive Fields, with the last membership observation.

    A Post may change any Field while a later operand is evaluated. Recheck
    only after such a change; an ordinary deep intersection then costs one
    Field lookup per leaf instead of rescanning every earlier witness at
    every parent node.
    """

    __slots__ = ("fields", "token")

    def __init__(evidence, field: "_Field | None" = None) -> None:
        evidence.fields = {field} if field is not None else set()
        evidence.token = _field_change_token

    def _Merge(evidence, other: "_Evidence") -> "_Evidence":
        # Combine into the larger set, so a right-nested expression does not
        # repeatedly copy all of the witnesses already collected there.
        if len(evidence.fields) < len(other.fields):
            evidence, other = other, evidence

        evidence.fields.update(other.fields)

        if evidence.token is not other.token:
            evidence.token = None

        return evidence

    def _Holds(evidence, agent: object) -> bool:
        if evidence.token is _field_change_token:
            return True

        if not all(agent in field for field in evidence.fields):
            return False

        evidence.token = _field_change_token
        return True


def _probe_combined(
        combined: _Combined,
        agent: object,
        ) -> tuple[bool, _Evidence]:
    """Judge a compound query once, retaining the selected Field evidence.

    Each node checks its selected positive Fields before returning to its
    parent if any physical Field changed since the last check. No Post is
    run merely to recheck a Field.
    """

    # Each frame holds a node, its left/right stage and left's evidence.
    pending: list[tuple[_Combined, int, _Evidence | None]] = [
            (combined, 0, None),
            ]
    population: _Population = combined._left

    while True:
        while _uses_combined_method(population, "__contains__"):
            pending.append((population, 0, None))
            population = population._left

        verdict = agent in population
        field = _positive_field(population) if verdict else None
        evidence = _Evidence(field)

        while pending:
            node, stage, left_evidence = pending[-1]
            operator = node._operator

            if stage == 0:
                # The left side has just returned. A valid union left wins;
                # a false intersection/difference left decides its node.
                if verdict:
                    verdict = evidence._Holds(agent)

                if operator == "|" and verdict:
                    pending.pop()
                    continue
                elif operator != "|" and not verdict:
                    evidence = _Evidence()
                    pending.pop()
                    continue

                pending[-1] = (node, 1, evidence)
                population = node._right
                break

            pending.pop()
            if left_evidence is None:
                raise RuntimeError("a compound population lost its left evidence")

            if operator == "&":
                if verdict:
                    evidence = left_evidence._Merge(evidence)
                    verdict = evidence._Holds(agent)
                else:
                    evidence = _Evidence()
            elif operator == "-":
                if verdict:
                    verdict = evidence._Holds(agent)
                verdict = not verdict
                evidence = left_evidence if verdict else _Evidence()
                if verdict:
                    verdict = evidence._Holds(agent)
            elif verdict:
                verdict = evidence._Holds(agent)

            if not verdict:
                evidence = _Evidence()
        else:
            return verdict, evidence


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
    pure_fields = combined._pure_fields

    try:
        while True:
            while _uses_combined_method(population, "__iter__"):
                frame = _Walk_Frame(population)
                frames.append(frame)
                population = frame.left

            frame = None   # only the stack owns suspended frames
            iterator = iter(population)

            for agent in iterator:
                if pure_fields:
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

                    agent = None
                    frame = None
                    continue

                field = _positive_field(population)
                evidence = _Evidence(field)

                for frame in reversed(frames):
                    frame.agent = agent

                    if frame.operator == "|":
                        if not frame.on_right:
                            if not evidence._Holds(agent):
                                break
                            frame.seen[id(agent)] = agent
                        elif frame.seen.get(id(agent)) is agent:
                            break
                    elif frame.operator == "&":
                        if _uses_combined_method(frame.right, "__contains__"):
                            present, right_evidence = _probe_combined(frame.right, agent)
                        else:
                            present = agent in frame.right
                            right_field = _positive_field(frame.right) if present else None
                            right_evidence = _Evidence(right_field)
                        if not present:
                            break
                        evidence = evidence._Merge(right_evidence)
                    else:
                        if agent in frame.right:
                            break

                    if not evidence._Holds(agent):
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
    finally:
        # A closed or failed generator can still have a retained Python
        # frame. End the walk's ownership without relying on frame disposal.
        frames.clear()
        frame = iterator = agent = None


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

    def _Add(
            field,
            agent: object,
            ) -> None:
        """The Field-entry half of membership: hold the Agent weakly
        in the Field. Private: by itself it would skip the Gate, Records
        and Imprints while leaving the Agent's state unchanged."""

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
        global _field_change_token
        _field_change_token = object()

    def _Remove(
            field,
            agent: object,
            ) -> None:
        """Rip's and rollback's half of leaving. Private: by itself it
        would skip the Agent's state change and every teardown."""

        if field._members.pop(id(agent), None) is not None:
            global _field_change_token
            _field_change_token = object()

    def _Forget(
            field,
            expired: _Member,
            ) -> None:
        if field._members.get(expired.key) is expired:
            del field._members[expired.key]
            global _field_change_token
            _field_change_token = object()

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
        """Anyone? Stops at the first member that counts (``while ~Enemy:``)."""

        return any(
                True
                for _ in partition
                )

    def __invert__(
            partition,
            ) -> "_Partition":
        """``~`` means broken, and broken twice is still broken: on the
        defective half it gives that half back, so ``~~Wizard`` is
        ``~Wizard`` (STEP-SPEC-38)."""

        if partition._label == "defective":
            return partition

        holds = partition._holds

        return _Partition(
                partition._field,
                lambda agent: not holds(agent),
                "defective",
                )
