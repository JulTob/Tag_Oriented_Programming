"""The public TOP types: Tag and its metaclass.

TOP borrows the language's own syntax for Tag-level acts and leaves the
Tag's dotted namespace to the program:

    Wizard(charlie)               apply (Bases first)
    charlie in Wizard             active membership, sound or defective
    Wizard in charlie             the same, from the Agent's side
    "Wizard" in charlie           the same, by name
    isinstance(charlie, Wizard)   ever a member ("ever a Wizard, always a Wizard")
    for w in Wizard               the sound population
    if Wizard                     is there a sound Wizard at all?
    for w in ~Wizard              the defective population
    Wizard[:]                     everyone: the whole Field
    Wizard[charlie]               the Agent-bound view
    del Wizard[charlie]           leave the Field (Rip)
    Form(Wizard)                  the Base-first closure, as Tags
    f"{Wizard:form}"              the same, as text

A Tag marked @Pin applies to Tags (STEP-SPEC-9); the pinned Tag is then
an Agent in every spelling above: Rare(Wizard), Wizard in Rare,
for tag in Rare, Rare[Wizard], del Rare[Wizard], f"{Wizard:pins}".
"""

from __future__ import annotations

from typing import Any
from typing import Iterator

from .access import _view_of
from .contracts import _holds
from .declarations import _MISSING
from .declarations import _check_pin_bases
from .declarations import _is_pin
from .declarations import _name_checks
from .errors import TagCompositionError
from .fields import _Field
from .fields import _Partition
from .geometry import _form_of
from .geometry import _is_tag
from .lifecycle import _rip
from .state import Tagged
from .state import _name_of
from .state import _state_of
from .transactions import _apply


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
                "_tagkit_field",
                _Field(),
                )
        _name_checks(namespace)

        tag = super().__new__(
                meta,
                name,
                bases,
                namespace,
                **kwargs,
                )
        _check_pin_bases(tag)

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
        state = _state_of(candidate)

        return (
                state is not None
                and tag in state.active
                )

    def __instancecheck__(
            tag,
            candidate: object,
            ) -> bool:
        state = _state_of(candidate)

        if state is not None and tag in state.ever:
            return True

        return super().__instancecheck__(candidate)

    def _sound(
            tag,
            ) -> _Partition:
        return _Partition(
                tag._tagkit_field,
                _holds,
                "sound",
                )

    def __iter__(
            tag,
            ) -> Iterator[object]:
        return iter(tag._sound())

    def __len__(
            tag,
            ) -> int:
        return len(tag._sound())

    def __bool__(
            tag,
            ) -> bool:
        return bool(tag._sound())

    def __invert__(
            tag,
            ) -> _Partition:
        return ~tag._sound()

    def __getitem__(
            tag,
            key: Any,
            ) -> Any:
        if isinstance(key, slice):
            if key != slice(None):
                raise TypeError(
                        "Tag[:] is the whole Field; positional slices have"
                        " no meaning for a population"
                        )

            return tag._tagkit_field

        return _view_of(
                key,
                tag,
                )

    def __delitem__(
            tag,
            agent: object,
            ) -> None:
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
