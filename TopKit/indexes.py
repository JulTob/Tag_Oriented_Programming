"""Indexes: a Tag's Field as a mapping, ordered by its key (STEP-SPEC-17).

A Record marked ``@Index`` is a component of the Tag's key. The whole
key, every component in declaration order, is unique across the Field
and constant on the Agent. Read on the Tag, a component is a **handle**:
one name in two scopes, the value on the Agent and the map on the Tag.

    Signal.t                 the values of t, as a dictionary's keys are:
                             iterate, len, in, min, max
    Signal.t[:]              everyone, in Index order; [::-1] descending
    Signal.t[a:b]            the half-open value range, in Index order
    Signal.t[v]              the members with t == v: one Agent when t is
                             the whole key, a population otherwise
    Signal.t[1].seq[2]       one component per bracket; a chain is the
                             intersection Signal.t[1] & Signal.seq[2]
    2 in Signal.t[1].seq     is that value present, without failing

The whole key names one Agent; part of it names a population. A handle
walks the whole Field, as ``Tag[:]`` does; sound only is ``if agent:``
in the loop. The Index has one order, declaration order: a handle
constrains and never reorders.
"""

from __future__ import annotations

from bisect import bisect_left
from typing import Any
from typing import Iterator
from weakref import WeakKeyDictionary

from .declarations import Index
from .declarations import _MISSING
from .errors import TagCompositionError
from .errors import TagDeclarationError
from .errors import TagResolutionError
from .fields import _Population
from .geometry import _form_of


# ------------------------------------------------------------------
# Which Tag declares the Index, and its components
# ------------------------------------------------------------------


_index_cache: "WeakKeyDictionary[type, Any]" = WeakKeyDictionary()


def _declared_components(
        tag: type,
        ) -> tuple[str, ...]:
    """The Index components ``tag`` itself declares, in declaration order."""

    return tuple(
            name
            for name, attribute in tag.__dict__.items()
            if isinstance(attribute, Index)
            )


def _index_of(
        tag: type,
        ) -> tuple[type, tuple[str, ...]] | None:
    """The Tag in ``tag``'s Form that declares the Index, with the key's
    components; None when the Form has no Index."""

    cached = _index_cache.get(
            tag,
            _MISSING,
            )

    if cached is not _MISSING:
        return cached

    found = None

    for member in _form_of(tag):
        components = _declared_components(member)

        if components:
            found = (
                    member,
                    components,
                    )
            break

    _index_cache[tag] = found

    return found


def _check_index_form(
        tag: type,
        ) -> None:
    """One Index per Form, declared in one Tag. Checked when the class is
    made, so the mistake is found where it is written."""

    owners = [
            klass
            for klass in tag.__mro__
            if _declared_components(klass)
            ]

    if len(owners) <= 1:
        return

    names = ", ".join(
            klass.__name__
            for klass in owners
            )

    raise TagDeclarationError(
            f"{tag.__name__}: one Index per Form, declared in one Tag, but"
            f" {names} each declare components. A Shape inherits its Base's"
            " key and may not add to it: membership is closed upward, so a"
            " component the Base's uniqueness already decides could never"
            " separate two members"
            )


# ------------------------------------------------------------------
# The key a tagging builds
# ------------------------------------------------------------------


def _describe(
        components: tuple[str, ...],
        key: tuple[Any, ...],
        ) -> str:
    return ", ".join(
            f"{name}={value!r}"
            for name, value in zip(components, key)
            )


def _check_key(
        tag: type,
        key: tuple[Any, ...],
        components: tuple[str, ...],
        ) -> None:
    """The key a tagging built, before commit: hashable, not yet taken,
    comparable with the keys already present. Any failure is a
    Composition Failure, and the call rolls back."""

    try:
        hash(key)
    except TypeError as error:
        raise TagCompositionError(
                f"{tag.__name__}: the key {_describe(components, key)} is"
                " not hashable; every Index component must be"
                ) from error

    field = tag._topkit_field

    if field.Holder(key) is not None:
        raise TagCompositionError(
                f"{tag.__name__}: the key {_describe(components, key)} is"
                " already taken by another member; the whole key is unique"
                " across the Field"
                )

    ordered = field.Keys()

    if not ordered:
        return

    sample = ordered[0]

    for name, mine, theirs in zip(components, key, sample):
        try:
            _ = mine < theirs
            _ = theirs < mine
        except TypeError as error:
            raise TagCompositionError(
                    f"{tag.__name__}.{name}: {mine!r} is not comparable with"
                    f" the keys already present ({theirs!r}); one"
                    " component, one order"
                    ) from error


