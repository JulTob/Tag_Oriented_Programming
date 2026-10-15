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

from inspect import getattr_static
from typing import Any
from typing import Iterator

from .access import _keyword
from .access import _refuse_host_truth
from .access import _view_of
from .contracts import _holds
from .declarations import _MISSING
from .declarations import _KIND
from .declarations import Report
from .declarations import _Own_Operation
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
from .state import Tagged
from .state import _Pinned_Operation
from .state import _Pinned_Value
from .state import _name_of
from .state import _state_of
from .transactions import _apply


_TYPE_NAMESPACE = type.__dict__["__dict__"]
_TYPE_MRO = type.__dict__["__mro__"]


def _declared_operation(member: object) -> bool:
    """Inspect an Operation mark without running callable metadata hooks."""

    if not isinstance(member, classmethod):
        return False

    function = classmethod.__func__.__get__(member)
    mark = getattr_static(function, _KIND, None)
    return type(mark) is str and mark == "operation"


def _scope_operation(member: Any) -> Any:
    if _declared_operation(member) and not isinstance(member, _Own_Operation):
        return _Own_Operation(member.__func__, member)
    return member


def _scope_tag_member(member: Any, owner: type | None = None) -> Any:
    """Give an explicitly reused Report or Operation its own Tag binding."""

    member = _scope_operation(member)
    if (isinstance(member, (Report, _Own_Operation))
            and member._owner_ref is not None
            and (owner is None or member._owner_ref() is not owner)):
        return member._copy_for_new_owner()
    return member


def _metaclass_data_member(tag: type, name: str) -> bool:
    # A data descriptor on the metaclass wins over the class MRO under
    # Python's own lookup rules. Leave that protocol seat to Python.
    for metaclass in _TYPE_MRO.__get__(type(tag)):
        metaname = _TYPE_NAMESPACE.__get__(metaclass).get(name, _MISSING)
        if metaname is _MISSING:
            continue
        kind = type(metaname)
        if (
                getattr_static(kind, "__set__", _MISSING) is not _MISSING
                or getattr_static(kind, "__delete__", _MISSING) is not _MISSING
                ):
            return True
        break

    return False


def _inherited_tag_member(
        tag: type,
        name: str,
        ) -> bool:
    """Whether a Base owns a shared member absent from this Tag.

    Python class inheritance still serves plain host/class members.  A
    Report or Operation belongs to its declaring Tag, including one a Pin
    landed there; applying a Shape separately applies its Bases to Agents.
    """

    if name in _TYPE_NAMESPACE.__get__(tag):
        return False

    for base in _TYPE_MRO.__get__(tag)[1:]:
        namespace = _TYPE_NAMESPACE.__get__(base)
        member = namespace.get(name, _MISSING)

        if member is _MISSING:
            continue

        if not isinstance(base, MetaTag):
            return False

        scoped = isinstance(
                member,
                (Report, _Own_Operation, _Pinned_Operation, _Pinned_Value),
                )
        return scoped and not _metaclass_data_member(tag, name)

    return False


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
                FIELD_SEAT,
                _Field(),
                )
        copies: dict[int, Any] = {}
        for member_name, member in tuple(namespace.items()):
            original_id = id(member)
            if original_id not in copies:
                copies[original_id] = _scope_tag_member(member)
            namespace[member_name] = copies[original_id]
        _check_rip_declarations(
                name,
                namespace,
                )
        _name_checks(namespace, name)

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
        value = _scope_tag_member(value, tag)
        super().__setattr__(name, value)
        if (isinstance(value, (Report, _Own_Operation))
                and _TYPE_NAMESPACE.__get__(tag).get(name) is value):
            value.__set_name__(tag, name)

    def __delattr__(
            tag,
            name: str,
            ) -> None:
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
