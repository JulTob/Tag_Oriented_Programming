"""Geometry: how Tags relate. A Base forms into a Shape.

The Form of a Tag is its ordered, duplicate-free, Base-first closure,
ending with the Tag itself. Applying a Tag follows its Form.
"""

from __future__ import annotations

from typing import Iterable
from weakref import WeakKeyDictionary
from weakref import ref

from .memo import _class_namespace
from .memo import _memo_key
from .memo import _memo_of
from .memo import _physical_namespace_get
from .memo import _remember_memo
from .memo import _type_bases


_tag_meta: type | None = None
_category_meta: type | None = None
_tag_types: tuple[type, type, type] | None = None
_META_KIND = "_topkit_metaclass_kind"
_TAG_KIND = object()
_PIN_KIND = object()
# Compatibility fallback for non-Tags; ordinary classes have no TOP Bases.
_bases_cache: "WeakKeyDictionary[type, tuple[type, ...]]" = WeakKeyDictionary()


def _form_key(tag: type) -> str:
    return _memo_key(tag, "BASES")


def _tag_metaclass(
        ) -> type:
    """Bind ``MetaTag`` without needing the root ``Tag`` while it is built."""

    global _tag_meta

    if _tag_meta is None:
        from .tags import MetaTag

        _tag_meta = MetaTag

    return _tag_meta


class _Category_Stamp:
    """One metaclass's fixed declaration kind, without retaining its owner."""

    __slots__ = ("kind", "owner")

    def __init__(self, kind: object) -> None:
        try:
            object.__getattribute__(self, "owner")
        except AttributeError:
            pass
        else:
            raise TypeError("a TOP metaclass category is initialized once")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "owner", None)

    def __set_name__(self, owner: type, name: str) -> None:
        if self.owner is not None:
            raise TypeError("a TOP metaclass category already has its owner")
        object.__setattr__(self, "owner", ref(owner))

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("a TOP metaclass category is fixed at declaration")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("a TOP metaclass category is fixed at declaration")


def _metaclass_kind(meta: type) -> object | None:
    """Read an authenticated, physically owned declaration kind.

    A foreign metaclass's changing Python ancestry cannot change a TOP
    metaclass's declaration kind or authenticate a copied namespace slot.
    """

    global _category_meta
    if _category_meta is None:
        from .tags import _CategoryMeta

        _category_meta = _CategoryMeta
    if not issubclass(type(meta), _category_meta):
        return None
    namespace = _class_namespace(meta)
    try:
        first = next(iter(namespace.items()), None)
    except RuntimeError:   # another thread changed the dictionary's size
        first = None
    # _CategoryMeta installs its protected slot first. Reading that pair
    # by key identity avoids both namespace copies and stored key hooks.
    # Keep the physical snapshot fallback for unusual/reordered namespaces.
    if first is not None and first[0] is _META_KIND:
        stamp = first[1]
    else:
        stamp = _physical_namespace_get(namespace, _META_KIND)
    if type(stamp) is not _Category_Stamp or stamp.owner is None or stamp.owner() is not meta:
        return None
    return stamp.kind


def _tag_classes(
        ) -> tuple[type, type, type]:
    """The shared metaclass and both roots, bound after bootstrap."""

    global _tag_types

    if _tag_types is None:
        from .tags import Pin, Tag

        _tag_types = (_tag_metaclass(), Tag, Pin)

    return _tag_types


def _class_kind(
        candidate: object,
        ) -> object | None:
    """The fixed kind of an authenticated TOP class, roots included.

    A metaclass subtype created by Pin actualization remains valid; a
    presented ``__class__``, changed ancestor or copied stamp does not
    grant this category.
    """

    meta = type(candidate)
    if not issubclass(meta, _tag_metaclass()):
        return None
    return _metaclass_kind(meta)


def _is_tag_class(
        candidate: object,
        ) -> bool:
    """Whether a class belongs to either authenticated TOP category."""

    return _class_kind(candidate) is not None


def _is_class(
        candidate: object,
        ) -> bool:
    """A native Python class, independently of a presented ``__class__``."""

    return issubclass(type(candidate), type)


def _is_tag(
        candidate: object,
        ) -> bool:
    """A concrete TOP class: an ordinary Tag, a Link Tag or a Pin."""

    _meta, tag_root, pin_root = _tag_classes()

    return (
            _is_tag_class(candidate)
            and candidate is not tag_root
            and candidate is not pin_root
            )


def _direct_bases(
        tag: type,
        ) -> tuple[type, ...]:
    """The Bases a Tag declares directly, in declaration order."""

    return tuple(
            base
            for base in _type_bases.__get__(tag)
            if _is_tag(base)
            )


def _form_of(
        tag: type,
        ) -> tuple[type, ...]:
    """Base-first closure of one Tag: every required Base once, then the Tag."""

    owned = _is_tag(tag)

    if owned:
        name = _form_key(tag)
        bases = _memo_of(tag, name)

        if bases is not None:
            return bases + (tag,)
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
        return _remember_memo(tag, name, result[:-1]) + (tag,)
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
        specialized.update(_tag_types[1:])   # declaration roots are not concrete leaves

    return tuple(
            candidate
            for candidate in active
            if candidate not in specialized
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