# ------------------------------------------------------------------
# Views and handles
# ------------------------------------------------------------------


def _slice_text(
        key: slice,
        ) -> str:
    start = "" if key.start is None else repr(key.start)
    stop = "" if key.stop is None else repr(key.stop)
    text = f"{start}:{stop}"

    if key.step is not None and key.step != 1:
        text = f"{text}:{key.step!r}"

    return text


class _Keyed(_Population):
    """One Tag's Field seen through its Index: constrained component by
    component, walked in Index order, live like every population."""

    def __init__(
            view,
            tag: type,
            fixed: dict[str, Any] | None = None,
            ranges: dict[str, tuple[Any, Any]] | None = None,
            reverse: bool = False,
            label: str | None = None,
            ) -> None:
        found = _index_of(tag)

        if found is None:
            raise TypeError(
                    f"{tag.__name__} has no Index"
                    )

        owner, components = found
        view._tag = tag
        view._owner = owner
        view._components = components
        view._position = {
                name: position
                for position, name in enumerate(components)
                }
        view._fixed = dict(fixed or {})
        view._ranges = dict(ranges or {})
        view._reverse = reverse
        view._label = label if label is not None else tag.__name__

    def _keeps(
            view,
            key: tuple[Any, ...],
            ) -> bool:
        for name, wanted in view._fixed.items():
            if key[view._position[name]] != wanted:
                return False

        for name, (low, high) in view._ranges.items():
            component = key[view._position[name]]

            if low is not None and component < low:
                return False

            if high is not None and not component < high:
                return False

        return True

    def _pairs(
            view,
            ) -> Iterator[tuple[tuple[Any, ...], object]]:
        """The (key, member) pairs the view sees, in its direction. The
        leading component is found by bisection; the rest is a filter."""

        field = view._owner._topkit_field
        keys = field.Keys()
        leading = view._components[0]
        wanted = view._fixed.get(
                leading,
                _MISSING,
                )

        if wanted is not _MISSING:
            start = bisect_left(
                    keys,
                    (wanted,),
                    )
            selected = []

            for position in range(start, len(keys)):
                key = keys[position]

                if key[0] != wanted:
                    break

                selected.append(key)
        else:
            low, high = view._ranges.get(
                    leading,
                    (None, None),
                    )
            start = 0 if low is None else bisect_left(keys, (low,))
            stop = len(keys) if high is None else bisect_left(keys, (high,))
            selected = keys[start:stop]

        if view._reverse:
            selected = selected[::-1]

        shape = None if view._tag is view._owner else view._tag._topkit_field

        for key in selected:
            if not view._keeps(key):
                continue

            agent = field.Holder(key)

            if agent is None:
                continue

            if shape is not None and agent not in shape:
                continue

            yield key, agent

    def _the_one(
            view,
            ) -> object:
        """The member at the whole key, or a Resolution Failure."""

        key = tuple(
                view._fixed[name]
                for name in view._components
                )
        agent = view._owner._topkit_field.Holder(key)

        if agent is None or (
                view._tag is not view._owner
                and agent not in view._tag._topkit_field
                ):
            raise TagResolutionError(
                    f"no {view._tag.__name__} at"
                    f" {_describe(view._components, key)}"
                    )

        return agent

    def __iter__(
            view,
            ) -> Iterator[object]:
        return (
                agent
                for _key, agent in view._pairs()
                )

    def __contains__(
            view,
            agent: object,
            ) -> bool:
        key = view._owner._topkit_field.Key_Of(agent)

        if key is _MISSING:
            return False

        if (
                view._tag is not view._owner
                and agent not in view._tag._topkit_field
                ):
            return False

        return view._keeps(key)

    def __getattr__(
            view,
            name: str,
            ) -> "_Handle":
        if name.startswith("_"):
            raise AttributeError(name)

        if name not in view._position:
            raise AttributeError(
                    f"{view._tag.__name__} has no Index component {name!r};"
                    f" its key is {', '.join(view._components)}"
                    )

        if name in view._fixed or name in view._ranges:
            raise AttributeError(
                    f"{name!r} is already constrained in {view._label}; one"
                    " component per bracket, each once"
                    )

        return _Handle(
                view,
                name,
                )

    def __setattr__(
            view,
            name: str,
            value: Any,
            ) -> None:
        if name.startswith("_"):
            object.__setattr__(
                    view,
                    name,
                    value,
                    )
            return

        raise AttributeError(
                f"{view._label} is a view; it is read-only, and membership"
                " comes from tagging"
                )


