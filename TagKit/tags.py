"""The public TOP types: Tag and its metaclass.

    Wizard(charlie)          apply (Bases first)
    charlie in Wizard        active membership
    isinstance(charlie, Wizard)   ever a member ("ever a Wizard, always a Wizard")
    for w in Wizard          the whole Field
    Wizard[:]  /  ~Wizard[:] sound / defective members
    Wizard[charlie]          the Agent-bound view
    Wizard.Rip(charlie)      leave the Field
"""

from __future__ import annotations

from typing import Any
from typing import Iterator

from .access import _view_of
from .contracts import _holds
from .declarations import _MISSING
from .fields import _Field
from .fields import _Partition
from .geometry import _form_of
from .lifecycle import _rip
from .state import Tagged
from .state import _state_of
from .transactions import _apply


class MetaTag(type):
    """Metaclass of every Tag: the Tag-level operations."""

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

        return super().__new__(
                meta,
                name,
                bases,
                namespace,
                **kwargs,
                )

    @property
    def Field(
            tag,
            ) -> _Field:
        return tag._tagkit_field

    def Form(
            tag,
            ) -> tuple[type, ...]:
        """Base-first closure of this Tag, ending with the Tag itself."""

        return _form_of(tag)

    def __contains__(
            tag,
            candidate: object,
            ) -> bool:
        state = _state_of(candidate)

        return (
                state is not None
                and tag in state.active
                )

    def __iter__(
            tag,
            ) -> Iterator[object]:
        return iter(tag._tagkit_field)

    def __getitem__(
            tag,
            key: Any,
            ) -> Any:
        if isinstance(key, slice):
            if key != slice(None):
                raise TypeError(
                        "Tag[:] is the sound Field; positional slices have"
                        " no meaning for a population"
                        )

            return _Partition(
                    tag._tagkit_field,
                    _holds,
                    "sound",
                    )

        return _view_of(
                key,
                tag,
                )

    def __instancecheck__(
            tag,
            candidate: object,
            ) -> bool:
        state = _state_of(candidate)

        if state is not None and tag in state.ever:
            return True

        return super().__instancecheck__(candidate)

    def Rip(
            tag,
            agent: object,
            ) -> object:
        """Extract an Agent from this Tag's Field. Contributions stay."""

        return _rip(
                agent,
                tag,
                )

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

        if isinstance(target, type):
            raise TypeError(
                    f"{tag.__name__} is applied to objects, not classes"
                    )

        return _apply(
                target,
                tag,
                inputs,
                )


class Tag(metaclass=MetaTag):
    """A semantic category. Subclass it; its members are its contributions."""

    __slots__ = ()


__all__ = [
        "MetaTag",
        "Tag",
        "Tagged",
        ]
