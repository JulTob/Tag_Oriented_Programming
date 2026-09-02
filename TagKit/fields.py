from __future__ import annotations

"""Weak, ordered, identity-based Tag Fields."""

from functools import partial
from typing import Iterator
import weakref

from .errors import TagCompositionError


def _agent_posts_hold(
        agent: object,
        ) -> bool:
    from .contracts import _check_conditions
    from .errors import TagPostconditionError

    return _check_conditions(
            agent,
            "postconditions",
            TagPostconditionError,
            "Postcondition",
            False,
            )


def _same_registry(
        left: object,
        right: object,
        ) -> bool:
    return (
            getattr(
                    left,
                    "_field",
                    left,
                    )
            is getattr(
                    right,
                    "_field",
                    right,
                    )
            )


class _Field:
    """A non-owning population of Agents for one Tag."""

    def __init__(
            field,
            ) -> None:
        field._references: dict[
                int,
                weakref.ReferenceType[object],
                ] = {}

    def _add(
            field,
            agent: object,
            ) -> None:
        identity = id(agent)
        current = field._references.get(identity)

        if (
                current is not None
                and current() is agent
                ):
            return

        if current is not None:
            field._references.pop(
                    identity,
                    None,
                    )

        try:
            reference = weakref.ref(
                    agent,
                    partial(
                            field._Forget,
                            identity,
                            ),
                    )
        except TypeError as error:
            raise TagCompositionError(
                    "Tagged Agents must support weak references for Fields"
                    ) from error

        field._references[identity] = reference

    def _remove(
            field,
            agent: object,
            ) -> None:
        field._references.pop(
                id(agent),
                None,
                )

    def __contains__(
            field,
            agent: object,
            ) -> bool:
        reference = field._references.get(
                id(agent)
                )

        return (
                reference is not None
                and reference() is agent
                )

    def _Forget(
            field,
            identity: int,
            expired: weakref.ReferenceType[object],
            ) -> None:
        if field._references.get(identity) is expired:
            field._references.pop(
                    identity,
                    None,
                    )

    def __iter__(
            field,
            ) -> Iterator[object]:
        for identity, reference in tuple(
                field._references.items()
                ):
            if field._references.get(identity) is not reference:
                continue

            agent = reference()

            if agent is None:
                if field._references.get(identity) is reference:
                    field._references.pop(
                            identity,
                            None,
                        )
                continue

            yield agent

    def __len__(
            field,
            ) -> int:
        return sum(
                1
                for _agent in field
                )

    def __invert__(
            field,
            ) -> "_Empty_Field":
        # The Field is the universe for this Tag; its complement is empty.
        return _Empty_Field(field)

    def __sub__(
            field,
            other: object,
            ) -> object:
        if isinstance(
                other,
                _Valid_Field,
                ) and other._field is field:
            return _Defective_Field(field)

        if isinstance(
                other,
                _Defective_Field,
                ) and other._field is field:
            return _Valid_Field(field)

        if other is field or (
                isinstance(
                        other,
                        _Field,
                        )
                and other is field
                ):
            return _Empty_Field(field)

        return NotImplemented

    def __or__(
            field,
            other: object,
            ) -> "_Field":
        if (
                isinstance(
                        other,
                        (
                            _Valid_Field,
                            _Defective_Field,
                            _Empty_Field,
                            _Field,
                            ),
                        )
                and _same_registry(
                        field,
                        other,
                        )
                ):
            return field

        return NotImplemented

    def __ror__(
            field,
            other: object,
            ) -> "_Field":
        return field.__or__(other)


class _Empty_Field:
    """The empty complement of a Tag Field universe."""

    def __init__(
            view,
            field: _Field,
            ) -> None:
        view._field = field

    def __contains__(
            view,
            agent: object,
            ) -> bool:
        return False

    def __iter__(
            view,
            ) -> Iterator[object]:
        return iter(())

    def __len__(
            view,
            ) -> int:
        return 0

    def __invert__(
            view,
            ) -> _Field:
        return view._field

    def __or__(
            view,
            other: object,
            ) -> object:
        if _same_registry(
                view,
                other,
                ):
            return other

        return NotImplemented

    def __ror__(
            view,
            other: object,
            ) -> object:
        return view.__or__(other)


class _Valid_Field:
    """Field members whose visible Postconditions currently hold."""

    def __init__(
            view,
            field: _Field,
            ) -> None:
        view._field = field

    def __contains__(
            view,
            agent: object,
            ) -> bool:
        return (
                agent in view._field
                and _agent_posts_hold(agent)
                )

    def __iter__(
            view,
            ) -> Iterator[object]:
        for agent in view._field:
            if _agent_posts_hold(agent):
                yield agent

    def __len__(
            view,
            ) -> int:
        return sum(
                1
                for _agent in view
                )

    def __invert__(
            view,
            ) -> "_Defective_Field":
        return _Defective_Field(view._field)

    def __or__(
            view,
            other: object,
            ) -> object:
        if isinstance(
                other,
                _Defective_Field,
                ) and other._field is view._field:
            return view._field

        if isinstance(
                other,
                _Valid_Field,
                ) and other._field is view._field:
            return view

        if isinstance(
                other,
                _Empty_Field,
                ) and other._field is view._field:
            return view

        if other is view._field:
            return view._field

        return NotImplemented

    def __ror__(
            view,
            other: object,
            ) -> object:
        return view.__or__(other)

    def __sub__(
            view,
            other: object,
            ) -> object:
        if isinstance(
                other,
                _Defective_Field,
                ) and other._field is view._field:
            return view

        if isinstance(
                other,
                _Valid_Field,
                ) and other._field is view._field:
            return _Empty_Field(view._field)

        if other is view._field:
            return _Empty_Field(view._field)

        return NotImplemented


class _Defective_Field:
    """Field members whose visible Postconditions currently fail."""

    def __init__(
            view,
            field: _Field,
            ) -> None:
        view._field = field

    def __contains__(
            view,
            agent: object,
            ) -> bool:
        return (
                agent in view._field
                and not _agent_posts_hold(agent)
                )

    def __iter__(
            view,
            ) -> Iterator[object]:
        for agent in view._field:
            if not _agent_posts_hold(agent):
                yield agent

    def __len__(
            view,
            ) -> int:
        return sum(
                1
                for _agent in view
                )

    def __invert__(
            view,
            ) -> _Valid_Field:
        return _Valid_Field(view._field)

    def __or__(
            view,
            other: object,
            ) -> object:
        if isinstance(
                other,
                _Valid_Field,
                ) and other._field is view._field:
            return view._field

        if isinstance(
                other,
                _Defective_Field,
                ) and other._field is view._field:
            return view

        if isinstance(
                other,
                _Empty_Field,
                ) and other._field is view._field:
            return view

        if other is view._field:
            return view._field

        return NotImplemented

    def __ror__(
            view,
            other: object,
            ) -> object:
        return view.__or__(other)

    def __sub__(
            view,
            other: object,
            ) -> object:
        if isinstance(
                other,
                _Valid_Field,
                ) and other._field is view._field:
            return view

        if isinstance(
                other,
                _Defective_Field,
                ) and other._field is view._field:
            return _Empty_Field(view._field)

        if other is view._field:
            return _Empty_Field(view._field)

        return NotImplemented