class _Handle:
    """``Tag.name`` for an Index component: the values of that component
    among the members a view sees, and the seat for one component."""

    __slots__ = (
            "_view",
            "_name",
            )

    def __init__(
            handle,
            view: _Keyed,
            name: str,
            ) -> None:
        handle._view = view
        handle._name = name

    def __getitem__(
            handle,
            key: Any,
            ) -> Any:
        view = handle._view
        name = handle._name

        if isinstance(key, slice):
            if key.step not in (None, 1, -1):
                raise TypeError(
                        f"{view._label}.{name}[{_slice_text(key)}]: the step"
                        " of a value range is its direction, 1 or -1; a"
                        " range of values has no every-other"
                        )

            ranges = dict(view._ranges)
            ranges[name] = (
                    key.start,
                    key.stop,
                    )

            return _Keyed(
                    view._tag,
                    view._fixed,
                    ranges,
                    view._reverse != (key.step == -1),
                    f"{view._label}.{name}[{_slice_text(key)}]",
                    )

        fixed = dict(view._fixed)
        fixed[name] = key
        narrowed = _Keyed(
                view._tag,
                fixed,
                view._ranges,
                view._reverse,
                f"{view._label}.{name}[{key!r}]",
                )

        if len(fixed) == len(view._components):
            return narrowed._the_one()

        return narrowed

    def __setitem__(
            handle,
            key: Any,
            value: Any,
            ) -> None:
        raise TypeError(
                f"{handle!r}: membership comes from tagging, never from"
                " assignment"
                )

    def __delitem__(
            handle,
            key: Any,
            ) -> None:
        raise TypeError(
                f"{handle!r}: Rip is `del"
                f" {handle._view._tag.__name__}[agent]`, never a deletion"
                " by key"
                )

    def _values(
            handle,
            ) -> list[Any]:
        """The distinct values of this component among the members the
        view sees, in the component's own order, reversed with the view."""

        view = handle._view
        position = view._position[handle._name]
        distinct = {
                key[position]
                for key, _agent in view._pairs()
                }

        return sorted(
                distinct,
                reverse=view._reverse,
                )

    def __iter__(
            handle,
            ) -> Iterator[Any]:
        return iter(handle._values())

    def __len__(
            handle,
            ) -> int:
        return len(handle._values())

    def __bool__(
            handle,
            ) -> bool:
        return any(
                True
                for _pair in handle._view._pairs()
                )

    def __contains__(
            handle,
            value: Any,
            ) -> bool:
        view = handle._view

        if not view._ranges and len(view._fixed) + 1 == len(view._components):
            fixed = dict(view._fixed)
            fixed[handle._name] = value
            key = tuple(
                    fixed[name]
                    for name in view._components
                    )

            try:
                agent = view._owner._topkit_field.Holder(key)
            except TypeError:
                return False   # an unhashable value is never a key

            return agent is not None and (
                    view._tag is view._owner
                    or agent in view._tag._topkit_field
                    )

        position = view._position[handle._name]

        return any(
                key[position] == value
                for key, _agent in view._pairs()
                )

    def __repr__(
            handle,
            ) -> str:
        return f"<{handle._view._label}.{handle._name}>"


def _handle_of(
        tag: type,
        name: str,
        ) -> _Handle:
    """What ``Tag.name`` reads as for an Index component."""

    return _Handle(
            _Keyed(tag),
            name,
            )
