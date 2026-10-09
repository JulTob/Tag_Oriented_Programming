"""The public TOP types: Tag and its metaclass.

TOP borrows the language's own syntax for Tag-level acts and leaves the
Tag's dotted namespace to the program:

    Wizard(charlie)               apply (Bases first)
    charlie in Wizard             active membership, sound or defective
    "Deprecated" in Wizard        a keyword: the Tag carries the Flag Pin Deprecated
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

The dot on a Tag reads and writes the Tag. A name the Tag gives its
Agents (a Record, an Action, a condition) is not a value of the Tag:
``Wizard.hp = 10`` and ``del Wizard.hp`` are refused (STEP-SPEC-28).
"""

from __future__ import annotations

from typing import Any
from typing import Iterator
import weakref

from .access import _keyword
from .access import _view_of
from .contracts import _holds
from .declarations import _MISSING
from .declarations import _agent_kind
from .declarations import _check_pin_bases
from .declarations import _is_pin
from .declarations import _name_checks
from .errors import TagCategoryError
from .errors import TagCompositionError
from .fields import _Field
from .fields import _Partition
from .fields import _population_of
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
                "_topkit_field",
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
        tag._topkit_field._tag = weakref.ref(tag)   # a Pin's Field holds Tags
        _check_pin_bases(tag)

        return tag

    def __setattr__(
            tag,
            name: str,
            value: Any,
            ) -> None:
        """``Wizard.motto = "wise"`` sets a value of the Tag. A name the Tag
        gives its Agents is refused, before anything changes."""

        _refuse_a_write_over_an_agent_name(
                tag,
                name,
                value,
                )
        super().__setattr__(
                name,
                value,
                )

    def __delattr__(
            tag,
            name: str,
            ) -> None:
        _refuse_a_write_over_an_agent_name(
                tag,
                name,
                _MISSING,   # a deletion
                )
        super().__delattr__(name)

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
        """``agent in Wizard``: membership. ``"Deprecated" in Wizard``: a
        keyword among the Tag's Flag Pins; a string is never a member."""

        if isinstance(candidate, str):
            return _keyword(
                    tag,
                    candidate,
                    )

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
                tag._topkit_field,
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

    def __or__(
            tag,
            other: Any,
            ) -> Any:
        """``Wizard | Fighter``: the sound population of either. A Tag in an
        operator seat is its sound population; anything that is not a
        population keeps ``type``'s own meaning (``Wizard | None``)."""

        if _population_of(other) is NotImplemented:
            return super().__or__(other)

        return tag._sound() | other

    def __ror__(
            tag,
            other: Any,
            ) -> Any:
        if _population_of(other) is NotImplemented:
            return super().__ror__(other)

        return other | tag._sound()

    def __and__(
            tag,
            other: Any,
            ) -> Any:
        return tag._sound() & other

    def __rand__(
            tag,
            other: Any,
            ) -> Any:
        return other & tag._sound()

    def __sub__(
            tag,
            other: Any,
            ) -> Any:
        return tag._sound() - other

    def __rsub__(
            tag,
            other: Any,
            ) -> Any:
        return other - tag._sound()

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

            return tag._topkit_field

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


_AGENT_KINDS = {
        "record": ("a Record of each", None),
        "action": ("an Action of each", None),
        "precondition": ("a Precondition of each", "@Pre"),
        "postcondition": ("a Postcondition of each", "@Post"),
        "condition": ("a Precondition and a Postcondition of each", "@Pre @Post"),
        "imprint": ("an Imprint of each", "@Imprint"),
        "delete": ("a name deleted from each", "@Delete"),
        }
# what a declaration is to the Agents, and the mark that writes it when it
# is a protocol; a Record or an Action is written on each Agent instead


def _refuse_a_write_over_an_agent_name(
        tag: type,
        name: str,
        value: Any,
        ) -> None:
    """A Category Failure (STEP-SPEC-28) when ``name`` is something the Tag
    gives its Agents: writing ``value`` there, or deleting it when
    ``value`` is _MISSING, would make the Tag and its Agents disagree.
    Before the Tag's first use it would erase the declaration; after, the
    Tag would read a value no Agent has."""

    kind = _agent_kind(
            tag,
            name,
            )

    if kind is None:
        return

    what, mark = _AGENT_KINDS[kind]
    agent = _loop_name(tag)
    loop = f"for {agent} in {tag.__name__}:"

    if mark is not None:
        spelling = f"Write it in a Tag's class body: {mark} def {name}(agent): ..."
    elif value is _MISSING:
        spelling = f"Write: {loop} del {agent}.{name}"
    else:
        spelling = f"Write: {loop} {agent}.{name} = {value!r}"

    raise TagCategoryError(
            f"{name} is {what} {tag.__name__}, not a value of the Tag"
            f" {tag.__name__}. {spelling}"
            )


def _loop_name(
        tag: type,
        ) -> str:
    """What a loop over the Tag calls each member: ``wizard`` for Wizard."""

    name = tag.__name__.lower()

    if name == tag.__name__:
        return "agent"   # a lower-case Tag: its own name would shadow it

    return name


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
