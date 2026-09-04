"""Geometry: how Tags relate. A Base forms into a Shape.

The Form of a Tag is its ordered, duplicate-free, Base-first closure,
ending with the Tag itself. Applying a Tag follows its Form.
"""

from __future__ import annotations

from typing import Iterable
from weakref import WeakKeyDictionary


_tag_types: tuple[type, type] | None = None
_form_cache: "WeakKeyDictionary[type, tuple[type, ...]]" = WeakKeyDictionary()


def _is_tag(
        candidate: object,
        ) -> bool:
    global _tag_types

    if _tag_types is None:
        from .tags import MetaTag
        from .tags import Tag

        _tag_types = (MetaTag, Tag)

    meta, root = _tag_types

    return (
            isinstance(candidate, meta)
            and candidate is not root
            )


def _direct_bases(
        tag: type,
        ) -> tuple[type, ...]:
    """The Bases a Tag declares directly, in declaration order."""

    return tuple(
            base
            for base in tag.__bases__
            if _is_tag(base)
            )


def _form_of(
        tag: type,
        ) -> tuple[type, ...]:
    """Base-first closure of one Tag: every required Base once, then the Tag."""

    cached = _form_cache.get(tag)

    if cached is not None:
        return cached

    form: list[type] = []

    def Visit(
            candidate: type,
            ) -> None:
        for base in _direct_bases(candidate):
            Visit(base)

        if candidate not in form:
            form.append(candidate)

    Visit(tag)

    result = tuple(form)
    _form_cache[tag] = result

    return result


def _leaves(
        active: Iterable[type],
        ) -> tuple[type, ...]:
    """Active Tags that no other active Tag specializes."""

    active = tuple(active)

    return tuple(
            candidate
            for candidate in active
            if not any(
                    other is not candidate
                    and issubclass(other, candidate)
                    for other in active
                    )
            )


def _requiring_shapes(
        tag: type,
        active: Iterable[type],
        ) -> tuple[type, ...]:
    """Active Shapes that still require ``tag`` as a Base."""

    return tuple(
            other
            for other in active
            if (
                other is not tag
                and issubclass(other, tag)
                )
            )


def _related(
        one: type,
        other: type,
        ) -> bool:
    """True when one Tag is a Base or Shape of the other."""

    return (
            issubclass(one, other)
            or issubclass(other, one)
            )
