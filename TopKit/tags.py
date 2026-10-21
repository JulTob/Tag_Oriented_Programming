"""The public TOP types: Tag and its metaclass.

TOP borrows the language's own syntax for Tag-level acts and leaves the
Tag's dotted namespace to the program:

    Wizard(charlie)               apply (Bases first)
    charlie in Wizard             sound membership, as in the plain loop
    charlie in Wizard[:]          active membership, sound or defective
    "Deprecated" in Wizard        a keyword: the Tag carries the Flag Pin Deprecated
    Wizard in charlie             the same, from the Agent's side
    "Wizard" in charlie           the same, by name
    isinstance(charlie, Wizard)   ever a member ("ever a Wizard, always a Wizard")
    for w in Wizard               the sound population
    if Wizard                     do the Tag's own visible Posts hold?
    len(Wizard)                   the number of sound Wizards
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

from .observations import _refuse_observed_act

from .arrest import _arrest_of
from .arrest import _safehouse
from .access import _keyword
from .access import _refuse_host_truth
from .access import _view_of
from .contracts import _holds
from .contracts import _holds_for_population
from .declarations import _MISSING
from .declarations import _check_constant_declarations
from .declarations import _check_constant_shapes
from .declarations import _check_pin_bases
from .declarations import _check_rip_declarations
from .declarations import _check_tool_declarations
from .declarations import _constant_owner
from .declarations import _is_dunder
from .declarations import _is_pin
from .declarations import _kind_of
from .declarations import _name_checks
from .declarations import _refuse_condition_dunder
from .declarations import _refuse_truth_gain
from .errors import TagCompositionError
from .fields import FIELD_SEAT
from .fields import _Field
from .fields import _Partition
from .fields import _field_of
from .fields import _population_of
from .fields import _sound_of
from .geometry import _form_of
from .geometry import _is_tag
from .lifecycle import _rip
from .lifecycle import _rip_field
from .state import Tagged
from .state import _guard_operation_declaration
from .state import _name_of
from .state import _state_of
from .transactions import _apply


_link_agent = object()
_link_contact = object()
_link_pair_view = object()


class MetaTag(type):
    """Metaclass of every Tag: the Tag-level acts, in language syntax."""

    def __new__(
            meta,
            name: str,
            bases: tuple[type, ...],
            namespace: dict[str, Any],
            **kwargs: Any,
            ) -> "MetaTag":
        _refuse_observed_act('create a Tag')

        namespace.setdefault(
                FIELD_SEAT,
                _Field(),
                )
        _check_rip_declarations(
                name,
                namespace,
                )
        _name_checks(namespace, name)
        for member_name, member in tuple(namespace.items()):
            namespace[member_name] = _guard_operation_declaration(member)

        tag = super().__new__(
                meta,
                name,
                bases,
                namespace,
                **kwargs,
                )
        _check_pin_bases(tag)
        _check_constant_declarations(tag, namespace)
        _check_tool_declarations(tag, namespace)

        return tag

    def __setattr__(
            tag,
            name: str,
            value: Any,
            ) -> None:
        _refuse_observed_act('change a Tag declaration')

        _refuse_truth_gain(tag.__name__, name, value)
        if _is_dunder(name):
            _refuse_condition_dunder(tag.__name__, name, _kind_of(value))
        owner = _constant_owner(tag, name)

        if owner is not None:
            raise TagCompositionError(
                    f"{tag.__name__}.{name} is Constant from"
                    f" {owner.__name__}; it cannot be overwritten"
                    )

        _check_constant_shapes(tag, name)
        super().__setattr__(name, value)

    def __delattr__(
            tag,
            name: str,
            ) -> None:
        _refuse_observed_act('delete a Tag declaration')

        owner = _constant_owner(tag, name)

        if owner is not None:
            raise TagCompositionError(
                    f"{tag.__name__}.{name} is Constant from"
                    f" {owner.__name__}; it cannot be deleted"
                    )

        super().__delattr__(name)

    def __call__(
            tag,
            target: object = _MISSING,
            /,
            **inputs: Any,
            ) -> object:
        _refuse_observed_act('apply a Tag or Pin')

        if target is _link_agent or target is _link_contact:
            target = target._current()
        elif type(target) is _link_pair_view:
            target = target._current()
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
        else:
            _refuse_host_truth(target)

        return _apply(
                target,
                tag,
                inputs,
                )

    def __contains__(
            tag,
            candidate: object,
            ) -> bool:
        """``agent in Wizard``: sound membership, as in the plain loop.
        ``agent in Wizard[:]`` is raw membership. A string asks for a
        keyword among the Tag's Flag Pins, never Agent membership."""

        if candidate is _link_agent or candidate is _link_contact:
            candidate = candidate._current()
        elif type(candidate) is _link_pair_view:
            candidate = candidate._current()
        if isinstance(candidate, str):
            return _keyword(
                    tag,
                    candidate,
                    )

        # A concrete Tag's Field has native identity entries. Read them
        # before and after judging Posts, with callbacks between the checks.
        members = _field_of(tag)._members
        identity = id(candidate)
        reference = members.get(identity)
        if reference is None or reference() is not candidate:
            return False
        if _safehouse and _arrest_of(candidate) is not None:
            return False
        state = _state_of(candidate)
        if state is not None and state.postconditions and not _holds_for_population(candidate):
            return False
        # A Post or a physical dictionary callback may change admission.
        # Keep the second identity check, including a leave-and-rejoin.
        reference = members.get(identity)
        return (reference is not None and reference() is candidate
                and (not _safehouse or _arrest_of(candidate) is None))

    def __instancecheck__(
            tag,
            candidate: object,
            ) -> bool:
        if candidate is _link_agent or candidate is _link_contact:
            candidate = candidate._current()
        elif type(candidate) is _link_pair_view:
            candidate = candidate._current()
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
        return _holds(tag)

    def __invert__(
            tag,
            ) -> _Partition:
        return ~_sound_of(tag)

    def __or__(
            tag,
            other: Any,
            ) -> Any:
        """``Wizard | Fighter``: the sound population of either. A Tag in an
        operator seat is its sound population; anything that is not a
        population keeps ``type``'s own meaning (``Wizard | None``)."""

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
        if key is _link_agent or key is _link_contact:
            key = key._current()
        elif type(key) is _link_pair_view:
            key = key._current()
        if key is Ellipsis:
            from .safehouses import _Safehouse
            return _Safehouse(tag)
        if isinstance(key, slice):
            if key != slice(None):
                raise TypeError(
                        "Tag[:] is the whole Field; positional slices have"
                        " no meaning for a population"
                        )

            return _field_of(tag)

        return _view_of(
                key,
                tag,
                )

    def __delitem__(
            tag,
            agent: object,
            ) -> None:
        _refuse_observed_act('Rip a Tag')

        if agent is _link_agent or agent is _link_contact:
            agent = agent._current()
        elif type(agent) is _link_pair_view:
            agent = agent._current()
        if isinstance(agent, slice):
            if agent != slice(None):
                raise TypeError("del Tag[:] Rips the whole Field; positional slices are unavailable")
            _rip_field(tag)
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
