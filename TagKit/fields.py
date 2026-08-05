from __future__ import annotations

"""Weak, ordered, identity-based Tag Fields."""

from functools import partial
from typing import Iterator
import weakref

from .errors import TagCompositionError


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
