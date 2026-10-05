"""The public TOP types: Tag and its metaclass.

TOP borrows the language's own syntax for Tag-level acts and leaves the
Tag's dotted namespace to the program:

    Wizard(charlie)               apply (Bases first)
    charlie in Wizard             a sound member: what the loop sees
    charlie in Wizard[:]          a member, sound or defective
    "Deprecated" in Wizard        a keyword: the Tag carries the Flag Pin Deprecated
    Wizard in charlie             the same, from the Agent's side
    "Wizard" in charlie           the same, by name
    isinstance(charlie, Wizard)   ever a member ("ever a Wizard, always a Wizard")
    for w in Wizard               the sound population
    if Wizard                     is there a sound Wizard at all?
    for w in ~Wizard              the defective population
    Wizard[:]                     everyone: the whole Field
    Wizard[...]                   the safehouse: Agents kept at a failed deletion
    Wizard[charlie]               the Agent-bound view
    del Wizard[charlie]           leave the Field (Rip)
    del Wizard[...]               triage: let go of what the safehouse keeps
    Form(Wizard)                  the Base-first closure, as Tags
    f"{Wizard:form}"              the same, as text

A Tag marked @Pin applies to Tags (STEP-SPEC-9); the pinned Tag is then
an Agent in every spelling above: Rare(Wizard), Wizard in Rare,
for tag in Rare, Rare[Wizard], del Rare[Wizard], f"{Wizard:pins}".
"""

from __future__ import annotations

from typing import Any
from typing import Iterator
import weakref

from .access import _keyword
from .access import _view_of
from .contracts import _holds
from .declarations import _MISSING
from .declarations import _REPORTS
from .declarations import _check_pin_bases
from .declarations import _is_pin
from .declarations import _name_checks
from .errors import TagCompositionError
from .errors import TagDeclarationError
from .fields import _Field
from .fields import _Partition
from .fields import _population_of
from .geometry import _form_of
from .geometry import _is_tag
from .lifecycle import _Safehouse
from .lifecycle import _rip
from .lifecycle import _triage
from .state import Tagged
from .state import _name_of
from .state import _state_of
from .transactions import _apply


def _sound_of(
        tag: type,
        ) -> _Partition:
    """The sound population of a Tag: the members whose contract holds.
    A module function, not a member of the metaclass reached through
    the class, so a Tag declaring its own ``_sound`` is not in the way."""

    return _Partition(
            tag.__dict__["_topkit_field"],
            _holds,
            "sound",
            )


