"""Geometry: how Tags relate. A Base forms into a Shape.

The Form of a Tag is its ordered, duplicate-free, Base-first closure,
ending with the Tag itself. Applying a Tag follows its Form.
"""

from __future__ import annotations

from typing import Iterable
from weakref import WeakKeyDictionary


_tag_types: tuple[type, type] | None = None
_bases_cache: "WeakKeyDictionary[type, tuple[type, ...]]" = WeakKeyDictionary()
# a Tag's Bases, Base-first; never the Tag itself, which would keep its own key alive


def _tag_classes(
        ) -> tuple[type, type]:
    """``MetaTag`` and the root ``Tag``, bound on first use: ``tags``
    imports this module, so they cannot be imported at the top."""

    global _tag_types

    if _tag_types is None:
        from .tags import MetaTag
        from .tags import Tag

        _tag_types = (MetaTag, Tag)

    return _tag_types


def _is_tag_class(
        candidate: object,
        ) -> bool:
    """A class made by ``MetaTag``, the root ``Tag`` included. A Tag is
    identified by its metaclass, never by a lookalike name."""

    meta, _root = _tag_classes()

    return isinstance(candidate, meta)


def _is_tag(
        candidate: object,
        ) -> bool:
    """A Tag below the root: the root is the only Tag with no Tag among
    its Bases."""

    _meta, root = _tag_classes()

    return (
            _is_tag_class(candidate)
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

    cached = _bases_cache.get(tag)

    if cached is not None:
        return cached + (tag,)

    form: list[type] = []
    seen: set[type] = set()
    pending: list[tuple[type, bool]] = [
            (
                tag,
                False,
                ),
            ]

    while pending:
        candidate, expanded = pending.pop()

        if expanded:
            form.append(candidate)
            continue

        if candidate in seen:
            continue

        seen.add(candidate)
        pending.append(
                (
                    candidate,
                    True,
                    )
                )

        for base in reversed(_direct_bases(candidate)):
            if base not in seen:
                pending.append(
                        (
                            base,
                            False,
                            )
                        )

    result = tuple(form)
    _bases_cache[tag] = result[:-1]

    return result


def _leaves(
        active: Iterable[type],
        ) -> tuple[type, ...]:
    """Active Tags that no other active Tag specializes."""

    active = tuple(active)
    specialized = {
            base
            for other in active
            for base in _form_of(other)[:-1]
            }

    if len(active) > 1:
        _is_tag(None)   # binds the root
        specialized.add(_tag_types[1])   # every other Tag specializes the root

    return tuple(
            candidate
            for candidate in active
            if candidate not in specialized
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


def _is_base_of(
        base: type,
        shape: type,
        ) -> bool:
    """True when ``base`` is a Base in ``shape``'s Form: a strict Base,
    never ``shape`` itself."""

    return (
            base is not shape
            and issubclass(shape, base)
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
