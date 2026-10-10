"""Geometry: how Tags relate. A Base forms into a Shape.

The Form of a Tag is its ordered, duplicate-free, Base-first closure,
ending with the Tag itself. Applying a Tag follows its Form.
"""

from __future__ import annotations

from typing import Iterable
from typing import NamedTuple
from weakref import WeakKeyDictionary


_tag_types: tuple[type, type] | None = None
# Compatibility fallback for non-Tags; ordinary classes have no TOP Bases.
_bases_cache: "WeakKeyDictionary[type, tuple[type, ...]]" = WeakKeyDictionary()


class _Bases_Memo(NamedTuple):
    owner: type
    bases: tuple[type, ...]


def _form_key(tag: type) -> str:
    return f"_TOPKIT_BASES_{id(tag):#x}"


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

    owned = _is_tag(tag)

    if owned:
        name = _form_key(tag)
        namespace = vars(tag)
        memo = namespace.get(name)

        if type(memo) is _Bases_Memo and memo.owner is tag:
            return memo.bases + (tag,)
    else:
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

    if owned:
        # A Base's Contributions may point back to its Shape. Keep that
        # cycle on the Tag, never in a global cache or its public Field.
        if name not in namespace and all(
                name not in vars(base)
                for base in tag.__mro__[1:]
                ):
            type.__setattr__(tag, name, _Bases_Memo(tag, result[:-1]))
    else:
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


def _related(
        one: type,
        other: type,
        ) -> bool:
    """True when one Tag is a Base or Shape of the other."""

    return (
            issubclass(one, other)
            or issubclass(other, one)
            )