class MetaTag(type):
    """Metaclass of every Tag: the Tag-level acts, in language syntax."""

    def __new__(
            meta,
            name: str,
            bases: tuple[type, ...],
            namespace: dict[str, Any],
            **kwargs: Any,
            ) -> "MetaTag":
        namespace.setdefault(
                "_topkit_field",
                _Field(),
                )
        if _REPORTS in namespace:
            raise TagDeclarationError(
                    f"{name} defines {_REPORTS}, the name under which TopKit"
                    " keeps a Tag's Report values; a Tag's body cannot use it"
                    )

        namespace[_REPORTS] = {}   # made with the Tag, so a rolled-back Pin keeps the values built during it
        _name_checks(namespace)

        tag = super().__new__(
                meta,
                name,
                bases,
                namespace,
                **kwargs,
                )
        _check_pin_bases(tag)
        tag.__dict__["_topkit_field"]._owner = weakref.ref(tag)   # the Tag holds its Field, never the reverse

        return tag

    def __call__(
            tag,
            target: object = _MISSING,
            /,
            **inputs: Any,
            ) -> object:
        if target is _MISSING:
            raise TypeError(
                    f"{tag.__name__} is a Tag: apply it to a Target,"
                    f" {tag.__name__}(target)"
                    )

        if _is_pin(tag):
            _check_pin_target(
                    tag,
                    target,
                    )
        elif isinstance(target, type):
            raise TypeError(
                    f"{tag.__name__} is applied to objects, not classes"
                    )

        return _apply(
                target,
                tag,
                inputs,
                )

    def __contains__(
            tag,
            candidate: object,
            ) -> bool:
        """``agent in Wizard``: a sound member, the population the loop
        sees (STEP-SPEC-19); ``agent in Wizard[:]`` is membership. Inside
        a check the kit runs under its guard (a Postcondition, the quality
        check, a condition read by name, a ``Contract`` read) it answers
        membership for the Agent under check, as ``Contract.Holds(agent)``
        answers True there; a Precondition at the tagging's gate, an
        Imprint and a ``@Rip`` protocol read the sound population as code
        outside does, unless their tagging began inside a check.
        ``"Deprecated" in Wizard``: a keyword among the Tag's Flag Pins; a
        string is never a member."""

        if isinstance(candidate, str):
            return _keyword(
                    tag,
                    candidate,
                    )

        state = _state_of(candidate)

        return (
                state is not None
                and tag in state.active
                and (
                    state.checking                  # asked from inside a check
                    or not state.postconditions     # nothing promised: every member is sound
                    or _holds(candidate)
                    )
                )

    def __instancecheck__(
            tag,
            candidate: object,
            ) -> bool:
        state = _state_of(candidate)

        if state is not None and tag in state.ever:
            return True

        return super().__instancecheck__(candidate)

    def __iter__(
            tag,
            ) -> Iterator[object]:
        return iter(_sound_of(tag))

    def __len__(
            tag,
            ) -> int:
        return len(_sound_of(tag))

    def __bool__(
            tag,
            ) -> bool:
        return bool(_sound_of(tag))

    def __invert__(
            tag,
            ) -> _Partition:
        return ~_sound_of(tag)

    def __or__(
            tag,
            other: Any,
            ) -> Any:
        """``Wizard | Fighter``: the sound population of either. A Tag in an
        operator seat is its sound population, decided by its metaclass;
        anything that is not a population keeps ``type``'s own meaning
        (``Wizard | None``)."""

        if _population_of(other) is NotImplemented:
            return super().__or__(other)

        return _sound_of(tag) | other

    def __ror__(
            tag,
            other: Any,
            ) -> Any:
        if _population_of(other) is NotImplemented:
            return super().__ror__(other)

        return other | _sound_of(tag)

    def __and__(
            tag,
            other: Any,
            ) -> Any:
        return _sound_of(tag) & other

    def __rand__(
            tag,
            other: Any,
            ) -> Any:
        return other & _sound_of(tag)

    def __sub__(
            tag,
            other: Any,
            ) -> Any:
        return _sound_of(tag) - other

    def __rsub__(
            tag,
            other: Any,
            ) -> Any:
        return other - _sound_of(tag)

    def __getitem__(
            tag,
            key: Any,
            ) -> Any:
        if key is Ellipsis:
            return _Safehouse(tag)   # Tag[...]: kept by this Tag or by a Shape over it

        if isinstance(key, slice):
            if key != slice(None):
                raise TypeError(
                        "Tag[:] is the whole Field; positional slices have"
                        " no meaning for a population"
                        )

            return tag._topkit_field

        return _view_of(
                key,
                tag,
                )

    def __delitem__(
            tag,
            agent: object,
            ) -> None:
        if agent is Ellipsis:
            _triage(tag)   # del Tag[...]: let go of what the safehouse keeps
            return

        _rip(
                agent,
                tag,
                )

    def __format__(
            tag,
            spec: str,
            ) -> str:
        if spec == "":
            return str(tag)

        if spec == "form":
            return " → ".join(
                    member.__name__
                    for member in _form_of(tag)
                    )

        if spec == "pins":
            from .queries import Tags

            return ", ".join(
                    pin.__name__
                    for pin in Tags(tag)
                    )

        if spec == "contract":
            from .contracts import Contract

            return Contract.Display(tag)

        raise ValueError(
                f"unknown format spec {spec!r} for a Tag; use 'form',"
                " 'pins', or 'contract'"
                )


def _check_pin_target(
        pin: type,
        target: object,
        ) -> None:
    if not _is_tag(target):
        raise TagCompositionError(
                f"{pin.__name__} is a Pin: apply it to a Tag, not to"
                f" {_name_of(target)}"
                )

    if target in _form_of(pin):
        raise TagCompositionError(
                f"{pin.__name__} cannot pin itself"
                )


class Tag(metaclass=MetaTag):
    """A semantic category. Subclass it; its members are its contributions."""

    __slots__ = ()


__all__ = [
        "MetaTag",
        "Tag",
        "Tagged",
        ]
